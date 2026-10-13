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
  gap_to_leader?: number;
  interval?: number;
  last_lap_time?: number;
  best_lap_time?: number;
  tire_compound?: string;
  stint_lap_count: number;
  positions_gained: number;
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

  const formatLapTime = (timeInSeconds?: number) => {
    if (!timeInSeconds) return "-:--.---";
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
    // Fetch live snapshot REST fallback for selected session
    setLoading(true);
    fetch(`http://localhost:8000/api/v1/live/${selectedSessionId}/snapshot`)
      .then(res => res.json())
      .then(data => {
        if (data && data.session_id) {
          setLiveData(data);
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));

    // Connect to WebSocket for selected session
    let ws: WebSocket;
    try {
      ws = new WebSocket(`ws://localhost:8000/ws/live/${selectedSessionId}`);
      ws.onopen = () => setConnected(true);
      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'SNAPSHOT') {
            setLiveData(msg.payload);
          } else if (msg.type === 'TIMING') {
            setLiveData(prev => prev ? {
              ...prev,
              current_lap: msg.payload.current_lap ?? prev.current_lap,
              track_status: msg.payload.track_status ?? prev.track_status,
              timing_tower: msg.payload.timing_tower ?? prev.timing_tower,
              data_state: msg.data_state ?? prev.data_state
            } : prev);
          }
        } catch (_) {}
      };
      ws.onclose = () => setConnected(false);
      ws.onerror = () => setConnected(false);
    } catch (_) {}

    return () => {
      if (ws) ws.close();
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

            {/* Timing Tower */}
            <Text style={styles.sectionTitle}>TIMING TOWER</Text>

            {liveData?.timing_tower?.map((t) => (
              <View key={t.driver_number} style={styles.timingRow}>
                <Text style={styles.positionText}>{spoilerShield ? "•" : `P${t.position}`}</Text>
                <View style={[styles.teamAccent, { backgroundColor: t.team_color }]} />
                <View style={styles.driverInfo}>
                  <Text style={styles.driverCode}>{t.driver_code}</Text>
                  <Text style={styles.teamName}>{t.team_name}</Text>
                </View>
                <View style={styles.tireBadge}>
                  <Text style={styles.tireText}>{t.tire_compound?.[0] || "?"}</Text>
                </View>
                <View style={styles.lapTimes}>
                  <Text style={styles.gapText}>
                    {spoilerShield ? "-" : (t.gap_to_leader === 0 ? "LEADER" : `+${t.gap_to_leader?.toFixed(3)}s`)}
                  </Text>
                  <Text style={styles.bestTimeText}>
                    {spoilerShield ? "-:--.---" : formatLapTime(t.best_lap_time)}
                  </Text>
                </View>
              </View>
            ))}
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
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingVertical: 10,
    paddingHorizontal: 12,
  },
  positionText: {
    color: '#FFF',
    fontWeight: 'bold',
    width: 28,
    fontSize: 13,
    fontFamily: 'monospace',
  },
  teamAccent: {
    width: 3,
    height: 24,
    borderRadius: 1.5,
    marginRight: 8,
  },
  driverInfo: {
    flex: 1,
  },
  driverCode: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 13,
  },
  teamName: {
    color: '#8F96A3',
    fontSize: 11,
  },
  tireBadge: {
    backgroundColor: '#272A35',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 3,
    marginRight: 12,
  },
  tireText: {
    color: '#FFCC00',
    fontSize: 10,
    fontWeight: 'bold',
  },
  lapTimes: {
    alignItems: 'flex-end',
  },
  gapText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
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
});


