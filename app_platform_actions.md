# App Platform Actions — Detailed Reference

All 28 actions available in the EightfoldAI App Platform. Apps return actions inside their trigger
responses (in the `actions: List[AppActionSingleResponse]` field). Each action is identified by its
`action_name` string and executed server-side by the platform.

**Source:** `www/app_platform/actions/action_registry.py`, `www/app_platform/actions/action_base.py`

**Related files:** `app_platform_triggers.md`, `app_platform_trigger_schemas.md`

---

## How Actions Work

```
App Response
  └── actions: [
        { "action_name": "send_email", "action_data": { ... } },
        { "action_name": "save_assessment_to_profile_data", "action_data": { ... } }
      ]
```

The platform iterates `actions` after receiving the app response and executes each one in order.
Actions are validated against an allow-list per trigger type before execution.

---

## Category Index

1. [Data & Profile Management](#1-data--profile-management) — 11 actions
2. [Entity Operations](#2-entity-operations) — 2 actions
3. [Communication](#3-communication) — 4 actions
4. [Interview & Assessment](#4-interview--assessment) — 2 actions
5. [Media & Content](#5-media--content) — 4 actions
6. [Data Export](#6-data-export) — 1 action
7. [Administrative](#7-administrative) — 2 actions
8. [Utility](#8-utility) — 2 actions

---

## 1. Data & Profile Management

### `save_to_profile_data`
**Purpose:** Saves arbitrary JSON data to a candidate's profile under a specified namespace and subkey.

**Typical triggers:** `SCHEDULED_*`, `WEBHOOK_RECEIVE_EVENT`, `POST_ASSESSMENT_WEBHOOK`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `namespace` | Str | required | Data namespace key |
| `subkey_id` | Str | optional | Sub-identifier within namespace |
| `data` | Dict | required | JSON data to persist |

---

### `save_profile_app_data`
**Purpose:** Saves app-generated data to profile under the `APP_PROFILE_DATA` namespace with allowed-field validation.

**Typical triggers:** `CAREER_HUB_PROFILE_VIEW`, `TA_PROFILE_VIEW`, `SCHEDULED_*`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `app_id` | Str | required | App identifier (used as namespace key) |
| `data` | Dict | required | Data to save; validated against allowed fields |

---

### `save_profile_highlights`
**Purpose:** Saves profile highlights (summaries, key attributes) to the profile data store.

**Typical triggers:** `CAREER_HUB_PROFILE_VIEW`, `TA_PROFILE_VIEW`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `highlights` | List[Dict] | required | List of highlight objects |

---

### `save_assessment_to_profile_data`
**Purpose:** Stores assessment test results and vendor-specific data in a candidate's profile. Requires a prior assessment invitation.

**Typical triggers:** `ASSESSMENT_PROCESS_WEBHOOK`, `POST_ASSESSMENT_WEBHOOK`

**Feature gate:** None (always available)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `assessment_data` | Nested ApplicationAssessmentData | required | Full assessment result object |
| `app_id` | Str | required | App identifier |

---

### `save_practice_assessment_result_to_profile_data`
**Purpose:** Saves practice/unproctored assessment data to profile. Unlike `save_assessment_to_profile_data`, does not require a prior invitation record.

**Typical triggers:** `POST_ASSESSMENT_WEBHOOK`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `assessment_data` | Dict | required | Assessment result data |
| `app_id` | Str | required | App identifier |

---

### `save_interview_to_profile_data`
**Purpose:** Saves interview report, metadata, and activity display data to a candidate's profile after an interview session completes.

**Typical triggers:** `INTERVIEW_GENERATE_SESSION_URL` (callback), `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `interview_id` | Raw | required | Vendor interview session ID |
| `interview_report` | Dict | required | Interview result and metadata |
| `activity_display_data` | Nested InterviewActivityData | optional | Data for activity feed display |

---

### `save_app_data`
**Purpose:** Saves general app data to the `app_platform_apps_data` table (not profile-specific). Used for app-level state persistence.

**Typical triggers:** `SCHEDULED_*`, `POST_INSTALL`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `app_id` | Str | required | App identifier |
| `data_key` | Str | required | Storage key |
| `data` | Dict | required | Data to persist |

---

### `store_app_specific_data`
**Purpose:** Stores app-specific profile data namespaced by `app_id`. Similar to `save_profile_app_data` but with different namespace scoping and no field validation.

**Typical triggers:** `CAREER_HUB_PROFILE_VIEW`, `TA_PROFILE_VIEW`, `SCHEDULED_*`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Target candidate profile ID |
| `app_id` | Str | required | Namespace key |
| `data` | Dict | required | Data to persist |

---

### `store_employee_availability_data`
**Purpose:** Saves employee availability data for resource planning integrations (e.g., scheduling tools, workforce management apps).

**Typical triggers:** `SCHEDULED_*`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `employee_email` | Email | required | Target employee |
| `availability` | Dict | required | Availability schedule data |
| `effective_date` | Str | optional | ISO date string |

---

### `save_account_credentialed_data`
**Purpose:** Saves OAuth account credential data to the `user_auth_tokens` table. Used by apps that complete an OAuth flow on behalf of a user.

**Typical triggers:** `POST_INSTALL`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_email` | Email | required | User to associate credentials with |
| `app_id` | Str | required | App identifier |
| `access_token` | Str | required | OAuth access token |
| `refresh_token` | Str | optional | OAuth refresh token |
| `token_expiry` | Int | optional | Unix timestamp of token expiry |
| `extra_data` | Dict | optional | Additional credential metadata |

---

### `token_deauthorized`
**Purpose:** Marks an existing OAuth token as deauthorized and clears the stored access token. Used when a user revokes app access.

**Typical triggers:** `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_email` | Email | required | User whose token is being revoked |
| `app_id` | Str | required | App identifier |

---

## 2. Entity Operations

### `entity_update_action`
**Purpose:** Updates position or candidate entity fields — supports custom fields and ATS data updates.

**Typical triggers:** `POSITION_EXPORT`, `WEBHOOK_RECEIVE_EVENT`, `SCHEDULED_*`

**Feature gate:** `raise_exception_on_payrate_lookup_failure_gate` — when enabled, raises exception on payrate lookup failure instead of silently continuing.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | Str | required | `"position"` or `"candidate"` |
| `entity_id` | Int | required | ID of the entity to update |
| `fields` | Dict | required | Field name → value map to update |
| `ats_data` | Dict | optional | ATS-specific data to update |

---

### `ats_entity_create_update_action`
**Purpose:** Creates or updates ATS entities (positions or candidates) with full sync tracking. Preferred when the operation must be tracked for ATS reconciliation.

**Typical triggers:** `POSITION_EXPORT`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | Str | required | `"position"` or `"candidate"` |
| `entity_data` | Dict | required | Entity fields to create or update |
| `sync_id` | Str | optional | External sync identifier for tracking |
| `operation` | Str | optional | `"upsert"` (default), `"insert"`, `"update"` |

---

## 3. Communication

### `send_email`
**Purpose:** Sends a raw email with full control over sender, recipient, subject, body, and attachments.

**Typical triggers:** `SCHEDULED_*`, `ASSESSMENT_PROCESS_WEBHOOK`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `from_email` | Email | required | Sender email address |
| `to_email` | Email | required | Recipient email address |
| `subject` | Str | required | Email subject line |
| `body` | Str | required | Email body (HTML or plain text) |
| `cc` | List[Email] | optional | CC recipients |
| `bcc` | List[Email] | optional | BCC recipients |
| `attachments` | List[Dict] | optional | List of attachment objects |

---

### `send_email_with_template`
**Purpose:** Sends an email using a saved Eightfold email template with variable substitution.

**Typical triggers:** `SCHEDULED_*`, `ASSESSMENT_INVITE_CANDIDATE`, `ASSESSMENT_PROCESS_WEBHOOK`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | Str | required | ID of the saved email template |
| `to_email` | Email | required | Recipient email address |
| `variables` | Dict | optional | Template variable substitutions |
| `from_email` | Email | optional | Override sender address |

---

### `send_email_with_template_v2`
**Purpose:** Enhanced version of `send_email_with_template` with support for extra variables, dynamic attachments, and additional metadata.

**Typical triggers:** `SCHEDULED_*`, `ASSESSMENT_PROCESS_WEBHOOK`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `template_id` | Str | required | ID of the saved email template |
| `to_email` | Email | required | Recipient email address |
| `variables` | Dict | optional | Primary template variable substitutions |
| `extra_variables` | Dict | optional | Additional variables passed to template engine |
| `attachments` | List[Dict] | optional | Dynamic attachment objects |
| `from_email` | Email | optional | Override sender address |

---

### `add_user_message`
**Purpose:** Adds a message to the Eightfold user messaging system. Supports conversation threading and message metadata.

**Typical triggers:** `WEBHOOK_RECEIVE_EVENT`, `SCHEDULED_*`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `recipient_email` | Email | required | Message recipient |
| `message_body` | Str | required | Message content |
| `conversation_id` | Str | optional | Thread to attach the message to |
| `sender_name` | Str | optional | Display name for the sender |
| `metadata` | Dict | optional | Additional message metadata |

---

## 4. Interview & Assessment

### `schedule_interview_action`
**Purpose:** Schedules an interview for a candidate using an Eightfold scheduling template. Creates calendar invites and sends notifications.

**Typical triggers:** `ASSESSMENT_PROCESS_WEBHOOK`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Candidate profile ID |
| `position_id` | Int | required | Position/job ID |
| `scheduling_template_id` | Str | required | Eightfold scheduling template to use |
| `interviewers` | List[Email] | optional | Interviewer email addresses |
| `timeslot` | Nested TimeSlot | optional | Preferred time slot |
| `notes` | Str | optional | Additional scheduling notes |

---

### `assessment_auto_invite_candidate`
**Purpose:** Triggers automatic assessment invitation for a candidate. Fires the `ASSESSMENT_INVITE_CANDIDATE` trigger internally.

**Typical triggers:** `ASSESSMENT_PROCESS_WEBHOOK`, `SCHEDULED_*`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Candidate profile ID |
| `test_id` | Raw | required | Assessment test to invite candidate for |
| `application_id` | Str | optional | Associated application ID |
| `ats_job_id` | Int | optional | Associated ATS job ID |

---

## 5. Media & Content

### `handle_profile_video_creation`
**Purpose:** Processes profile video creation events. When the talent exchange approval gate is enabled, also auto-sets the profile approval status to `approved`.

**Typical triggers:** `WEBHOOK_RECEIVE_EVENT`

**Feature gate:** `etx_approval_status_gate` — when enabled, auto-updates profile approval status on video creation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Candidate profile ID |
| `video_url` | Str | required | URL of the created video |
| `video_metadata` | Dict | optional | Video duration, format, thumbnail, etc. |

---

### `handle_profile_video_flagging`
**Purpose:** Flags or manages profile videos. Sends notifications to exchange admins when a video is flagged.

**Typical triggers:** `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Candidate profile ID |
| `video_id` | Str | required | Video identifier to flag |
| `flag_reason` | Str | optional | Reason for flagging |
| `notify_admins` | Boolean | optional | Whether to send admin notifications (default: true) |

---

### `persist_content`
**Purpose:** Saves app-generated content (documents, files, reports) to S3. Accepts base64-encoded file content.

**Typical triggers:** `SCHEDULED_*`, `WEBHOOK_RECEIVE_EVENT`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `content_base64` | Str | required | Base64-encoded file content |
| `filename` | Str | required | Target filename |
| `content_type` | Str | required | MIME type (e.g., `application/pdf`) |
| `profile_id` | Int | optional | Associate content with a profile |
| `metadata` | Dict | optional | Additional content metadata |

---

### `download_to_pdf`
**Purpose:** Exports one or more candidate profiles to PDF. Supports optional field masking and resume inclusion.

**Typical triggers:** `POSITION_EXPORT`, `SCHEDULED_*`

**Feature gate:** `download_profiles_to_pdf_gate`
- **Gate ON:** Processes PDF asynchronously via queue; returns a secure download link
- **Gate OFF:** Processes PDF inline on-demand

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_ids` | List[Int] | required | List of candidate profile IDs to export |
| `include_resume` | Boolean | optional | Include original resume in PDF (default: false) |
| `mask_fields` | List[Str] | optional | Profile fields to redact/mask in output |
| `template_id` | Str | optional | PDF template to use |

---

## 6. Data Export

### `convert_data_to_csv`
**Purpose:** Converts data rows to CSV format and uploads the file to S3. Returns a download URL.

**Typical triggers:** `SCHEDULED_*`, `POSITION_EXPORT`

**Feature gate:** `extract_highlights_from_traits_for_csv_gate` — when enabled, extracts profile highlights from traits section when building the CSV row data.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `rows` | List[Dict] | required | Data rows to include in the CSV |
| `columns` | List[Str] | optional | Column headers (inferred from rows if omitted) |
| `filename` | Str | optional | Output filename |
| `include_highlights` | Boolean | optional | Extract highlights from traits (if gate enabled) |

---

## 7. Administrative

### `stage_advance`
**Purpose:** Placeholder action for advancing a candidate to the next pipeline stage. Currently a no-op; reserved for future implementation.

**Typical triggers:** `ASSESSMENT_PROCESS_WEBHOOK`, `WEBHOOK_RECEIVE_EVENT`

**Feature gate:** `app_platform_candidate_stage_advance_trigger_gate` — must be enabled for this action to be recognized.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `profile_id` | Int | required | Candidate profile ID |
| `position_id` | Int | required | Position ID |
| `target_stage` | Str | optional | Target stage name |

---

### `schedule_app_notification`
**Purpose:** Schedules an asynchronous app notification via the platform's notification queue. Used for delayed or batched notifications.

**Typical triggers:** `SCHEDULED_*`, `WEBHOOK_RECEIVE_EVENT`, `ASSESSMENT_PROCESS_WEBHOOK`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `notification_type` | Str | required | Notification type identifier |
| `recipient_email` | Email | required | Notification recipient |
| `payload` | Dict | required | Notification payload data |
| `delay_seconds` | Int | optional | Delay before sending (default: 0) |

---

## 8. Utility

### `open_url`
**Purpose:** Instructs the frontend to open a URL in a new browser tab, with an optional accompanying message.

**Typical triggers:** `CAREERHUB_APP_PLATFORM_CARD_CLICK`, `USER_APP_ACTION_EVENT`, `TA_PROFILE_VIEW`

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | Str | required | URL to open |
| `message` | Str | optional | Message to display alongside the URL open |
| `open_in_new_tab` | Boolean | optional | Whether to open in a new tab (default: true) |

---

### `echo`
**Purpose:** Test/diagnostic action. Echoes back the provided data for e2e testing of the action infrastructure. Has no side effects.

**Typical triggers:** Any trigger (dev/test use only)

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `data` | Dict | optional | Any data to echo back |

---

## Quick Reference: Action → Category → Gate

| Action | Category | Gate Required |
|--------|----------|--------------|
| `save_to_profile_data` | Data & Profile | — |
| `save_profile_app_data` | Data & Profile | — |
| `save_profile_highlights` | Data & Profile | — |
| `save_assessment_to_profile_data` | Data & Profile | — |
| `save_practice_assessment_result_to_profile_data` | Data & Profile | — |
| `save_interview_to_profile_data` | Data & Profile | — |
| `save_app_data` | Data & Profile | — |
| `store_app_specific_data` | Data & Profile | — |
| `store_employee_availability_data` | Data & Profile | — |
| `save_account_credentialed_data` | Data & Profile | — |
| `token_deauthorized` | Data & Profile | — |
| `entity_update_action` | Entity Operations | `raise_exception_on_payrate_lookup_failure_gate` (behavioral) |
| `ats_entity_create_update_action` | Entity Operations | — |
| `send_email` | Communication | — |
| `send_email_with_template` | Communication | — |
| `send_email_with_template_v2` | Communication | — |
| `add_user_message` | Communication | — |
| `schedule_interview_action` | Interview & Assessment | — |
| `assessment_auto_invite_candidate` | Interview & Assessment | — |
| `handle_profile_video_creation` | Media & Content | `etx_approval_status_gate` (behavioral) |
| `handle_profile_video_flagging` | Media & Content | — |
| `persist_content` | Media & Content | — |
| `download_to_pdf` | Media & Content | `download_profiles_to_pdf_gate` (behavioral) |
| `convert_data_to_csv` | Data Export | `extract_highlights_from_traits_for_csv_gate` (behavioral) |
| `stage_advance` | Administrative | `app_platform_candidate_stage_advance_trigger_gate` (required) |
| `schedule_app_notification` | Administrative | — |
| `open_url` | Utility | — |
| `echo` | Utility | — |

> **Gate types:**
> - **required** — gate must be ON for the action to function
> - **behavioral** — gate changes behavior (ON vs OFF has different outcomes but action works either way)

---

*Generated from EightfoldAI monorepo — `www/app_platform/actions/`. Date: 2026-03-25.*
