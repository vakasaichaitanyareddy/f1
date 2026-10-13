import React, { useState, useEffect } from 'react';
import { 
  StyleSheet, Text, View, ScrollView, TouchableOpacity, 
  SafeAreaView, StatusBar, ActivityIndicator 
} from 'react-native';

interface DriverTiming {
  driver_number: number;
  driver_code: string;
  driver_name: string;
  team_name: string;
  team_color: string;
  position: number;
  grid?: number;
  current_lap?: number;
  gap_to_leader?: number;
  interval?: number;
  last_lap_time?: number;
  best_lap_time?: number;
  sectors?: {
    sector_1?: number;
    sector_2?: number;
    sector_3?: number;
  };
  tire_compound?: string;
  stint_lap_count: number;
  positions_gained: number;
}

interface PitStop {
  driver_number: number;
  lap_number: number;
  pit_duration?: number;
  lane_duration?: number;
  timestamp: string;
}

interface RaceControl {
  date: string;
  lap_number?: number;
  category: string;
  message: string;
  flag?: string;
  scope?: string;
  sector?: number;
}

interface DriverMapPosition {
  driver_number: number;
  driver_code: string;
  team_color: string;
  x: number;
  y: number;
}

interface TelemetryItem {
  driver_number: number;
  speed: number;
  throttle: number;
  brake: number;
  n_gear: number;
  drs: number;
  rpm: number;
}

interface LiveSnapshot {
  session_id: string;
  session_name: string;
  circuit_name: string;
  total_laps: number;
  current_lap: number;
  track_status: string;
  data_state?: string;
  timing_tower: DriverTiming[];
  pit_stops?: PitStop[];
  race_control?: RaceControl[];
  driver_map_positions?: DriverMapPosition[];
  telemetry?: TelemetryItem[];
  weather?: {
    air_temperature: number;
    track_temperature: number;
  };
  provenance: {
    source: string;
    data_state: string;
    is_test_fixture: boolean;
  };
}


interface AvailableSession {
  session_id: string;
  session_name: string;
  data_state: string;
  circuit_name: string;
}


export default function App() {
  const [activeTab, setActiveTab] = useState<'LIVE' | 'STANDINGS' | 'CHAMPIONSHIP'>('LIVE');
  const [liveSubView, setLiveSubView] = useState<'TIMING' | 'MAP' | 'TELEMETRY' | 'PITS' | 'RACE_CONTROL'>('TIMING');
  const [selectedDriverNum, setSelectedDriverNum] = useState<number>(1);
  const [standings, setStandings] = useState<any[]>([]);
  const [liveData, setLiveData] = useState<LiveSnapshot | null>(null);
  const [availableSessions, setAvailableSessions] = useState<AvailableSession[]>([]);
  const [selectedSessionId, setSelectedSessionId] = useState<string>('2024_01_race');
  const [spoilerShield, setSpoilerShield] = useState(false);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  // Championship Intelligence state
  const [selectedDriver, setSelectedDriver] = useState<string>('PER');
  const [selectedRival, setSelectedRival] = useState<string>('VER');
  const [calculatorData, setCalculatorData] = useState<any>(null);

  const formatLapTime = (timeInSeconds?: number | null) => {
    if (timeInSeconds == null || !Number.isFinite(timeInSeconds) || timeInSeconds <= 0) return "-:--.---";
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = (timeInSeconds % 60).toFixed(3);
    return `${minutes}:${seconds.padStart(6, '0')}`;
  };

  useEffect(() => {
    // 1. Fetch available sessions
    fetch('http://localhost:8000/api/v1/live/sessions')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) setAvailableSessions(data);
      })
      .catch(() => {});

    // 2. Fetch standings
    fetch('http://localhost:8000/api/v1/standings/drivers')
      .then(res => res.json())
      .then(data => {
        setStandings(data);
        if (data.length > 1) {
          setSelectedDriver(data[1].driver.code);
          setSelectedRival(data[0].driver.code);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!selectedDriver) return;
    const rivalParam = selectedRival ? `&rival_code=${selectedRival}` : '';
    fetch(`http://localhost:8000/api/v1/championship/calculator?driver_code=${selectedDriver}${rivalParam}&remaining_gps=23&remaining_sprints=6`)
      .then(res => res.json())
      .then(data => {
        if (data.status === 'SUCCESS') setCalculatorData(data);
      })
      .catch(() => {});
  }, [selectedDriver, selectedRival]);

  useEffect(() => {
    // Clear previous session data so old session values cannot linger during switch
    setLiveData(null);
    setLoading(true);

    let activeSession = selectedSessionId;

    fetch(`http://localhost:8000/api/v1/live/${selectedSessionId}/snapshot`)
      .then(res => res.json())
      .then(data => {
        if (activeSession === selectedSessionId && data && data.session_id) {
          setLiveData(data);
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));

    let ws: WebSocket | null = null;
    let isSubscribed = true;

    try {
      ws = new WebSocket(`ws://localhost:8000/ws/live/${selectedSessionId}`);
      ws.onopen = () => {
        if (isSubscribed) setConnected(true);
      };
      ws.onmessage = (event) => {
        if (!isSubscribed) return;
        try {
          const msg = JSON.parse(event.data);
          // Pass control messages (PING / PONG)
          if (msg.type === 'PING' || msg.type === 'PONG') {
            return;
          }
          // Data-bearing events must belong strictly to the active selectedSessionId.
          // Reject any data-bearing message with mismatched or absent session_id.
          if (!msg.session_id || msg.session_id !== selectedSessionId) {
            return;
          }
          if (msg.type === 'SNAPSHOT') {
            setLiveData(msg.payload);
          } else if (msg.type === 'TIMING') {
            setLiveData(prev => prev ? {
              ...prev,
              current_lap: msg.payload?.current_lap ?? prev.current_lap,
              track_status: msg.payload?.track_status ?? prev.track_status,
              timing_tower: msg.payload?.timing_tower ?? prev.timing_tower,
              data_state: msg.data_state ?? prev.data_state
            } : prev);
          } else if (msg.type === 'MAP_POSITIONS') {
            setLiveData(prev => prev ? {
              ...prev,
              driver_map_positions: msg.payload
            } : prev);
          } else if (msg.type === 'TELEMETRY') {
            setLiveData(prev => prev ? {
              ...prev,
              telemetry: msg.payload
            } : prev);
          } else if (msg.type === 'RACE_CONTROL') {
            setLiveData(prev => {
              if (!prev) return prev;
              const prevRc = prev.race_control || [];
              const updatedRc = [...prevRc, msg.payload].slice(-30);
              return {
                ...prev,
                race_control: updatedRc,
                track_status: msg.payload?.flag === 'RED' ? 'RED' : (msg.payload?.flag?.includes('YELLOW') ? 'YELLOW' : prev.track_status)
              };
            });
          }
        } catch (_) {}
      };
      ws.onclose = () => {
        if (isSubscribed) setConnected(false);
      };
      ws.onerror = () => {
        if (isSubscribed) setConnected(false);
      };
    } catch (_) {}

    return () => {
      isSubscribed = false;
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onclose = null;
        ws.onerror = null;
        ws.close();
      }
    };
  }, [selectedSessionId]);

  const calc = calculatorData?.calculation;

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      {/* Top Header */}
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <Text style={styles.brandBadge}>APEX</Text>
          <Text style={styles.brandTitle}>GP</Text>
        </View>
        <View style={styles.headerActions}>
          <View style={[styles.statusDot, connected ? styles.dotGreen : styles.dotOrange]} />
          <TouchableOpacity 
            style={[styles.shieldButton, spoilerShield && styles.shieldButtonActive]}
            onPress={() => setSpoilerShield(!spoilerShield)}
          >
            <Text style={styles.shieldText}>SPOILER: {spoilerShield ? "ON" : "OFF"}</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Dynamic Session Switcher Bar (Mobile) */}
      {availableSessions.length > 0 && activeTab === 'LIVE' && (
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.sessionPickerScroll}>
          {availableSessions.map((s) => (
            <TouchableOpacity
              key={s.session_id}
              style={[
                styles.sessionPill,
                selectedSessionId === s.session_id && styles.sessionPillActive
              ]}
              onPress={() => setSelectedSessionId(s.session_id)}
            >
              <Text style={[
                styles.sessionPillText,
                selectedSessionId === s.session_id && styles.sessionPillTextActive
              ]}>
                {s.data_state === "LIVE" ? "🔴 " : ""}{s.session_name}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      )}

      {/* Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity 
          style={[styles.tabItem, activeTab === 'LIVE' && styles.tabItemActive]}
          onPress={() => setActiveTab('LIVE')}
        >
          <Text style={[styles.tabText, activeTab === 'LIVE' && styles.tabTextActive]}>LIVE</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tabItem, activeTab === 'STANDINGS' && styles.tabItemActive]}
          onPress={() => setActiveTab('STANDINGS')}
        >
          <Text style={[styles.tabText, activeTab === 'STANDINGS' && styles.tabTextActive]}>STANDINGS</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tabItem, activeTab === 'CHAMPIONSHIP' && styles.tabItemActive]}
          onPress={() => setActiveTab('CHAMPIONSHIP')}
        >
          <Text style={[styles.tabText, activeTab === 'CHAMPIONSHIP' && styles.tabTextActive]}>INTELLIGENCE</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {activeTab === 'LIVE' ? (
          <View>
            {/* Live Session Card */}
            <View style={styles.liveBanner}>
              <View style={styles.bannerRow}>
                <Text style={styles.trackStatusBadge}>
                  {liveData?.track_status || "GREEN"}
                </Text>
                <Text style={styles.lapCounter}>
                  LAP {liveData?.current_lap || 0} / {liveData?.total_laps || 57}
                </Text>
              </View>
              <Text style={styles.sessionTitle}>{liveData?.session_name || "Bahrain Grand Prix"}</Text>
              <Text style={styles.sessionMeta}>
                {liveData?.circuit_name} • {liveData?.weather?.track_temperature}°C TRACK • FEED: {liveData?.provenance?.data_state || "HISTORICAL"}
              </Text>
              <Text style={styles.provenanceNote}>
                PROVENANCE: {liveData?.provenance?.source} ({liveData?.provenance?.data_state})
              </Text>
            </View>

            {/* Sub-view switcher for Mobile Live Race Center */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.subViewPickerScroll}>
              <TouchableOpacity
                style={[styles.subViewPill, liveSubView === 'TIMING' && styles.subViewPillActive]}
                onPress={() => setLiveSubView('TIMING')}
              >
                <Text style={[styles.subViewText, liveSubView === 'TIMING' && styles.subViewTextActive]}>TIMING</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.subViewPill, liveSubView === 'MAP' && styles.subViewPillActive]}
                onPress={() => setLiveSubView('MAP')}
              >
                <Text style={[styles.subViewText, liveSubView === 'MAP' && styles.subViewTextActive]}>CIRCUIT MAP ({liveData?.driver_map_positions?.length || 0})</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.subViewPill, liveSubView === 'TELEMETRY' && styles.subViewPillActive]}
                onPress={() => setLiveSubView('TELEMETRY')}
              >
                <Text style={[styles.subViewText, liveSubView === 'TELEMETRY' && styles.subViewTextActive]}>TELEMETRY</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.subViewPill, liveSubView === 'PITS' && styles.subViewPillActive]}
                onPress={() => setLiveSubView('PITS')}
              >
                <Text style={[styles.subViewText, liveSubView === 'PITS' && styles.subViewTextActive]}>PIT STOPS ({liveData?.pit_stops?.length || 0})</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.subViewPill, liveSubView === 'RACE_CONTROL' && styles.subViewPillActive]}
                onPress={() => setLiveSubView('RACE_CONTROL')}
              >
                <Text style={[styles.subViewText, liveSubView === 'RACE_CONTROL' && styles.subViewTextActive]}>RACE CONTROL ({liveData?.race_control?.length || 0})</Text>
              </TouchableOpacity>
            </ScrollView>

            {/* SUB-VIEW 1: TIMING TOWER */}
            {liveSubView === 'TIMING' && (
              <View>
                <Text style={styles.sectionTitle}>TIMING TOWER</Text>
                {liveData?.timing_tower?.map((t) => (
                  <TouchableOpacity
                    key={t.driver_number}
                    style={[styles.timingRow, selectedDriverNum === t.driver_number && styles.timingRowSelected]}
                    onPress={() => setSelectedDriverNum(t.driver_number)}
                  >
                    <View style={styles.timingRowLeft}>
                      <Text style={styles.positionText}>{spoilerShield ? "•" : `P${t.position}`}</Text>
                      {/* Gain / Loss indicator */}
                      {!spoilerShield && (
                        <View style={styles.gainBox}>
                          {typeof t.positions_gained === 'number' && Number.isFinite(t.positions_gained) ? (
                            t.positions_gained > 0 ? (
                              <Text style={styles.gainGreen}>▲{t.positions_gained}</Text>
                            ) : t.positions_gained < 0 ? (
                              <Text style={styles.gainRed}>▼{Math.abs(t.positions_gained)}</Text>
                            ) : (
                              <Text style={styles.gainGray}>-</Text>
                            )
                          ) : (
                            <Text style={styles.gainGray}>-</Text>
                          )}
                        </View>
                      )}
                      <View style={[styles.teamAccent, { backgroundColor: t.team_color }]} />
                      <View style={styles.driverInfo}>
                        <View style={styles.driverTopRow}>
                          <Text style={styles.driverCode}>{t.driver_code}</Text>
                          {typeof t.current_lap === 'number' && t.current_lap > 0 ? (
                            <Text style={styles.driverLap}>L{t.current_lap}</Text>
                          ) : null}
                        </View>
                        <Text style={styles.teamName} numberOfLines={1}>{t.team_name}</Text>
                        {/* Sectors S1 / S2 / S3 */}
                        {!spoilerShield && (
                          <View style={styles.sectorRow}>
                            <Text style={styles.sectorText}>
                              S1: {typeof t.sectors?.sector_1 === 'number' && Number.isFinite(t.sectors.sector_1) && t.sectors.sector_1 > 0 ? t.sectors.sector_1.toFixed(1) : '-'}
                            </Text>
                            <Text style={styles.sectorDot}>•</Text>
                            <Text style={styles.sectorText}>
                              S2: {typeof t.sectors?.sector_2 === 'number' && Number.isFinite(t.sectors.sector_2) && t.sectors.sector_2 > 0 ? t.sectors.sector_2.toFixed(1) : '-'}
                            </Text>
                            <Text style={styles.sectorDot}>•</Text>
                            <Text style={styles.sectorText}>
                              S3: {typeof t.sectors?.sector_3 === 'number' && Number.isFinite(t.sectors.sector_3) && t.sectors.sector_3 > 0 ? t.sectors.sector_3.toFixed(1) : '-'}
                            </Text>
                          </View>
                        )}
                      </View>
                    </View>
                    <View style={styles.timingRowRight}>
                      <View style={styles.tireBadge}>
                        <Text style={styles.tireText}>{t.tire_compound?.[0] || "?"} L{t.stint_lap_count ?? 0}</Text>
                      </View>
                      <View style={styles.lapTimes}>
                        <Text style={styles.gapText}>
                          {spoilerShield ? "-" : (
                            t.gap_to_leader === 0 ? "LEADER" :
                            (typeof t.gap_to_leader === 'number' && Number.isFinite(t.gap_to_leader) && t.gap_to_leader > 0) ? `+${t.gap_to_leader.toFixed(3)}s` : "-"
                          )}
                        </Text>
                        <Text style={styles.intervalText}>
                          {spoilerShield ? "-" : (
                            t.interval === 0 ? "INT: -" :
                            (typeof t.interval === 'number' && Number.isFinite(t.interval) && t.interval > 0) ? `INT: +${t.interval.toFixed(3)}s` : "INT: -"
                          )}
                        </Text>
                        <Text style={styles.bestTimeText}>
                          {spoilerShield ? "-:--.---" : formatLapTime(t.best_lap_time)}
                        </Text>
                      </View>
                    </View>
                  </TouchableOpacity>
                ))}
              </View>
            )}

            {/* SUB-VIEW 2: CIRCUIT MAP (D4-01) */}
            {liveSubView === 'MAP' && (() => {
              const circuitName = liveData?.circuit_name || "Grand Prix Circuit";
              const isBahrain = circuitName.toLowerCase().includes("bahrain") || circuitName.toLowerCase().includes("sakhir");
              return (
                <View style={styles.mapCard}>
                  <View style={styles.mapHeaderRow}>
                    <Text style={styles.mapCircuitTitle}>{circuitName}</Text>
                    <Text style={styles.mapBeaconCount}>
                      {isBahrain ? `GPS ACTIVE: ${liveData?.driver_map_positions?.length || 0} CARS` : "LAYOUT PENDING"}
                    </Text>
                  </View>
                  {!isBahrain ? (
                    <View style={styles.emptyBox}>
                      <Text style={styles.emptyText}>Circuit Layout Unavailable</Text>
                      <Text style={styles.emptyTelemSub}>
                        Verified track geometry is calibrated for Bahrain GP. Geometry for {circuitName} is scheduled for Release 4.
                      </Text>
                    </View>
                  ) : (
                    <>
                      {/* Circuit Track Canvas Area */}
                      <View style={styles.trackCanvasContainer}>
                        <View style={styles.trackCenterline} />
                        <View style={styles.startFinishLine}>
                          <Text style={styles.startFinishText}>S/F</Text>
                        </View>
                        {/* Driver beacons positioned on track canvas */}
                        {liveData?.driver_map_positions?.map((pos) => {
                          // Normalize OpenF1 coordinates (bounds approx 3000..6500 x, -600..0 y)
                          const normX = Math.max(10, Math.min(270, 20 + ((pos.x - 3000) / 3800) * 240));
                          const normY = Math.max(10, Math.min(180, 25 + ((pos.y + 600) / 600) * 140));
                          const isSelected = selectedDriverNum === pos.driver_number;
                          return (
                            <TouchableOpacity
                              key={pos.driver_number}
                              style={[
                                styles.carBeacon,
                                { left: normX, top: normY, borderColor: pos.team_color },
                                isSelected && styles.carBeaconSelected
                              ]}
                              onPress={() => setSelectedDriverNum(pos.driver_number)}
                            >
                              <Text style={[styles.carBeaconText, { color: pos.team_color }]}>{pos.driver_code}</Text>
                            </TouchableOpacity>
                          );
                        })}
                      </View>
                      <Text style={styles.mapFooterNote}>Interactive Track View • Tap any car beacon to inspect telemetry</Text>
                    </>
                  )}
                </View>
              );
            })()}

            {/* SUB-VIEW 3: TELEMETRY INSPECTOR (D5-01) */}
            {liveSubView === 'TELEMETRY' && (() => {
              const driverTelem = liveData?.telemetry?.find(t => t.driver_number === selectedDriverNum);
              const driverTiming = liveData?.timing_tower?.find(t => t.driver_number === selectedDriverNum);
              return (
                <View style={styles.telemetryCard}>
                  <View style={styles.telemetryHeader}>
                    <View style={styles.driverBadgeRow}>
                      <View style={[styles.teamAccent, { backgroundColor: driverTiming?.team_color || '#FFF' }]} />
                      <Text style={styles.telemetryDriverName}>
                        #{selectedDriverNum} {driverTiming?.driver_name || `Driver ${selectedDriverNum}`} ({driverTiming?.driver_code || '---'})
                      </Text>
                    </View>
                    <Text style={styles.telemetryTeamName}>{driverTiming?.team_name || 'F1 Team'}</Text>
                  </View>

                  {/* Driver Picker Pills */}
                  <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.telemPickerScroll}>
                    {liveData?.timing_tower?.map((t) => (
                      <TouchableOpacity
                        key={t.driver_number}
                        style={[
                          styles.telemDriverPill,
                          selectedDriverNum === t.driver_number && styles.telemDriverPillActive
                        ]}
                        onPress={() => setSelectedDriverNum(t.driver_number)}
                      >
                        <Text style={[
                          styles.telemDriverText,
                          selectedDriverNum === t.driver_number && styles.telemDriverTextActive
                        ]}>
                          {t.driver_code}
                        </Text>
                      </TouchableOpacity>
                    ))}
                  </ScrollView>

                  {driverTelem ? (
                    <View style={styles.gaugeGrid}>
                      <View style={styles.gaugeBox}>
                        <Text style={styles.gaugeLabel}>SPEED</Text>
                        <Text style={styles.gaugeValue}>{driverTelem.speed} <Text style={styles.gaugeUnit}>km/h</Text></Text>
                      </View>
                      <View style={styles.gaugeBox}>
                        <Text style={styles.gaugeLabel}>GEAR</Text>
                        <Text style={styles.gaugeValueHighlight}>{driverTelem.n_gear}</Text>
                      </View>
                      <View style={styles.gaugeBox}>
                        <Text style={styles.gaugeLabel}>THROTTLE</Text>
                        <Text style={styles.gaugeValueGreen}>{driverTelem.throttle}%</Text>
                      </View>
                      <View style={styles.gaugeBox}>
                        <Text style={styles.gaugeLabel}>BRAKE</Text>
                        <Text style={styles.gaugeValueRed}>{driverTelem.brake > 0 ? `${driverTelem.brake}%` : 'OFF'}</Text>
                      </View>
                      <View style={styles.gaugeBox}>
                        <Text style={styles.gaugeLabel}>ENGINE RPM</Text>
                        <Text style={styles.gaugeValue}>{driverTelem.rpm}</Text>
                      </View>
                      <View style={styles.gaugeBox}>
                        <Text style={styles.gaugeLabel}>DRS</Text>
                        <Text style={driverTelem.drs ? styles.gaugeValueGreen : styles.gaugeValueMuted}>
                          {driverTelem.drs ? 'OPEN' : 'CLOSED'}
                        </Text>
                      </View>
                    </View>
                  ) : (
                    <View style={styles.emptyTelemBox}>
                      <Text style={styles.emptyTelemText}>No live telemetry packets for car #{selectedDriverNum}.</Text>
                      <Text style={styles.emptyTelemSub}>Select another driver from the pills above.</Text>
                    </View>
                  )}
                </View>
              );
            })()}

            {/* SUB-VIEW 4: PIT STOPS */}
            {liveSubView === 'PITS' && (
              <View style={styles.pitStopsContainer}>
                <Text style={styles.sectionTitle}>PIT STOP LOG</Text>
                {liveData?.pit_stops && liveData.pit_stops.length > 0 ? (
                  liveData.pit_stops.map((p, idx) => (
                    <View key={idx} style={styles.pitCard}>
                      <View>
                        <Text style={styles.pitCarNum}>CAR #{p.driver_number}</Text>
                        <Text style={styles.pitLap}>Lap {p.lap_number}</Text>
                      </View>
                      <View style={styles.pitDurations}>
                        <Text style={styles.pitDurationStop}>{p.pit_duration ? `${p.pit_duration}s stop` : 'Stop'}</Text>
                        {p.lane_duration && (
                          <Text style={styles.pitDurationLane}>{p.lane_duration}s lane</Text>
                        )}
                      </View>
                    </View>
                  ))
                ) : (
                  <View style={styles.emptyBox}>
                    <Text style={styles.emptyText}>No pit stops recorded yet for this session.</Text>
                  </View>
                )}
              </View>
            )}

            {/* SUB-VIEW 5: RACE CONTROL */}
            {liveSubView === 'RACE_CONTROL' && (
              <View style={styles.raceControlContainer}>
                <Text style={styles.sectionTitle}>OFFICIAL RACE CONTROL TIMELINE</Text>
                {liveData?.race_control && liveData.race_control.length > 0 ? (
                  liveData.race_control.map((rc, idx) => (
                    <View key={idx} style={styles.rcCard}>
                      <View style={styles.rcTopRow}>
                        {rc.flag && (
                          <View style={[
                            styles.rcFlagBadge,
                            rc.flag === 'GREEN' || rc.flag === 'CLEAR' ? styles.rcFlagGreen :
                            rc.flag === 'RED' ? styles.rcFlagRed : styles.rcFlagYellow
                          ]}>
                            <Text style={styles.rcFlagText}>{rc.flag}</Text>
                          </View>
                        )}
                        <Text style={styles.rcCategory}>{rc.category}</Text>
                        {rc.lap_number && <Text style={styles.rcLap}>Lap {rc.lap_number}</Text>}
                      </View>
                      <Text style={styles.rcMessage}>{rc.message}</Text>
                    </View>
                  ))
                ) : (
                  <View style={styles.emptyBox}>
                    <Text style={styles.emptyText}>No race control notices posted.</Text>
                  </View>
                )}
              </View>
            )}
          </View>
        ) : activeTab === 'STANDINGS' ? (
          <View>
            <Text style={styles.sectionTitle}>DRIVER WORLD CHAMPIONSHIP</Text>
            {standings.map((s, index) => (
              <View key={index} style={styles.timingRow}>
                <Text style={styles.positionText}>{spoilerShield ? "•" : `P${s.position}`}</Text>
                <View style={styles.driverInfo}>
                  <Text style={styles.driverCode}>{s.driver.first_name} {s.driver.last_name}</Text>
                  <Text style={styles.teamName}>{s.driver.constructor_name}</Text>
                </View>
                <Text style={styles.pointsText}>{spoilerShield ? "••" : `${s.points} PTS`}</Text>
              </View>
            ))}
          </View>
        ) : (
          <View style={styles.intelContainer}>
            <Text style={styles.sectionTitle}>CHAMPIONSHIP SCENARIO CALCULATOR</Text>
            <Text style={styles.intelSub}>What does this driver need to win the title?</Text>

            {/* Contender selector pills */}
            <Text style={styles.fieldLabel}>CONTENDER</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pickerScroll}>
              {standings.map((s) => (
                <TouchableOpacity
                  key={s.driver.code}
                  style={[
                    styles.pickerPill,
                    selectedDriver === s.driver.code && styles.pickerPillActive
                  ]}
                  onPress={() => setSelectedDriver(s.driver.code)}
                >
                  <Text style={[
                    styles.pickerText,
                    selectedDriver === s.driver.code && styles.pickerTextActive
                  ]}>
                    {s.driver.code}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            <Text style={styles.fieldLabel}>COMPARE TO RIVAL</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pickerScroll}>
              {standings.map((s) => (
                <TouchableOpacity
                  key={s.driver.code}
                  style={[
                    styles.pickerPill,
                    selectedRival === s.driver.code && styles.pickerPillRivalActive
                  ]}
                  onPress={() => setSelectedRival(s.driver.code)}
                >
                  <Text style={[
                    styles.pickerText,
                    selectedRival === s.driver.code && styles.pickerTextActive
                  ]}>
                    {s.driver.code}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>

            {/* Calculator Card */}
            {calc && (
              <View style={styles.calcCard}>
                <View style={styles.calcHeader}>
                  <Text style={styles.calcTitle}>{calc.target_driver} vs {calc.rival_driver}</Text>
                  <Text style={[
                    styles.calcBadge,
                    calc.is_eliminated ? styles.badgeEliminated : styles.badgeEligible
                  ]}>
                    {calc.is_eliminated ? "ELIMINATED" : calc.clinched_now ? "CHAMPION CLINCHED" : "TITLE ELIGIBLE"}
                  </Text>
                </View>

                <View style={styles.metricRow}>
                  <View style={styles.metricBox}>
                    <Text style={styles.metricLabel}>GAP TO RIVAL</Text>
                    <Text style={styles.metricValue}>
                      {spoilerShield ? "••" : (calc.point_gap > 0 ? `-${calc.point_gap}` : `+${Math.abs(calc.point_gap)}`)}
                    </Text>
                  </View>
                  <View style={styles.metricBox}>
                    <Text style={styles.metricLabel}>MIN PTS NEEDED</Text>
                    <Text style={styles.metricValueHighlight}>
                      {calc.min_points_needed_if_rival_zero ?? "N/A"}
                    </Text>
                  </View>
                  <View style={styles.metricBox}>
                    <Text style={styles.metricLabel}>RIVAL CAP</Text>
                    <Text style={styles.metricValueWarn}>
                      ≤ {calc.max_rival_points_allowed}
                    </Text>
                  </View>
                </View>

                {calc.scenarios && calc.scenarios.map((sc: any, idx: number) => (
                  <View key={idx} style={styles.scenarioCard}>
                    <Text style={styles.scenarioTitle}>{sc.name}</Text>
                    <Text style={styles.scenarioDesc}>{sc.description}</Text>
                    <View style={styles.scenarioStats}>
                      <Text style={styles.scenarioStatTarget}>Target: +{sc.target_score} pts</Text>
                      <Text style={styles.scenarioStatRival}>Rival Cap: ≤ {sc.rival_max_allowed} pts</Text>
                    </View>
                  </View>
                ))}

                {/* Monte Carlo Simulation Quick Button */}
                <TouchableOpacity
                  style={styles.simButton}
                  onPress={() => {
                    fetch('http://localhost:8000/api/v1/championship/simulate?iterations=500&remaining_gps=23&remaining_sprints=6')
                      .then(res => res.json())
                      .then(data => {
                        if (data.probabilities) {
                          setCalculatorData((prev: any) => ({ ...prev, simulation: data.probabilities }));
                        }
                      })
                      .catch(() => {});
                  }}
                >
                  <Text style={styles.simButtonText}>🎲 Run 500x Monte Carlo Forecast</Text>
                </TouchableOpacity>

                {calculatorData?.simulation && (
                  <View style={styles.simResultsBox}>
                    <Text style={styles.simResultsTitle}>TITLE PROBABILITY (500 SIMS):</Text>
                    {calculatorData.simulation.slice(0, 4).map((p: any) => (
                      <View key={p.driver_code} style={styles.simRow}>
                        <Text style={styles.simDriver}>{p.driver_code}</Text>
                        <Text style={styles.simExpPts}>{p.expected_final_points} EXP PTS</Text>
                        <Text style={styles.simPct}>{p.championship_probability_pct}%</Text>
                      </View>
                    ))}
                  </View>
                )}
              </View>
            )}
          </View>
        )}

      </ScrollView>
    </SafeAreaView>
  );
}


const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0D0E12',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
  },
  brandRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  brandBadge: {
    backgroundColor: '#E10600',
    color: '#FFF',
    fontWeight: '900',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    fontSize: 16,
    marginRight: 4,
  },
  brandTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  headerActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  dotGreen: {
    backgroundColor: '#30D158',
  },
  dotOrange: {
    backgroundColor: '#FF9F0A',
  },
  shieldButton: {
    backgroundColor: '#272A35',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 4,
  },
  shieldButtonActive: {
    backgroundColor: '#E10600',
  },
  shieldText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  tabBar: {
    flexDirection: 'row',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    backgroundColor: '#15171E',
  },
  tabItem: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
  },
  tabItemActive: {
    borderBottomWidth: 2,
    borderBottomColor: '#E10600',
  },
  tabText: {
    color: '#8F96A3',
    fontSize: 12,
    fontWeight: 'bold',
  },
  tabTextActive: {
    color: '#FFF',
  },
  content: {
    padding: 16,
  },
  liveBanner: {
    backgroundColor: '#15171E',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
  },
  bannerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  trackStatusBadge: {
    backgroundColor: '#30D158',
    color: '#000',
    fontSize: 10,
    fontWeight: '900',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
  },
  lapCounter: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  sessionTitle: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  sessionMeta: {
    color: '#8F96A3',
    fontSize: 12,
    marginTop: 2,
  },
  provenanceNote: {
    color: '#64D2FF',
    fontSize: 10,
    marginTop: 6,
  },
  sectionTitle: {
    color: '#8F96A3',
    fontSize: 12,
    fontWeight: 'bold',
    letterSpacing: 1,
    marginBottom: 10,
  },
  timingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  timingRowLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    marginRight: 8,
  },
  timingRowRight: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  positionText: {
    color: '#FFF',
    fontWeight: 'bold',
    width: 24,
    fontSize: 13,
    fontFamily: 'monospace',
  },
  gainBox: {
    width: 22,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 4,
  },
  gainGreen: {
    color: '#30D158',
    fontSize: 10,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  gainRed: {
    color: '#E10600',
    fontSize: 10,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  gainGray: {
    color: '#8F96A3',
    fontSize: 11,
    fontFamily: 'monospace',
  },
  teamAccent: {
    width: 3,
    height: 32,
    borderRadius: 1.5,
    marginRight: 8,
  },
  driverInfo: {
    flex: 1,
  },
  driverTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  driverCode: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 13,
  },
  driverLap: {
    color: '#8F96A3',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  teamName: {
    color: '#8F96A3',
    fontSize: 11,
  },
  sectorRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
    gap: 4,
  },
  sectorText: {
    color: '#8F96A3',
    fontSize: 9,
    fontFamily: 'monospace',
  },
  sectorDot: {
    color: '#3F4452',
    fontSize: 8,
  },
  tireBadge: {
    backgroundColor: '#272A35',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    marginRight: 10,
  },
  tireText: {
    color: '#FFCC00',
    fontSize: 10,
    fontWeight: 'bold',
  },
  lapTimes: {
    alignItems: 'flex-end',
    minWidth: 70,
  },
  gapText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  intervalText: {
    color: '#8F96A3',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  bestTimeText: {
    color: '#64D2FF',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  pointsText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 14,
    fontFamily: 'monospace',
  },
  sessionPickerScroll: {
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingVertical: 8,
    paddingHorizontal: 12,
  },
  sessionPill: {
    backgroundColor: '#0D0E12',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 14,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 8,
  },
  sessionPillActive: {
    backgroundColor: '#E10600',
    borderColor: '#E10600',
  },
  sessionPillText: {
    color: '#8F96A3',
    fontSize: 11,
    fontWeight: '600',
  },
  sessionPillTextActive: {
    color: '#FFFFFF',
    fontWeight: 'bold',
  },
  intelContainer: {
    paddingBottom: 24,
  },
  intelSub: {
    color: '#8F96A3',
    fontSize: 12,
    marginBottom: 12,
  },
  fieldLabel: {
    color: '#8F96A3',
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 6,
    letterSpacing: 1,
  },
  pickerScroll: {
    marginBottom: 14,
  },
  pickerPill: {
    backgroundColor: '#15171E',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
  },
  pickerPillActive: {
    backgroundColor: '#E10600',
    borderColor: '#E10600',
  },
  pickerPillRivalActive: {
    backgroundColor: '#3671C6',
    borderColor: '#3671C6',
  },
  pickerText: {
    color: '#8F96A3',
    fontWeight: 'bold',
    fontSize: 12,
  },
  pickerTextActive: {
    color: '#FFF',
  },
  calcCard: {
    backgroundColor: '#15171E',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#272A35',
    padding: 14,
    marginTop: 8,
  },
  calcHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingBottom: 8,
  },
  calcTitle: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  calcBadge: {
    fontSize: 10,
    fontWeight: 'bold',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  badgeEliminated: {
    backgroundColor: '#3B1214',
    color: '#FF6464',
  },
  badgeEligible: {
    backgroundColor: '#11331B',
    color: '#4ADE80',
  },
  metricRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 14,
  },
  metricBox: {
    backgroundColor: '#0D0E12',
    borderWidth: 1,
    borderColor: '#272A35',
    borderRadius: 8,
    padding: 8,
    flex: 1,
    marginHorizontal: 3,
  },
  metricLabel: {
    color: '#8F96A3',
    fontSize: 9,
    fontWeight: 'bold',
  },
  metricValue: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  metricValueHighlight: {
    color: '#64D2FF',
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  metricValueWarn: {
    color: '#FBBF24',
    fontSize: 13,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  scenarioCard: {
    backgroundColor: '#0D0E12',
    borderWidth: 1,
    borderColor: '#272A35',
    borderRadius: 8,
    padding: 10,
    marginBottom: 8,
  },
  scenarioTitle: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  scenarioDesc: {
    color: '#8F96A3',
    fontSize: 11,
    marginTop: 2,
  },
  scenarioStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    borderTopWidth: 1,
    borderTopColor: '#272A35',
    paddingTop: 6,
    marginTop: 6,
  },
  scenarioStatTarget: {
    color: '#64D2FF',
    fontSize: 11,
    fontFamily: 'monospace',
  },
  scenarioStatRival: {
    color: '#FBBF24',
    fontSize: 11,
    fontFamily: 'monospace',
  },
  simButton: {
    backgroundColor: '#E10600',
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  simButtonText: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
  },
  simResultsBox: {
    backgroundColor: '#0D0E12',
    borderWidth: 1,
    borderColor: '#272A35',
    borderRadius: 8,
    padding: 10,
    marginTop: 10,
  },
  simResultsTitle: {
    color: '#FFCC00',
    fontSize: 10,
    fontWeight: 'bold',
    marginBottom: 6,
    letterSpacing: 0.5,
  },
  simRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 3,
    borderBottomWidth: 1,
    borderBottomColor: '#1A1D26',
  },
  simDriver: {
    color: '#FFF',
    fontSize: 11,
    fontWeight: 'bold',
    width: 45,
  },
  simExpPts: {
    color: '#8F96A3',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  simPct: {
    color: '#64D2FF',
    fontSize: 11,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  subViewPickerScroll: {
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingVertical: 8,
    paddingHorizontal: 8,
    marginBottom: 10,
  },
  subViewPill: {
    backgroundColor: '#0D0E12',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 5,
    marginRight: 6,
  },
  subViewPillActive: {
    backgroundColor: '#E10600',
    borderColor: '#E10600',
  },
  subViewText: {
    color: '#8F96A3',
    fontSize: 10,
    fontWeight: 'bold',
  },
  subViewTextActive: {
    color: '#FFFFFF',
  },
  timingRowSelected: {
    backgroundColor: '#1E222D',
  },
  mapCard: {
    backgroundColor: '#15171E',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  mapHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  mapCircuitTitle: {
    color: '#FFF',
    fontSize: 13,
    fontWeight: 'bold',
  },
  mapBeaconCount: {
    color: '#30D158',
    fontSize: 9,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  trackCanvasContainer: {
    height: 220,
    backgroundColor: '#0D0E12',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#272A35',
    position: 'relative',
    overflow: 'hidden',
  },
  trackCenterline: {
    position: 'absolute',
    left: 20,
    right: 20,
    top: 40,
    bottom: 40,
    borderWidth: 14,
    borderColor: '#1E222D',
    borderRadius: 45,
  },
  startFinishLine: {
    position: 'absolute',
    left: 15,
    top: 100,
    width: 25,
    height: 4,
    backgroundColor: '#E10600',
    alignItems: 'center',
    justifyContent: 'center',
  },
  startFinishText: {
    color: '#FFF',
    fontSize: 7,
    fontWeight: '900',
    marginTop: -12,
  },
  carBeacon: {
    position: 'absolute',
    backgroundColor: '#0D0E12',
    borderWidth: 1.5,
    borderRadius: 6,
    paddingHorizontal: 4,
    paddingVertical: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  carBeaconSelected: {
    backgroundColor: '#272A35',
    transform: [{ scale: 1.15 }],
  },
  carBeaconText: {
    fontSize: 9,
    fontWeight: '900',
    fontFamily: 'monospace',
  },
  mapFooterNote: {
    color: '#8F96A3',
    fontSize: 9,
    marginTop: 8,
    textAlign: 'center',
  },
  telemetryCard: {
    backgroundColor: '#15171E',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 12,
    padding: 12,
    marginBottom: 16,
  },
  telemetryHeader: {
    marginBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingBottom: 8,
  },
  driverBadgeRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  telemetryDriverName: {
    color: '#FFF',
    fontSize: 14,
    fontWeight: 'bold',
  },
  telemetryTeamName: {
    color: '#8F96A3',
    fontSize: 11,
    marginTop: 2,
  },
  telemPickerScroll: {
    marginBottom: 12,
  },
  telemDriverPill: {
    backgroundColor: '#0D0E12',
    borderWidth: 1,
    borderColor: '#272A35',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginRight: 6,
  },
  telemDriverPillActive: {
    backgroundColor: '#272A35',
    borderColor: '#64D2FF',
  },
  telemDriverText: {
    color: '#8F96A3',
    fontSize: 10,
    fontWeight: 'bold',
  },
  telemDriverTextActive: {
    color: '#64D2FF',
  },
  gaugeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  gaugeBox: {
    backgroundColor: '#0D0E12',
    borderWidth: 1,
    borderColor: '#272A35',
    borderRadius: 8,
    padding: 10,
    width: '48%',
  },
  gaugeLabel: {
    color: '#8F96A3',
    fontSize: 9,
    fontWeight: 'bold',
  },
  gaugeValue: {
    color: '#FFF',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  gaugeValueHighlight: {
    color: '#64D2FF',
    fontSize: 18,
    fontWeight: '900',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  gaugeValueGreen: {
    color: '#30D158',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  gaugeValueRed: {
    color: '#FF6464',
    fontSize: 16,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  gaugeValueMuted: {
    color: '#8F96A3',
    fontSize: 14,
    fontWeight: 'bold',
    fontFamily: 'monospace',
    marginTop: 2,
  },
  gaugeUnit: {
    fontSize: 10,
    fontWeight: 'normal',
    color: '#8F96A3',
  },
  emptyTelemBox: {
    backgroundColor: '#0D0E12',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  emptyTelemText: {
    color: '#8F96A3',
    fontSize: 11,
    textAlign: 'center',
  },
  emptyTelemSub: {
    color: '#64D2FF',
    fontSize: 10,
    marginTop: 4,
  },
  pitStopsContainer: {
    marginBottom: 16,
  },
  pitCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  pitCarNum: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  pitLap: {
    color: '#8F96A3',
    fontSize: 10,
    marginTop: 2,
  },
  pitDurations: {
    alignItems: 'flex-end',
  },
  pitDurationStop: {
    color: '#30D158',
    fontSize: 12,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  pitDurationLane: {
    color: '#8F96A3',
    fontSize: 10,
    fontFamily: 'monospace',
  },
  raceControlContainer: {
    marginBottom: 16,
  },
  rcCard: {
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    padding: 10,
  },
  rcTopRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 4,
  },
  rcFlagBadge: {
    paddingHorizontal: 5,
    paddingVertical: 1,
    borderRadius: 3,
  },
  rcFlagGreen: {
    backgroundColor: '#30D158',
  },
  rcFlagYellow: {
    backgroundColor: '#FBBF24',
  },
  rcFlagRed: {
    backgroundColor: '#FF6464',
  },
  rcFlagText: {
    color: '#000',
    fontSize: 8,
    fontWeight: '900',
  },
  rcCategory: {
    color: '#E10600',
    fontSize: 10,
    fontWeight: 'bold',
    fontFamily: 'monospace',
  },
  rcLap: {
    color: '#8F96A3',
    fontSize: 10,
  },
  rcMessage: {
    color: '#FFF',
    fontSize: 11,
    fontFamily: 'monospace',
  },
  emptyBox: {
    backgroundColor: '#15171E',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
  },
  emptyText: {
    color: '#8F96A3',
    fontSize: 11,
  },
});



