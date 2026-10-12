# APEX GP — System Architecture & Technical Specifications

## 1. System Overview
APEX GP is an enterprise-grade Formula 1 intelligence and live telemetry analytics platform built using a clean, scalable monorepo architecture.

```
                      +---------------------------------------+
                      |               Clients                 |
                      |   [Next.js 15 Web]   [Expo / React-Native]|
                      +-------------------+-------------------+
                                          |
                                    HTTPS / WSS
                                          |
                      +-------------------v-------------------+
                      |             FastAPI Gateway           |
                      |    (Auth, OpenAPI, Rate-Limiter)      |
                      +---------+-------------------+---------+
                                |                   |
             +------------------v--+             +--v------------------+
             | Domain Services     |             | Realtime Hub (WS)   |
             | - Racing & Results  |             | - Live Timing Tower |
             | - Championship Math |             | - Race Control Feed |
             | - Circuit Analytics |             | - Telemetry Sync    |
             | - Strategy Engine   |             +----------+----------+
             | - Replay Engine     |                        |
             +----------+----------+                        |
                        |                                   |
         +--------------+---------------+                   |
         |                              |                   |
+--------v---------+          +---------v--------+          |
| PostgreSQL 16    |          | Redis 7          |<---------+
| (Durable Racing, |          | (Pub/Sub,        |
|  Users, Scenarios|          |  Live Caches,    |
|  Telemetry logs) |          |  Session Store)  |
+------------------+          +------------------+
```

## 2. Monorepo Organization
- `apps/web`: Next.js App router, Tailwind CSS, Lucide icons, ECharts / Recharts.
- `apps/mobile`: Expo / React Native with NativeWind.
- `services/api`: FastAPI application organized in clean domain-driven architecture.
- `packages/shared-types`: Canonical TypeScript interfaces mirror Pydantic domain models.
- `packages/design-tokens`: Formula 1 motorsport color tokens, team palettes, tire compound tokens.
- `packages/api-client`: Type-safe SDK for web and mobile.

## 3. Data Integrity & Provenance Rules
1. **Never Fabricate Data**: Live indicators must say `LIVE`, `DELAYED`, `STALE`, `HISTORICAL`, or `UNAVAILABLE`.
2. **Provenance Stamps**: Every data record carries `source`, `retrieved_at`, and `verified` flags.
3. **No Blind Fallbacks**: If live timing has missing sectors, display `N/A` rather than interpolated guesses, unless explicitly labelled as `reconstructed`.
4. **Pure Mathematical Engines**: Championship clinching and elimination engines operate purely on verified point systems (25-18-15..., sprint 8-7-6..., fastest lap rules) and FIA countback tie-break protocols.

## 4. Security & Compliance
- Passwords hashed using bcrypt / Argon2.
- Session tokens use standard JWT signed with high-entropy secret.
- No third-party provider tokens are bundled in client applications.
- Sensitive user preferences (e.g. spoiler shield, custom pit wall configurations) stored securely per tenant.
