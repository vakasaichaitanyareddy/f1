# APEX GP — Production-Grade Formula 1 Intelligence & Racing Platform

APEX GP is a multi-platform Formula 1 intelligence platform combining live timing, historical race analysis, exact championship calculation engines, track performance analytics, historical race replay, and strategy simulation.

## Repository Layout
- `apps/web`: Next.js 15 responsive web application.
- `apps/mobile`: Expo / React Native mobile application.
- `services/api`: FastAPI production backend with SQLAlchemy, Redis, and domain engines.
- `packages/shared-types`: Canonical TypeScript interfaces.
- `packages/design-tokens`: Formula 1 team colors, tire compounds, status tokens.
- `packages/api-client`: Type-safe SDK.
- `docs/`: Master specifications, feature inventory, architecture, and verification runbooks.

## Local Quickstart with Docker
```bash
docker compose up -d
```
The API is available at `http://localhost:8000` (docs at `http://localhost:8000/docs`).
The Web app is available at `http://localhost:3000`.

## Architecture & Verification
Refer to [docs/architecture.md](docs/architecture.md) and [docs/feature-inventory.md](docs/feature-inventory.md) for master requirements and live tracking.
