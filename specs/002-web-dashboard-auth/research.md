# Phase 0 Research: Web Dashboard Authentication

## Decision: FastAPI with Starlette sessions and templates

**Rationale**: The project is already Python-based and needs a small Web layer
with form login, authenticated pages, JSON endpoints, and streaming responses.
FastAPI provides these with low ceremony, supports pytest/TestClient route
tests, and does not require a separate frontend build system.

**Alternatives considered**:
- Flask: simple, but less direct schema integration for the JSON contracts.
- Django: too large for a single-device edge dashboard without a database.
- Raw ASGI/Starlette only: viable, but FastAPI improves route structure and
  schema testing with little extra complexity.

## Decision: MJPEG for annotated video stream

**Rationale**: MJPEG is supported by normal browser image elements, keeps the
dashboard frontend simple, and is enough for a low-latency latest-frame 1080P
monitoring view. JPEG quality and target stream FPS will be configurable to
balance CPU load, bandwidth, and frame rate on Jetson Orin Nano.

**Alternatives considered**:
- WebSocket binary frames: lower protocol overhead for some clients, but more
  frontend code and backpressure handling.
- WebRTC: better for complex low-latency video, but too heavy for v1 and not
  needed for a local monitoring dashboard.
- Server-Sent Events: suitable for structured events, not binary video.

## Decision: Poll latest JSON for status and detections

**Rationale**: The feature displays the latest frame's current result set, not a
history stream. Polling `/api/status` and `/api/detections/latest` every
500-1000 ms is easy to test, resilient to reconnects, and avoids per-client
queues. It satisfies the 1 second freshness target without adding WebSocket
state management.

**Alternatives considered**:
- WebSocket updates: useful for high-frequency bidirectional updates, but not
  necessary for latest-frame table refresh.
- SSE: simple one-way streaming, but still adds connection lifecycle handling
  with little benefit over polling for this scope.

## Decision: Single shared background detection pipeline

**Rationale**: The existing project already separates camera capture from
inference via `LatestFrameReader` and has reusable TensorRT detection and
overlay utilities. The Web service should start one background pipeline that
opens the CSI camera once, runs inference once per processed frame, renders the
overlay once, and publishes latest annotated frame/result/status snapshots.

**Alternatives considered**:
- Open a second camera stream for Web: rejected because CSI camera resources
  can conflict and it violates the requirement to avoid duplicate pipelines.
- Reimplement inference in Web routes: rejected because it duplicates tested
  runtime behavior and would block browser requests on inference.

## Decision: Lock-protected latest-state buffer

**Rationale**: Browser clients only need the most recent annotated frame and
latest detection result. A small state object protected by a lock avoids
unbounded queues, stale frame buildup, and cross-thread mutation hazards. The
pipeline can drop older frames through existing bounded capture behavior and
overwrite latest Web snapshots atomically.

**Alternatives considered**:
- Per-client queues: rejected because disconnected or slow clients can create
  memory growth.
- Global module variables without a lifecycle object: rejected because startup,
  tests, and shutdown need explicit ownership.

## Decision: Environment-backed secrets

**Rationale**: The first release needs one configured operator account without a
database. Keeping username and environment variable names in YAML while reading
password and session secret from environment variables prevents committing real
secrets and gives clear startup validation.

**Alternatives considered**:
- Hardcoded frontend password: rejected because it exposes credentials.
- Local database: unnecessary for one operator account in v1.
- Password file committed to the repository: rejected because it risks secret
  leakage.

## Decision: Mock-based default Web tests plus Jetson-marked hardware tests

**Rationale**: Default CI and development machines should validate Web
authentication, route protection, schemas, and pipeline integration without
opening a real CSI camera or loading TensorRT. Hardware validation remains
important and should use the repository's existing `--run-jetson` pattern.

**Alternatives considered**:
- Require CSI/TensorRT for all Web tests: rejected because it would make default
  tests impractical off-device.
- Skip pipeline tests entirely: rejected because Web delivery depends on
  cross-module pipeline behavior.
