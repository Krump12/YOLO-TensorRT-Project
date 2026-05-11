# Data Model: Agent Detection Dashboard

## DetectionRecord

Represents one target detected by YOLO inference.

### Fields

- `id`: unique detection identifier
- `detected_at`: time the source frame was processed
- `class_name`: detected target class label
- `confidence`: normalized confidence score from 0.0 to 1.0
- `bbox_x1`, `bbox_y1`, `bbox_x2`, `bbox_y2`: bounding box coordinates
- `frame_id`: source frame identifier when available
- `image_id`: saved image reference when available
- `camera_id`: source camera identifier
- `device_id`: source edge device identifier
- `created_at`: record creation time

### Relationships

- Referenced by `AgentAnalysisResult.related_detection_ids`
- Referenced by `AgentChatMessage.related_detection_ids`

### Validation Rules

- Must be created only when at least one target exists in the source frame.
- `confidence` must be clamped or rejected outside the 0.0 to 1.0 range.
- Bounding box coordinates must preserve `x1 <= x2` and `y1 <= y2`.
- Default recent queries include only records where `detected_at` is within the rolling latest 48 hours.

## AgentAnalysisResult

Represents a saved Agent assessment over recent detection evidence.

### Fields

- `id`: unique analysis identifier
- `analysis_time`: time the analysis completed
- `time_range_start`: evidence window start
- `time_range_end`: evidence window end
- `pest_or_disease_name`: identified pest or disease name, when found
- `severity`: `light`, `moderate`, or `severe`
- `conclusion`: concise result of the analysis
- `evidence`: structured evidence summary including counts, frequency, confidence, and time distribution
- `recommendation`: suggested handling or treatment measures
- `need_manual_review`: whether manual review is recommended
- `related_detection_ids`: detection records used as evidence
- `trigger_type`: `manual`, `high_risk`, or `scheduled`
- `status`: `pending`, `running`, `completed`, or `failed`
- `error`: failure message or code when analysis fails
- `created_at`: record creation time

### Relationships

- Many-to-many logical relationship with `DetectionRecord` through `related_detection_ids`
- Referenced by `AgentChatMessage.related_analysis_ids`

### Validation Rules

- Evidence window must not exceed the latest 48-hour default scope for normal analysis.
- Completed results must include conclusion, evidence, recommendation, manual-review flag, and analysis time.
- Failed results must not block realtime detection or history retention.

## AgentChatMessage

Represents one grounded user question and Agent answer.

### Fields

- `id`: unique chat message identifier
- `user_id`: authenticated user identifier
- `question`: user question
- `answer`: Agent answer
- `evidence`: evidence summary used to answer
- `related_detection_ids`: detection records cited by the answer
- `related_analysis_ids`: analysis results cited by the answer
- `language`: `zh` or `en`
- `created_at`: message creation time

### Relationships

- References zero or more `DetectionRecord` entries.
- References zero or more `AgentAnalysisResult` entries.

### Validation Rules

- Answers must be generated from the latest 48-hour detections and saved analysis results.
- If evidence is insufficient, answer must use the required insufficient-data conclusion in the selected language.
- Saved language must reflect the UI language at question time.

## LanguagePreference

Represents the browser-local interface language selection.

### Fields

- `language`: `zh` or `en`
- `updated_at`: last browser-side update time

### Validation Rules

- Unsupported language codes fall back to the project default language.
- Visible labels, prompts, table fields, fixed statuses, and errors use translation keys or translated strings.
