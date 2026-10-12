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

export default function App() {
  const [activeTab, setActiveTab] = useState<'LIVE' | 'STANDINGS'>('LIVE');
  const [standings, setStandings] = useState<any[]>([]);
  const [liveData, setLiveData] = useState<LiveSnapshot | null>(null);
  const [spoilerShield, setSpoilerShield] = useState(false);
  const [connected, setConnected] = useState(false);
  const [loading, setLoading] = useState(true);

  const formatLapTime = (timeInSeconds?: number) => {
    if (!timeInSeconds) return "-:--.---";
    const minutes = Math.floor(timeInSeconds / 60);
    const seconds = (timeInSeconds % 60).toFixed(3);
    return `${minutes}:${seconds.padStart(6, '0')}`;
  };

  useEffect(() => {
    // 1. Fetch standings
    fetch('http://localhost:8000/api/v1/standings/drivers')
      .then(res => res.json())
      .then(data => setStandings(data))
      .catch(() => {});

    // 2. Fetch live snapshot REST fallback
    fetch('http://localhost:8000/api/v1/live/2024_01_race/snapshot')
      .then(res => res.json())
      .then(data => {
        if (data && data.session_id) {
          setLiveData(data);
          setLoading(false);
        }
      })
      .catch(() => setLoading(false));

    // 3. Connect to WebSocket
    let ws: WebSocket;
    try {
      ws = new WebSocket('ws://localhost:8000/ws/live/2024_01_race');
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
              timing_tower: msg.payload.timing_tower ?? prev.timing_tower
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
  }, []);

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

      {/* Tabs */}
      <View style={styles.tabBar}>
        <TouchableOpacity 
          style={[styles.tabItem, activeTab === 'LIVE' && styles.tabItemActive]}
          onPress={() => setActiveTab('LIVE')}
        >
          <Text style={[styles.tabText, activeTab === 'LIVE' && styles.tabTextActive]}>LIVE RACE CENTER</Text>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.tabItem, activeTab === 'STANDINGS' && styles.tabItemActive]}
          onPress={() => setActiveTab('STANDINGS')}
        >
          <Text style={[styles.tabText, activeTab === 'STANDINGS' && styles.tabTextActive]}>STANDINGS</Text>
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
                {liveData?.circuit_name} • {liveData?.weather?.track_temperature}°C TRACK
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
        ) : (
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
});
