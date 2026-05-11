# Research: Agent Detection Dashboard

## Decision: Use Local SQLite for Web Feature Persistence

**Rationale**: The existing edge runtime is a single Python application on one Jetson device and the previous Web dashboard plan had no database. This feature requires durable 48-hour detection history, saved analysis results, and saved chat messages, but does not require multi-node coordination. SQLite provides a small local database file, transactional writes, indexed recent queries, simple deployment, and straightforward pytest fixtures.

**Alternatives considered**:

- In-memory history only: rejected because analysis, history review, and chat evidence must survive page refresh and short process interruptions.
- Flat JSON/CSV files: rejected because filtering by time, class, confidence, and related record IDs becomes fragile and harder to test.
- External PostgreSQL/MySQL service: rejected for v1 because it increases deployment and operations cost on an edge device without a current multi-device requirement.

## Decision: Store Only Target Detections at the Pipeline Boundary

**Rationale**: The existing `WebDetectionPipeline` already receives structured `DetectionResult` values for each frame. Persisting only when the detection list is non-empty keeps the rule close to the data source while avoiding changes to camera capture or TensorRT inference. Multiple targets in one frame can be saved as separate detection records sharing the same frame ID.

**Alternatives considered**:

- Persist every frame and filter later: rejected because the specification explicitly excludes no-target frames and storage pressure matters on the edge device.
- Persist only aggregate counts: rejected because history detail, Agent evidence, and chat citations need per-detection details.

## Decision: Use Rolling 48-Hour Query Filters Plus Cleanup

**Rationale**: Default queries for history, analysis, and chat evidence must exclude older data. Query-level filtering guarantees correctness even if cleanup is delayed. Periodic cleanup reduces disk usage without making user-facing correctness depend on a scheduled task.

**Alternatives considered**:

- Cleanup only: rejected because missed cleanup could show stale data.
- Query filtering only: accepted as a correctness fallback but not enough for long-running edge deployments with limited disk.

## Decision: Bound Agent Work and Ground It in Evidence Packets

**Rationale**: Agent analysis and Q&A must not block realtime inference and must not invent answers. Building an evidence packet from recent detections and saved analyses before invoking analysis/chat logic makes grounding testable. Background execution with a small bounded queue keeps long analysis jobs from accumulating.

**Alternatives considered**:

- Run analysis synchronously inside request handlers: rejected because slow analysis would block user interactions and could compete with monitoring.
- Let chat answer directly from free-form prompts: rejected because it weakens evidence traceability and makes insufficient-data behavior hard to verify.

## Decision: Use Deterministic Risk Rules Around Agent Output

**Rationale**: The Agent should produce natural-language rationale and recommendations, but risk triggering and insufficient-data behavior need deterministic tests. Class risk configuration, count/frequency thresholds, and minimum confidence criteria should be evaluated before or alongside Agent output.

**Alternatives considered**:

- Fully model-driven risk detection: rejected because high-risk auto-trigger behavior would be difficult to validate reliably.
- Manual analysis only: rejected because the specification requires automatic high-risk and scheduled analysis modes.

## Decision: Frontend Translation Keys with Stable Backend Status Codes

**Rationale**: Most dashboard text lives in templates/static JavaScript. Keeping a browser-local language preference and translating frontend labels/status codes immediately supports refresh persistence and avoids duplicating full localized strings in every API response. Backend responses should expose stable status codes plus data values; fixed backend messages that are shown directly should have localized variants or be translated client-side.

**Alternatives considered**:

- Server-side language stored in account profile: rejected because the spec only requires browser-local persistence.
- Return localized strings only from backend: rejected because immediate language switching would require refetching too much page state.
