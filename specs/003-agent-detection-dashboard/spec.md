# Feature Specification: Agent Detection Dashboard

**Feature Branch**: `004-agent-detection-dashboard`  
**Created**: 2026-05-11  
**Status**: Draft  
**Input**: User description: "Extend the existing YOLO TensorRT realtime detection web system with 48-hour target-only detection retention, Agent pest and disease analysis and Q&A, and Chinese/English language switching."

---

# User Scenarios & Testing *(mandatory)*

## User Story 1 - Retain Target Detection History (Priority: P1)

As an authenticated operator, I need the system to keep only detection results that contain targets for the most recent 48 hours, so I can review meaningful pest and disease evidence without sorting through empty frames.

### Why this priority

Detection history is the data foundation for review, Agent analysis, and Agent Q&A. Empty-frame storage would reduce usefulness and waste limited edge-device resources.

### Independent Test

Can be tested by feeding a mix of target and no-target detection results, then confirming that only target results appear in the 48-hour history with required details and filters.

### Acceptance Scenarios

1. **Given** realtime detection is running, **When** a frame contains one or more targets, **Then** each target detection is saved with detection time, class, confidence, bounding box, camera, device, frame or image reference, and creation time.

2. **Given** realtime detection is running, **When** a frame contains no targets, **Then** no detection history record is created for that frame.

3. **Given** target detections exist both inside and outside the last 48 hours, **When** the operator opens detection history, **Then** only detections from the latest 48 hours are shown by default in reverse chronological order.

4. **Given** the operator is viewing detection history, **When** they filter by class or confidence and open a row, **Then** the list and detail view reflect the selected criteria and show the selected detection details.

---

## User Story 2 - Analyze Pest and Disease Risk (Priority: P2)

As an authenticated operator, I need an Agent to analyze recent detection results and produce pest or disease risk findings, so I can understand severity and recommended actions from the last 48 hours of evidence.

### Why this priority

Analysis turns raw detections into actionable operational guidance, but it depends on reliable recent detection history.

### Independent Test

Can be tested by providing recent detections with known pest or disease patterns and verifying that the analysis result includes conclusion, pest or disease name, severity, evidence, recommendation, manual-review guidance, analysis time, and related detections.

### Acceptance Scenarios

1. **Given** recent target detections exist, **When** the operator starts analysis manually, **Then** the Agent produces and saves an analysis result linked to the relevant detections.

2. **Given** recent detections include high-risk pest or disease evidence, **When** the high-risk condition is recognized, **Then** analysis is triggered without blocking realtime inference or detection display.

3. **Given** scheduled analysis is enabled for recent data, **When** the scheduled time is reached, **Then** the Agent analyzes the selected recent period and saves the result.

4. **Given** analysis completes, **When** the operator opens the Agent analysis page, **Then** they can see severity, conclusion, evidence, recommendation, manual-review advice, and analysis time.

---

## User Story 3 - Ask Questions Grounded in Detection and Analysis Data (Priority: P2)

As an authenticated operator, I need to ask questions about recent detections and Agent analysis results, so I can decide whether to inspect manually, treat immediately, or keep observing.

### Why this priority

Q&A helps operators turn analysis records into decisions, but it must remain grounded in available evidence.

### Independent Test

Can be tested by asking questions about the last 48 hours and confirming that answers cite relevant detections and analyses, include uncertainty, and use the insufficient-data message when evidence is not enough.

### Acceptance Scenarios

1. **Given** recent detections and analyses exist, **When** the operator asks what pests or diseases appeared in the last 48 hours, **Then** the answer includes a conclusion, data basis, related detection records, related analysis results, recommendations, and uncertainty notes.

2. **Given** evidence is insufficient to answer confidently, **When** the operator asks for a diagnosis or treatment recommendation, **Then** the answer clearly states "当前检测数据不足，建议继续观察或人工复核。" in Chinese mode or the equivalent meaning in English mode.

3. **Given** the operator asks whether today is worse than yesterday, **When** enough time-based data exists, **Then** the answer compares the relevant periods using detection counts, frequency, severity, and confidence evidence.

---

## User Story 4 - Switch Interface Language (Priority: P3)

As an operator, I need to switch the web interface between Chinese and English, so I can use login, monitoring, history, Agent analysis, and Agent Q&A pages in my preferred language.

### Why this priority

Language support improves usability across operators, but it does not change the core detection and analysis workflow.

### Independent Test

Can be tested by switching language, refreshing the browser, and confirming all supported pages, controls, table fields, prompts, and errors remain in the selected language.

### Acceptance Scenarios

1. **Given** the operator is on any supported page, **When** they choose Chinese or English, **Then** visible page text changes immediately to the selected language.

2. **Given** the operator selected a language, **When** they refresh or revisit the page in the same browser, **Then** the previous language selection is preserved.

3. **Given** fixed system statuses or errors are shown, **When** the selected language changes, **Then** those statuses and errors are shown consistently in the selected language.

---

# Edge Cases

- If no target detections exist in the last 48 hours, detection history shows an empty state and Agent analysis/Q&A clearly reports insufficient data instead of inventing findings.

- If detections older than 48 hours still exist in storage, default history, analysis, and Q&A exclude them unless a later planning decision explicitly adds administrator-only maintenance views.

- If multiple targets are detected in one frame, each target is represented in history and can be linked to Agent evidence.

- If confidence filter settings exclude all detections, the history page shows an empty filtered result rather than an error.

- If the Agent cannot complete analysis, realtime detection and history retention continue, and the analysis page shows a recoverable failure state.

- If the user asks a question outside the available detection and analysis evidence, the Agent answers with uncertainty and limits its conclusion to available data.

- If translation text is missing for a visible label or status, the interface falls back to a clear default string rather than showing a raw key.

---

# Requirements *(mandatory)*

## Functional Requirements

- **FR-001**: The system MUST preserve the existing realtime camera reading, YOLO inference, login, and basic web monitoring behavior while adding the new capabilities.

- **FR-002**: The system MUST save detection history only when at least one target is detected.

- **FR-003**: The system MUST NOT create detection history records for frames with no detected targets.

- **FR-004**: Saved detection records MUST include a unique detection identifier, detection timestamp, class name, confidence, bounding box coordinates, camera identifier, device identifier, frame or image reference, and creation timestamp.

- **FR-005**: Recent detection history MUST default to the latest 48 hours and exclude older records from normal history, analysis, and Q&A views.

- **FR-006**: The system MUST automatically remove records older than 48 hours or reliably exclude them from all default recent-data experiences.

- **FR-007**: The detection history page MUST show recent target detections in reverse chronological order.

- **FR-008**: The detection history page MUST allow filtering by class and confidence.

- **FR-009**: The detection history page MUST allow viewing a single detection's details.

- **FR-010**: The system MUST provide Agent analysis based on recent detection results from the latest 48 hours.

- **FR-011**: Agent analysis input MUST consider pest or disease classes, detection counts, detection frequency, confidence, time distribution, and any available crop-stage or environment context.

- **FR-012**: Agent analysis output MUST include whether pest or disease evidence was found, pest or disease name when applicable, severity, rationale, recommended actions, manual-review advice, and analysis time.

- **FR-013**: Agent severity MUST use the levels light, moderate, and severe, displayed in the selected interface language.

- **FR-014**: Agent analysis results MUST be saved and associated with the detection records used as evidence.

- **FR-015**: Agent analysis MUST support manual start, high-risk automatic trigger, and scheduled recent-data analysis.

- **FR-016**: Agent analysis MUST NOT block realtime inference, realtime result display, or detection retention.

- **FR-017**: The Agent analysis page MUST show recent analysis results, severity, evidence, recommended treatment or handling measures, manual-review advice, and analysis time.

- **FR-018**: The system MUST provide an Agent Q&A page where authenticated users can ask about recent detections and saved analysis results.

- **FR-019**: Agent Q&A answers MUST be grounded in recent 48-hour detection records and saved Agent analysis results.

- **FR-020**: Agent Q&A answers MUST include a conclusion, data basis, related detection records, related analysis results, recommendations, and uncertainty notes when applicable.

- **FR-021**: If evidence is insufficient, Agent Q&A MUST clearly answer that current detection data is insufficient and continued observation or manual review is recommended.

- **FR-022**: Agent Q&A MUST save each question and answer with the user, evidence summary, related detection references, related analysis references, selected language, and creation time.

- **FR-023**: The web interface MUST offer Chinese and English language choices.

- **FR-024**: Language selection MUST affect login, realtime monitoring, detection history, Agent analysis, Agent Q&A, buttons, titles, table fields, prompts, errors, and fixed status text.

- **FR-025**: Switching language MUST update visible page text immediately.

- **FR-026**: The selected language MUST persist in the browser after page refresh.

- **FR-027**: Fixed backend or system statuses shown to users MUST be translatable or represented by stable status codes that the interface can translate.

- **FR-UX-001**: User-facing flows MUST define loading, empty, error, disabled, and success states where applicable.

- **FR-PERF-001**: Runtime-sensitive flows MUST preserve realtime inference continuity and make new analysis work observable as background progress rather than blocking monitoring.

---

# Key Entities *(include if feature involves data)*

## Detection Record

A target-containing inference result.

Key attributes include:

- detection identifier
- detected time
- class name
- confidence
- bounding box
- camera identifier
- device identifier
- frame or image reference
- creation time

---

## Agent Analysis Result

A saved assessment of recent detection evidence.

Key attributes include:

- analysis time
- analyzed time range
- pest or disease name
- severity
- conclusion
- evidence
- recommendation
- manual-review flag
- related detection references
- creation time

---

## Agent Chat Message

A saved user question and Agent answer grounded in recent detections and analysis results.

Key attributes include:

- user reference
- question
- answer
- evidence
- related detection references
- related analysis references
- language
- creation time

---

## Language Preference

The operator's selected interface language, either Chinese or English, persisted in the browser and applied across supported pages.

---

# Success Criteria *(mandatory)*

## Measurable Outcomes

- **SC-001**: In 100% of mixed-frame tests, frames without targets produce no detection history records.

- **SC-002**: In 100% of default history queries, detections older than 48 hours are absent and detections within the latest 48 hours are shown in reverse chronological order.

- **SC-003**: Operators can filter recent detection history by class and confidence and open a detection detail in under 30 seconds during usability validation.

- **SC-004**: Agent analysis produces pest or disease conclusion, severity, rationale, recommendation, manual-review advice, and analysis time for recent evidence in at least 95% of valid analysis requests.

- **SC-005**: Agent analysis starts and completes without interrupting realtime monitoring in 100% of validation runs.

- **SC-006**: Agent Q&A answers include conclusion, evidence basis, related records, recommendations, and uncertainty notes in at least 95% of answer evaluations where sufficient evidence exists.

- **SC-007**: Agent Q&A returns the insufficient-data response in 100% of evaluations where recent detections and analysis results do not support a conclusion.

- **SC-008**: Language switching updates visible text on all supported pages immediately and persists after refresh in 100% of browser persistence tests.

- **SC-UX-001**: Primary workflows remain usable at supported desktop and mobile viewport widths without overlapping text, controls, or tables.

- **SC-PERF-001**: New history, analysis, Q&A, and language features do not reduce the existing realtime monitoring target by more than 10% during normal single-operator validation.

---

# Assumptions

- Existing authentication remains the access control boundary for all new pages and actions.

- The feature targets the existing single-device, single-camera web dashboard scope unless later planning expands device management.

- "Recent" means a rolling 48-hour window measured from the current system time at query or analysis time.

- If multiple detections occur in the same frame, they may share the same frame or image reference while keeping separate detection identifiers.

- Crop growth stage and environment data are optional context; absence of this context must not prevent analysis based on detections alone.

- High-risk automatic analysis can use project-defined pest or disease class risk thresholds during planning.

- English insufficient-data answers should carry the same meaning as the required Chinese sentence.

- Interface language preference is browser-local and does not need to change the operator account profile for this feature.