import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, ScrollView, TouchableOpacity, SafeAreaView, StatusBar } from 'react-native';

export default function App() {
  const [standings, setStandings] = useState([]);
  const [spoilerShield, setSpoilerShield] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/standings/drivers')
      .then(res => res.json())
      .then(data => setStandings(data))
      .catch(() => {});
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" />
      <View style={styles.header}>
        <View style={styles.brandRow}>
          <Text style={styles.brandBadge}>APEX</Text>
          <Text style={styles.brandTitle}>GP</Text>
        </View>
        <TouchableOpacity 
          style={[styles.shieldButton, spoilerShield && styles.shieldButtonActive]}
          onPress={() => setSpoilerShield(!spoilerShield)}
        >
          <Text style={styles.shieldText}>SPOILER: {spoilerShield ? "ON" : "OFF"}</Text>
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        <View style={styles.card}>
          <Text style={styles.cardHeader}>ROUND 1 • COMPLETED</Text>
          <Text style={styles.cardTitle}>Bahrain Grand Prix 2024</Text>
          <Text style={styles.cardSubtitle}>Sakhir • 57 Laps • Fastest Lap: 1:32.608 (VER)</Text>
        </View>

        <Text style={styles.sectionTitle}>DRIVER STANDINGS</Text>
        {standings.map((s, index) => (
          <View key={index} style={styles.driverRow}>
            <Text style={styles.positionText}>{spoilerShield ? "•" : `P${s.position}`}</Text>
            <View style={styles.driverInfo}>
              <Text style={styles.driverName}>{s.driver.first_name} {s.driver.last_name}</Text>
              <Text style={styles.teamName}>{s.driver.constructor_name}</Text>
            </View>
            <Text style={styles.pointsText}>{spoilerShield ? "••" : `${s.points} PTS`}</Text>
          </View>
        ))}
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
  content: {
    padding: 16,
  },
  card: {
    backgroundColor: '#15171E',
    borderColor: '#272A35',
    borderWidth: 1,
    borderRadius: 8,
    padding: 16,
    marginBottom: 20,
  },
  cardHeader: {
    color: '#E10600',
    fontSize: 11,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  cardTitle: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  cardSubtitle: {
    color: '#8F96A3',
    fontSize: 12,
    marginTop: 4,
  },
  sectionTitle: {
    color: '#8F96A3',
    fontSize: 12,
    fontWeight: 'bold',
    letterSpacing: 1,
    marginBottom: 10,
  },
  driverRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#15171E',
    borderBottomWidth: 1,
    borderBottomColor: '#272A35',
    paddingVertical: 12,
    paddingHorizontal: 12,
  },
  positionText: {
    color: '#FFF',
    fontWeight: 'bold',
    width: 32,
    fontSize: 14,
  },
  driverInfo: {
    flex: 1,
  },
  driverName: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 14,
  },
  teamName: {
    color: '#8F96A3',
    fontSize: 12,
  },
  pointsText: {
    color: '#FFF',
    fontWeight: 'bold',
    fontSize: 14,
    fontFamily: 'monospace',
  },
});
