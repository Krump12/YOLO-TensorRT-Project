# Data Model: Web Dashboard Authentication

## WebConfig

Represents Web-specific runtime settings loaded from configuration and
environment variables.

**Fields**:
- `host`: bind address, default `0.0.0.0`
- `port`: positive TCP port, default `8000`
- `username`: configured operator username, non-empty
- `password_env`: environment variable name containing the password, non-empty
- `session_secret_env`: environment variable name containing the session secret, non-empty
- `stream_fps`: target browser stream frame rate, positive, default `20`
- `jpeg_quality`: integer 1-100, default `80`

**Validation rules**:
- `password_env` must resolve to a non-empty environment value before Web
  service startup.
- `session_secret_env` must resolve to a non-empty environment value before
  session middleware is enabled.
- `stream_fps` must not exceed the configured camera FPS unless explicitly
  overridden later.

## AuthenticatedSession

Represents a browser login state.

**Fields**:
- `authenticated`: boolean
- `username`: configured username
- `created_at`: session creation timestamp

**State transitions**:
- `anonymous` -> `authenticated`: valid username/password submitted.
- `authenticated` -> `anonymous`: logout submitted or session removed.

**Validation rules**:
- Protected routes require `authenticated == true`.
- Failed login must not reveal whether username or password was incorrect.

## DetectionResultDTO

Represents one object detected in the latest frame.

**Fields**:
- `class_id`: integer class identifier
- `class_name`: display label
- `confidence`: float from 0.0 to 1.0
- `bbox`: bounding box object

**Validation rules**:
- `class_name` must be present, using `unknown:<id>` when the class mapping is
  unavailable.
- `confidence` must be serialized as a number and bounded to 0.0-1.0.
- `bbox` coordinates must be integers and clipped to frame bounds before
  rendering.

## BoundingBoxDTO

Represents pixel coordinates for a detection.

**Fields**:
- `x1`: left coordinate
- `y1`: top coordinate
- `x2`: right coordinate
- `y2`: bottom coordinate

**Validation rules**:
- Coordinates are integers in source frame pixel space.
- `x2 >= x1` and `y2 >= y1` after clipping.

## DetectionSnapshot

Represents the latest structured detection result returned to browsers.

**Fields**:
- `timestamp`: ISO-8601 timestamp for the source frame/result update
- `fps`: current processed frame rate
- `target_count`: number of detections in this snapshot
- `detections`: list of `DetectionResultDTO`

**Relationships**:
- Contains zero or more `DetectionResultDTO` records.
- Mirrors the same frame represented by the latest annotated image when
  available.

**State transitions**:
- `empty`: no frame processed yet or no detections.
- `ready`: latest frame processed and result data available.
- `error`: camera or detector failure prevents updates; exposed through status.

## FrameSnapshot

Represents the latest Web-deliverable annotated frame.

**Fields**:
- `timestamp`: source frame timestamp
- `frame_id`: source frame sequence number
- `jpeg_bytes`: encoded annotated image
- `fps`: current processed frame rate
- `target_count`: detection count

**Validation rules**:
- Encoded bytes are overwritten atomically; old frames are not queued
  indefinitely.
- JPEG quality follows `WebConfig.jpeg_quality`.

## RuntimeStatus

Represents system readiness and live metrics.

**Fields**:
- `camera_running`: boolean
- `detector_loaded`: boolean
- `fps`: current processed frame rate
- `target_count`: current target count
- `last_update`: ISO-8601 timestamp or null
- `error`: optional current error message

**Validation rules**:
- Status remains available after login even when camera or detector is not
  ready.
- Error messages are operational and must not include secrets.
