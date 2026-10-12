# APEX GP Release Notes — v1.1.1 (Targeted Correctness Patch)

## Summary of Changes
Release v1.1.1 applies focused regulatory correctness, security validation, and documentation updates while preserving the v1.1.0 baseline.

### 1. Fastest-Lap & Race Distance Regulatory Interaction (Article 6.4 & 6.5)
- **Precise Distance Boundary Handling**:
  - Below 50% distance (< 0.50): Fastest-lap bonus is strictly ineligible (Columns 1 & 2 of Article 6.5).
  - Exactly 50% distance (0.50): Leader has completed >= 50% of the scheduled race distance. The fastest-lap bonus applies if the driver finishes in the top 10 (Column 3 of Article 6.5: 19 base + 1 FL = 20 pts).
  - Between 50% and 75% distance: Corrected rule logic to ensure fastest-lap bonus is **not** suppressed across the 50%–<75% band when top-10 finishers achieve the fastest lap.
- **2025 Onward Regulation Amendment**:
  - As ratified by the FIA World Motor Sport Council (WMSC) on October 17, 2024, the fastest-lap bonus point is formally rescinded beginning in the 2025 season.
  - In 2025 onward, maximum points per Grand Prix are capped at 25 points (win) + 0 points (FL), with `is_fastest_lap_eligible()` returning `False` under all race conditions.
- **Historical Season Rules Preserved**:
  - Pre-2019 modern seasons (2010–2018) and historical eras (2003–2009, 1991–2002) correctly award 0 bonus points for fastest laps.

### 2. Password Validation & Security Hardening
- **No Silent Truncation**:
  - Removed silent `[:72]` byte truncation in `get_password_hash()`.
  - Added strict Pydantic field validators on `UserCreate` and `UserLogin` schemas.
  - Passwords exceeding 72 bytes (whether in ASCII or multi-byte UTF-8, such as emoji/special characters) are explicitly rejected with HTTP 422 and a clear validation error.
  - Passwords under 8 bytes are rejected with a clear validation error.
  - Multi-byte UTF-8 passwords within the 72-byte limit are verified to hash and authenticate consistently.

### 3. Regulation-Source Metadata Registry
- Introduced `REGULATION_PROVENANCE_REGISTRY` in `app.championship.engine` documenting:
  - **2025+**: FIA Formula One Sporting Regulations (2025 Issue 1; WMSC Oct 2024), Article 6.4 & 6.5.
  - **2022–2024**: Post-Spa 2021 graduated scale overhaul, Article 6.4 & 6.5.
  - **2019–2021**: Fastest lap re-introduction (March 2019 WMSC), Article 6.4.
  - **2010–2018**: 25-18-15 scale introduction.
  - **2003–2009**: 10-8-6-5-4-3-2-1 scale.
  - **1991–2002**: 10-6-4-3-2-1 scale.

### 4. Integration Verification Results
- **Full Backend Pytest Suite**: 22 passed in 1.67s (0 errors, 0 warnings).
- **Web Production Build**: Next.js 15 compiled successfully (`npm run build`).
- **Mobile TypeScript Verification**: Clean compilation (`tsc --project apps/mobile/tsconfig.json --noEmit`).
- **Database & Application Lifespan**: Clean in-process startup and seeding verified.
- **Docker Daemon Limitation**: Docker Desktop Windows engine (`//./pipe/dockerDesktopLinuxEngine`) was stopped on the host environment; Compose configuration syntax was validated via `docker compose config`.
