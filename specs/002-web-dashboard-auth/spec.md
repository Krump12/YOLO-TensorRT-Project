# Feature Specification: Web Dashboard Authentication

**Feature Branch**: `feature/web`  
**Created**: 2026-05-07  
**Status**: Draft  
**Input**: User description: "Add a login-protected Web visualization system to the existing YOLO TensorRT CSI camera detection project without rewriting the original runtime."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Secure Access to Detection System (Priority: P1)

An operator opens the detection system in a browser, signs in with configured credentials, and reaches the live detection workspace. Users who are not signed in cannot view video, detection data, or system status.

**Why this priority**: The detection pages expose live camera imagery and runtime data, so access control is required before any Web visualization is useful.

**Independent Test**: Can be tested by opening protected pages before and after login, verifying that valid credentials grant access and invalid or missing credentials do not.

**Acceptance Scenarios**:

1. **Given** an unauthenticated visitor, **When** they open the system root, **Then** they are directed to the login page.
2. **Given** a user enters the correct username and password, **When** they submit the login form, **Then** they are redirected to the live detection dashboard.
3. **Given** a user enters an incorrect password, **When** they submit the login form, **Then** access is denied and the login page shows a clear failure state.
4. **Given** an authenticated user, **When** they choose logout, **Then** their authenticated session ends and protected pages require login again.

---

### User Story 2 - Monitor Live Detection Video (Priority: P2)

An authenticated operator views a live camera stream in the browser with detection overlays, current FPS, and the number of objects in the latest frame.

**Why this priority**: The primary value of the feature is remote, browser-based monitoring of the existing real-time detection output.

**Independent Test**: Can be tested by using a mocked or real detection feed and verifying that the dashboard shows annotated video plus live metrics without opening a duplicate camera source.

**Acceptance Scenarios**:

1. **Given** an authenticated user and a running detection pipeline, **When** they open the dashboard, **Then** the page displays a live video feed with detection boxes, class names, and confidence values.
2. **Given** the latest frame has detected objects, **When** the dashboard updates, **Then** the displayed target count matches the latest detection result.
3. **Given** the runtime is producing frames at the supported input size, **When** the browser displays the stream, **Then** the UI remains responsive and shows a recent annotated frame.
4. **Given** the camera or detector is not ready, **When** the user opens the dashboard, **Then** the page shows a clear non-ready state instead of hanging silently.

---

### User Story 3 - Review Current Detection Results (Priority: P3)

An authenticated operator opens a detections page that refreshes automatically and lists the current detection results with class, confidence, bounding box, and timestamp.

**Why this priority**: Operators need a structured view of the latest detections in addition to the visual stream.

**Independent Test**: Can be tested with mocked detection results by verifying table updates, empty state behavior, and the presence of required fields.

**Acceptance Scenarios**:

1. **Given** the latest frame contains detections, **When** the detections page refreshes, **Then** each result shows class name, confidence, bounding box coordinates, and timestamp.
2. **Given** no objects are detected in the latest displayed frame, **When** the detections page refreshes, **Then** it shows an empty state that clearly indicates no current targets.
3. **Given** detections change over time, **When** the browser remains on the detections page, **Then** the displayed list updates automatically without a manual browser refresh.
4. **Given** the page displays latest-frame results, **When** the user views the detections table, **Then** the page clearly indicates that it represents the most recent available frame.

### Edge Cases

- Credentials are missing from configuration or environment at startup: the system refuses to start protected Web access and reports a clear setup error.
- An unauthenticated user directly opens any protected page or data feed: the request is denied or redirected to login.
- The camera is unavailable, already in use, or cannot deliver frames: protected pages remain accessible after login but show a clear camera error state.
- The detector model is unavailable or fails to load: status reports detector readiness as false and the dashboard avoids showing misleading live results.
- The latest frame has no detections: metrics show zero targets and the detections page shows an empty state.
- Browser clients disconnect while the runtime continues: the detection pipeline continues without accumulating unbounded pending frames.
- The system shuts down while clients are connected: camera and detection resources are released and clients stop receiving updates cleanly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a browser-accessible login page where users enter a username and password.
- **FR-002**: System MUST authenticate users against server-side configuration values, with the password supplied from a non-committed secret source.
- **FR-003**: System MUST prevent unauthenticated access to all live video, detection data, status data, and protected pages.
- **FR-004**: System MUST maintain a login state for authenticated users until logout or session expiry.
- **FR-005**: Users MUST be able to log out from protected pages.
- **FR-006**: System MUST provide a live dashboard page that displays an annotated camera stream, current FPS, and current target count.
- **FR-007**: The annotated stream MUST show detection boxes, class names, and confidence values when detections are present.
- **FR-008**: System MUST reuse the existing camera capture, detection, visualization, FPS, and target counting behavior rather than opening an independent duplicate camera or detection workflow for Web viewing.
- **FR-009**: System MUST keep camera capture, detection processing, and browser delivery decoupled so slow or disconnected clients do not block real-time detection.
- **FR-010**: System MUST keep only bounded, recent frame and result data for browser delivery to avoid unbounded memory growth or stale-frame buildup.
- **FR-011**: System MUST provide an automatically refreshing detections page showing the latest-frame result set.
- **FR-012**: Each displayed detection MUST include class name, confidence, bounding box coordinates, and timestamp.
- **FR-013**: System MUST show a clear empty state when the latest-frame result set contains no detections.
- **FR-014**: System MUST provide authenticated status information that includes camera running state, detector readiness, FPS, and target count.
- **FR-015**: System MUST support 1080P camera input while keeping the browser display low latency.
- **FR-016**: System MUST allow operators to configure Web host, port, username, stream frame rate, stream image quality, and session secret source without changing application code.
- **FR-017**: System MUST fail fast with a clear message when required secrets are absent.
- **FR-018**: System MUST shut down gracefully by stopping detection work and releasing camera resources.
- **FR-019**: Existing local detection and display workflows MUST remain available and behaviorally unchanged.
- **FR-UX-001**: User-facing flows MUST define loading, empty, error, disabled, and success states for login, dashboard video, status metrics, and detections.
- **FR-PERF-001**: Runtime-sensitive flows MUST validate that browser monitoring does not noticeably reduce the existing detection frame rate and supports at least 20 displayed frames per second under target hardware conditions.

### Key Entities

- **Authenticated Session**: Represents a signed-in browser user; key attributes are authenticated state, username, creation time, and logout state.
- **Detection Frame Snapshot**: Represents the most recent browser-deliverable frame; key attributes are timestamp, annotated image, FPS, target count, and readiness/error state.
- **Detection Result**: Represents one detected object in the latest frame; key attributes are class identifier, class name, confidence, bounding box coordinates, and timestamp.
- **Runtime Status**: Represents operational health for the Web dashboard; key attributes are camera running state, detector loaded state, FPS, target count, and last update time.
- **Web Configuration**: Represents operator-controlled Web settings; key attributes are host, port, username, password secret source, stream frame rate, image quality, and session secret source.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of protected pages and live data feeds deny access to unauthenticated users in automated route tests.
- **SC-002**: A valid user can sign in and reach the dashboard in under 5 seconds on the target device after the Web service is ready.
- **SC-003**: Invalid credentials fail without exposing live video, detection data, or password details.
- **SC-004**: The dashboard displays annotated live video, FPS, and target count with at least 20 displayed frames per second under normal target-device operation.
- **SC-005**: The detections page reflects the latest available frame within 1 second for at least 95% of updates during normal operation.
- **SC-006**: The structured detection result includes timestamp, FPS, target count, class name, confidence, and bounding box data in 100% of successful result responses.
- **SC-007**: A 30-minute monitoring session does not show unbounded memory growth caused by frame or result buffering.
- **SC-008**: Shutdown releases camera and detection resources within 3 seconds in normal operation.
- **SC-UX-001**: Login, dashboard, and detections pages remain usable at common desktop browser widths without overlapping text or controls.
- **SC-PERF-001**: Enabling one browser dashboard session reduces the existing detection frame rate by no more than 10% compared with the non-Web runtime under the same scene and device conditions.

## Assumptions

- The first release supports one configured operator account and does not require account self-service, password reset, roles, or a database.
- The browser displays the latest available annotated frame and latest-frame detection results, not a historical timeline, unless a later feature adds history.
- Web monitoring runs on the same Jetson device as the existing detection runtime and uses the same camera and model configuration.
- Browser clients are on a trusted local network unless deployment documentation states otherwise.
- Hardware-only validation for real CSI camera and accelerator behavior is marked separately from default tests.
