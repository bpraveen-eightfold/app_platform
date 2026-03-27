# App Platform Trigger Schemas — Request & Response Types

Full field-level schema reference for all 29 App Platform triggers in the EightfoldAI platform.
Intended for MCP/AI context ingestion alongside `app_platform_triggers.md`.

**Source files:**
- `www/app_platform/core/app_platform_trigger_definitions.py`
- `www/app_platform/core/request_data_classes.py`
- `www/app_platform/core/response_data_classes.py`
- `www/app_platform/actions/action_response_data_classes.py`

---

## Shared / Reused Types

These types appear across multiple triggers. Defined once here; referenced by name below.

### ProfileRequestType
Used by: `CAREER_HUB_HOME_SIDEBAR_VIEW`, `CAREER_HUB_PROFILE_VIEW`, `CH_PROFILE_VIEW_MAIN_CONTENT`, `CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND`, `TA_PROFILE_VIEW`

| Field | Type | Required |
|-------|------|----------|
| `email` | Email | optional |
| `all_emails` | List[Email] | optional |
| `employee_email` | Email | optional |
| `fullname` | Str | optional |
| `firstname` | Str | optional |
| `lastname` | Str | optional |
| `title` | Str | optional |
| `skills` | List[Str] | optional |
| `image_url` | Url | optional |
| `location` | Str | optional |
| `location_country_code` | Str | optional |
| `profile_url` | Url | optional |
| `business_unit` | Str | optional |
| `current_user_email` | Email | optional |
| `profile_data` | Dict | optional |
| `profile_urls` | List[Url] | optional |
| `custom_fields` | Dict | optional |
| `manager_profile` | Nested ProfileRequestType | optional |
| `current_user_profile` | Nested ProfileRequestType | optional |

### ProfileViewResponseType
Used by: `CAREER_HUB_HOME_SIDEBAR_VIEW`, `CAREER_HUB_PROFILE_VIEW`, `CH_PROFILE_VIEW_MAIN_CONTENT`, `CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND`, `TA_PROFILE_VIEW`, `SMARTAPPLY_JOB_PAGE_VIEW`

| Field | Type | Required |
|-------|------|----------|
| `html` | Str | optional |
| `template` | Str | optional |
| `data` | Nested ProfileTemplateData | optional |

**ProfileTemplateData fields:**

| Field | Type | Required |
|-------|------|----------|
| `logo_url` | Str | optional |
| `title` | Str | optional |
| `subtitle` | Str | optional |
| `error` | Str | optional |
| `tiles` | List[Tile] | optional |
| `table` | Nested Table | optional |
| `footer` | Str | optional |

### AppActionResponseType
Used by: `POSITION_EXPORT`, `POST_ASSESSMENT_WEBHOOK`, `SCHEDULED_DAILY`, `SCHEDULED_HOURLY`, `SCHEDULED_WEEKLY`, `USER_APP_ACTION_EVENT`

| Field | Type | Required |
|-------|------|----------|
| `actions` | List[AppActionSingleResponse] | optional |

**AppActionSingleResponse fields:**

| Field | Type | Required |
|-------|------|----------|
| `action_name` | Str | required |
| `action_data` | Dict | optional |

### ApplicationAssessmentData
Used as response in: `ASSESSMENT_FETCH_CANDIDATE_REPORT`; nested in: `ASSESSMENT_PROCESS_WEBHOOK`

| Field | Type | Required |
|-------|------|----------|
| `assessment_id` | Raw | optional |
| `test_id` | Raw | **required** |
| `email` | Email | optional |
| `status` | Str | **required** |
| `vendor_report_status` | Str | optional |
| `assigned_ts` | Int | optional |
| `start_ts` | Int | optional |
| `completed_ts` | Int | optional |
| `num_tests_completed` | Int | optional |
| `num_tests_total` | Int | optional |
| `score` | Raw | optional |
| `score_unit` | Str | optional |
| `rating` | Raw | optional |
| `comments` | Str | optional |
| `plagiarism_status` | Raw | optional |
| `report_url` | Str | optional |
| `last_modified_ts` | Int | optional |
| `response_json` | Raw | **required** |
| `vendor_status` | Str | optional |
| `estimated_completion_time` | Int | optional |

### AssessmentInviteMetadata
Used in: `ASSESSMENT_INVITE_CANDIDATE` (request), `ASSESSMENT_PROCESS_WEBHOOK` (response)

| Field | Type | Required |
|-------|------|----------|
| `email` | Email | optional |
| `profile_id` | Int | optional |
| `profile_enc_id` | Str | optional |
| `pid` | Int | optional |
| `application_id` | Str | optional |
| `ats_job_id` | Int | optional |
| `ats_job_id_raw` | Str | optional |
| `ats_candidate_id` | Raw | optional |
| `test_id` | Raw | optional |
| `custom_form_fields` | Dict | optional |

### CareerhubEntityDetailsResponseType
Used as list item in: `CAREERHUB_ENTITY_SEARCH_RESULTS`; standalone in: `CAREERHUB_GET_ENTITY_DETAILS`

| Field | Type | Required |
|-------|------|----------|
| `entity_id` | Raw | **required** |
| `title` | Str | optional |
| `subtitle` | Str | optional |
| `description` | Str | optional |
| `source_name` | Str | optional |
| `image_url` | Str | optional |
| `cta_label` | Str | optional |
| `cta_url` | Str | optional |
| `card_label` | Str | optional |
| `last_modified_ts` | Int | optional |
| `metadata` | List[AppPlatformEntityField] | optional |
| `tags` | List[Str] | optional |
| `custom_sections` | List[AppPlatformEntityCustomSection] | optional |
| `fields` | List[AppPlatformEntityField] | optional |

---

## Trigger Schemas

---

### 1. ASSESSMENT_FETCH_CANDIDATE_REPORT
**Category:** Assessment

**Request: `AssessmentFetchCandidateReportRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `assessment_id` | Raw | optional |
| `test_id` | Raw | optional |
| `vendor_candidate_id` | Raw | optional |
| `action_user_email` | Email | optional |
| `email` | Email | optional |
| `trigger_name` | Str | optional |

**Response: `ApplicationAssessmentData`** — see Shared Types above.

---

### 2. ASSESSMENT_GET_LOGO_URL
**Category:** Assessment

**Request: `AssessmentGetLogoUrlRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |

**Response: `AssessmentGetLogoUrlResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `logo_url` | Str | **required** |

---

### 3. ASSESSMENT_INVITE_CANDIDATE
**Category:** Assessment

**Request: `AssessmentInviteCandidateRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `test_id` | Raw | optional |
| `invite_metadata` | Nested AssessmentInviteMetadata | optional |
| `action_user_email` | Email | optional |
| `notification_url` | Url | optional |
| `firstname` | Str | optional |
| `lastname` | Str | optional |
| `fullname` | Str | optional |
| `location` | Str | optional |
| `location_country` | Str | optional |
| `location_state` | Str | optional |
| `trigger_name` | Str | optional |

**Response: `AssessmentInviteCandidateResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `actions` | List[AppActionSingleResponse] | optional |
| `email` | Email | optional |
| `vendor_candidate_id` | Raw | optional |
| `test_url` | Url | optional |
| `invite_already_sent` | Boolean | optional |
| `assessment_id` | Raw | optional |

---

### 4. ASSESSMENT_IS_WEBHOOK_SUPPORTED
**Category:** Assessment

**Request: `AssessmentIsWebhookSupportedRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |

**Response: `AssessmentIsWebhookSupportedResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `is_webhook_supported` | Boolean | **required** |

---

### 5. ASSESSMENT_LIST_TESTS
**Category:** Assessment

**Request: `AssessmentListTestsRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `action_user_email` | Email | optional |
| `position_context` | Dict | optional |
| `trigger_name` | Str | optional |

**Response: List[`AssessmentTestType`]**

| Field | Type | Required |
|-------|------|----------|
| `id` | Raw | **required** |
| `name` | Str | **required** |
| `duration_minutes` | Int | optional |
| `published` | Boolean | optional |

---

### 6. ASSESSMENT_PROCESS_WEBHOOK
**Category:** Assessment

**Request: `AssessmentProcessWebhookRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `headers` | Dict | optional |
| `request_payload` | Dict | optional |
| `trigger_name` | Str | optional |

**Response: `AssessmentProcessWebhookResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `invite_metadata` | Nested InviteMetadataResponseType | optional |
| `assessment_report` | Nested ApplicationAssessmentData | optional |

**InviteMetadataResponseType fields:**

| Field | Type | Required |
|-------|------|----------|
| `email` | Email | **required** |
| `profile_id` | Int | **required** |
| `profile_enc_id` | Str | optional |
| `pid` | Int | **required** |
| `application_id` | Str | optional |
| `ats_job_id` | Int | optional |
| `ats_candidate_id` | Raw | optional |
| `test_id` | Raw | **required** |

---

### 7. CAREER_HUB_HOME_SIDEBAR_VIEW
**Category:** CareerHub UI

**Request:** `ProfileRequestType` — see Shared Types above.

**Response:** `ProfileViewResponseType` — see Shared Types above.

---

### 8. CAREER_HUB_PROFILE_VIEW
**Category:** CareerHub UI

**Request:** `ProfileRequestType` — see Shared Types above.

**Response:** `ProfileViewResponseType` — see Shared Types above.

---

### 9. CAREER_PLANNER_RECOMMENDED_COURSES
**Category:** CareerHub

**Request: `CareerhubEntitySearchResultsRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `current_user_email` | Email | optional |
| `term` | Str | optional |
| `fq` | Nested FieldQuery | optional |
| `facet_fields` | Raw | optional |
| `start` | Int | optional |
| `limit` | Int | optional |
| `cursor` | Raw | optional |
| `page_size` | Int | optional |
| `sort_by` | Raw | optional |
| `trigger_name` | Str | optional |
| `locale` | Str | optional |
| `filters` | Dict | optional |
| `trigger_source` | Str | optional |

**Response: List[`CareerhubRecommendedCourseResponseType`]**

| Field | Type | Required |
|-------|------|----------|
| `group_id` | Str | optional |
| `lms_course_id` | Raw | optional |
| `title` | Str | optional |
| `description` | Str | optional |
| `course_type` | Str | optional |
| `language` | Str | optional |
| `difficulty` | Str | optional |
| `duration_hours` | Float | optional |
| `published_date` | Raw | optional |
| `course_url` | Str | optional |
| `status` | Str | optional |
| `category` | Str | optional |
| `image_url` | Str | optional |
| `provider` | Str | optional |
| `skills` | List[Str] | optional |
| `lms_data` | Dict | optional |

---

### 10. CAREERHUB_APP_PLATFORM_CARD_CLICK
**Category:** CareerHub

**Request: `CareerhubAppPlatformCardClickRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `current_user_email` | Email | optional |
| `entity_id` | Str | optional |
| `profile_id` | Int | optional |

**Response: `CareerhubAppPlatformCardClickResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `redirect_url` | Str | optional |

---

### 11. CAREERHUB_ENTITY_SEARCH_RESULTS
**Category:** CareerHub

**Request:** `CareerhubEntitySearchResultsRequestType` — see trigger #9 above.

**Response: `CareerhubEntitySearchResultsResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `num_results` | Int | **required** |
| `entities` | List[CareerhubEntityDetailsResponseType] | **required** |
| `offset` | Int | optional |
| `limit` | Int | optional |
| `cursor` | Raw | optional |

---

### 12. CAREERHUB_GET_ENTITY_DETAILS
**Category:** CareerHub

**Request: `CareerhubEntityDetailsRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `entity_id` | Str | optional |
| `current_user_email` | Email | optional |
| `trigger_name` | Str | optional |
| `locale` | Str | optional |

**Response:** `CareerhubEntityDetailsResponseType` — see Shared Types above.

---

### 13. CAREERHUB_PROFILE_COURSE_ATTENDANCE
**Category:** CareerHub

**Request: `ProfileCourseAttendanceRequestType`** *(extends ProfileRequestType)*

Inherits all fields from `ProfileRequestType`, plus:

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |

**Response: List[`ProfileCourseAttendanceResponseType`]**

| Field | Type | Required |
|-------|------|----------|
| `group_id` | Str | optional |
| `title` | Str | optional |
| `description` | Str | optional |
| `course_type` | Str | optional |
| `language` | Str | optional |
| `difficulty` | Str | optional |
| `start_date` | Int | optional |
| `completion_date` | Int | optional |
| `course_url` | Str | optional |
| `provider` | Str | optional |
| `is_internal` | Boolean | optional |
| `status` | Str | optional |
| `points_earned` | Float | optional |
| `verified` | Raw | optional |
| `medium` | Str | optional |
| `data_json` | Dict | optional |

---

### 14. CAREERHUB_STATIC_ENTITY
**Category:** CareerHub

**Request: `CareerhubStaticEntityRequestType`**

*(No fields — empty request)*

**Response: `CareerhubStaticEntityResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `app_html` | Str | optional |
| `app_url` | Str | optional |

---

### 15. CH_PROFILE_VIEW_MAIN_CONTENT
**Category:** CareerHub UI

**Request:** `ProfileRequestType` — see Shared Types above.

**Response:** `ProfileViewResponseType` — see Shared Types above.

---

### 16. CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND
**Category:** CareerHub UI

**Request:** `ProfileRequestType` — see Shared Types above.

**Response:** `ProfileViewResponseType` — see Shared Types above.

---

### 17. INTERVIEW_GENERATE_SESSION_URL
**Category:** Interview

**Request: `InterviewGenerateSessionUrlRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `action_user_email` | Email | optional |
| `notification_url` | Url | optional |
| `interview_metadata` | Nested InterviewMetadata | optional |

**InterviewMetadata fields:**

| Field | Type | Required |
|-------|------|----------|
| `email` | Email | optional |
| `profile_id` | Int | optional |
| `profile_enc_id` | Str | optional |
| `pid` | Int | optional |
| `application_id` | Str | optional |
| `ats_job_id` | Int | optional |
| `ats_candidate_id` | Raw | optional |
| `interview_title` | Str | optional |

**Response: `InterviewGenerateSessionUrlResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `session_url` | Str | **required** |
| `interview_id` | Raw | **required** |
| `activity_display_data` | Nested InterviewActivityData | optional |

**InterviewActivityData fields:**

| Field | Type | Required |
|-------|------|----------|
| `note_type` | Str | optional |
| `logo_url` | Str | optional |
| `creation_ts` | Int | optional |
| `summary` | Str | optional |
| `completion_data` | List[CompletionDataItem] | optional |

---

### 18. INTERVIEW_ASSESSMENT_SCHEDULED
**Category:** Interview

**Request: `InterviewAssessmentScheduledRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `ats_job_id` | Int | optional |
| `position_id` | Int | optional |
| `requisition_name` | Str | optional |
| `interview_id` | Str | optional |
| `timeslot` | Nested TimeSlot | optional |
| `interviewers` | List[InterviewParticipant] | optional |
| `candidates` | List[InterviewParticipant] | optional |

**TimeSlot fields:**

| Field | Type | Required |
|-------|------|----------|
| `start_time` | Str | optional |
| `end_time` | Str | optional |

**InterviewParticipant fields:**

| Field | Type | Required |
|-------|------|----------|
| `first_name` | Str | optional |
| `last_name` | Str | optional |
| `email` | Str | optional |
| `optional` | Boolean | optional |

**Response: `InterviewAssessmentScheduledResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `status_code` | Int | optional |
| `ats_job_id` | Int | optional |
| `position_id` | Int | optional |
| `interview_id` | Str | optional |
| `timeslot` | Nested TimeSlot | optional |
| `interviewers` | List[InterviewParticipant] | optional |
| `candidates` | List[InterviewParticipant] | optional |

---

### 19. INTERVIEW_ASSESSMENT_SCHEDULE_CANCEL
**Category:** Interview

**Request: `InterviewAssessmentScheduleCancelRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `ats_job_id` | Int | optional |
| `position_id` | Int | optional |
| `interview_id` | Str | optional |

**Response: `InterviewAssessmentScheduleCancelResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `status_code` | Int | optional |
| `ats_job_id` | Int | optional |
| `position_id` | Int | optional |
| `interview_id` | Str | optional |

---

### 20. POSITION_EXPORT
**Category:** Position

**Request: `PositionRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `position_id` | Int | optional |
| `ats_job_id` | Int | optional |
| `name` | Str | optional |
| `group_id` | Str | optional |
| `hm_email` | Email | optional |
| `candidate_reviewers` | List[Email] | optional |
| `posting_url` | Url | optional |
| `pipeline_url` | Url | optional |
| `locations` | Str | optional |
| `location_city` | Str | optional |
| `location_country` | Str | optional |
| `ats_name` | Str | optional |
| `team_data` | Dict | optional |
| `recruiter_email` | Email | optional |
| `hiring_manager_email` | Email | optional |

**Response:** `AppActionResponseType` — see Shared Types above.

---

### 21. POST_ASSESSMENT_WEBHOOK
**Category:** Assessment

**Request: `AssessmentWebhookRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `candidate_data` | Nested AssessmentInviteMetadata | optional |
| `assessment_report` | Dict | optional |
| `user_email` | Email | optional |

**Response:** `AppActionResponseType` — see Shared Types above.

---

### 22. POST_INSTALL
**Category:** Lifecycle

**Request: `PostInstallRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `ef_settings` | Dict | optional |
| `app_settings` | Dict | optional |
| `action_user_email` | Email | optional |
| `trigger_name` | Str | optional |

**Response: `PostInstallResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `is_success` | Boolean | **required** |
| `error` | Str | optional |

---

### 23. SCHEDULED_DAILY
**Category:** Scheduled

**Request: `ScheduledDailyRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |

**Response:** `AppActionResponseType` — see Shared Types above.

---

### 24. SCHEDULED_HOURLY
**Category:** Scheduled

**Request: `ScheduledHourlyRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |

**Response:** `AppActionResponseType` — see Shared Types above.

---

### 25. SCHEDULED_WEEKLY
**Category:** Scheduled

**Request: `ScheduledWeeklyRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |

**Response:** `AppActionResponseType` — see Shared Types above.

---

### 26. SMARTAPPLY_JOB_PAGE_VIEW
**Category:** SmartApply

**Request: `SmartApplyRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `user_email` | Email | optional |
| `group_id` | Str | optional |
| `position_json` | Nested SmartApplyPositionRequestType | optional |

**SmartApplyPositionRequestType fields:**

| Field | Type | Required |
|-------|------|----------|
| `name` | Str | optional |
| `description` | Str | optional |
| `job_function` | Str | optional |
| `business_unit` | Str | optional |

**Response:** `ProfileViewResponseType` — see Shared Types above.

---

### 27. TA_PROFILE_VIEW
**Category:** Talent Acquisition

**Request:** `ProfileRequestType` — see Shared Types above.

**Response:** `ProfileViewResponseType` — see Shared Types above.

---

### 28. USER_APP_ACTION_EVENT
**Category:** User Action

**Request: `UserAppActionRequestType`** *(extends ProfileRequestType)*

Inherits all fields from `ProfileRequestType`, plus:

| Field | Type | Required |
|-------|------|----------|
| `trigger_name` | Str | optional |
| `action_data` | Dict | optional |

**Response:** `AppActionResponseType` — see Shared Types above.

---

### 29. WEBHOOK_RECEIVE_EVENT
**Category:** Webhook

**Request: `WebhookReceiveEventRequestType`**

| Field | Type | Required |
|-------|------|----------|
| `headers` | Dict | optional |
| `request_payload` | Dict | optional |
| `trigger_name` | Str | optional |

**Response: `WebhookReceiveEventResponseType`**

| Field | Type | Required |
|-------|------|----------|
| `actions` | List[AppActionSingleResponse] | optional |
| `is_success` | Boolean | **required** |
| `error` | Str | optional |
| `stacktrace` | Str | optional |

---

## Quick Lookup: Trigger → Classes

| Trigger | Request Class | Response Class |
|---------|--------------|----------------|
| `ASSESSMENT_FETCH_CANDIDATE_REPORT` | `AssessmentFetchCandidateReportRequestType` | `ApplicationAssessmentData` |
| `ASSESSMENT_GET_LOGO_URL` | `AssessmentGetLogoUrlRequestType` | `AssessmentGetLogoUrlResponseType` |
| `ASSESSMENT_INVITE_CANDIDATE` | `AssessmentInviteCandidateRequestType` | `AssessmentInviteCandidateResponseType` |
| `ASSESSMENT_IS_WEBHOOK_SUPPORTED` | `AssessmentIsWebhookSupportedRequestType` | `AssessmentIsWebhookSupportedResponseType` |
| `ASSESSMENT_LIST_TESTS` | `AssessmentListTestsRequestType` | `List[AssessmentTestType]` |
| `ASSESSMENT_PROCESS_WEBHOOK` | `AssessmentProcessWebhookRequestType` | `AssessmentProcessWebhookResponseType` |
| `CAREER_HUB_HOME_SIDEBAR_VIEW` | `ProfileRequestType` | `ProfileViewResponseType` |
| `CAREER_HUB_PROFILE_VIEW` | `ProfileRequestType` | `ProfileViewResponseType` |
| `CAREER_PLANNER_RECOMMENDED_COURSES` | `CareerhubEntitySearchResultsRequestType` | `List[CareerhubRecommendedCourseResponseType]` |
| `CAREERHUB_APP_PLATFORM_CARD_CLICK` | `CareerhubAppPlatformCardClickRequestType` | `CareerhubAppPlatformCardClickResponseType` |
| `CAREERHUB_ENTITY_SEARCH_RESULTS` | `CareerhubEntitySearchResultsRequestType` | `CareerhubEntitySearchResultsResponseType` |
| `CAREERHUB_GET_ENTITY_DETAILS` | `CareerhubEntityDetailsRequestType` | `CareerhubEntityDetailsResponseType` |
| `CAREERHUB_PROFILE_COURSE_ATTENDANCE` | `ProfileCourseAttendanceRequestType` | `List[ProfileCourseAttendanceResponseType]` |
| `CAREERHUB_STATIC_ENTITY` | `CareerhubStaticEntityRequestType` | `CareerhubStaticEntityResponseType` |
| `CH_PROFILE_VIEW_MAIN_CONTENT` | `ProfileRequestType` | `ProfileViewResponseType` |
| `CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND` | `ProfileRequestType` | `ProfileViewResponseType` |
| `INTERVIEW_GENERATE_SESSION_URL` | `InterviewGenerateSessionUrlRequestType` | `InterviewGenerateSessionUrlResponseType` |
| `INTERVIEW_ASSESSMENT_SCHEDULED` | `InterviewAssessmentScheduledRequestType` | `InterviewAssessmentScheduledResponseType` |
| `INTERVIEW_ASSESSMENT_SCHEDULE_CANCEL` | `InterviewAssessmentScheduleCancelRequestType` | `InterviewAssessmentScheduleCancelResponseType` |
| `POSITION_EXPORT` | `PositionRequestType` | `AppActionResponseType` |
| `POST_ASSESSMENT_WEBHOOK` | `AssessmentWebhookRequestType` | `AppActionResponseType` |
| `POST_INSTALL` | `PostInstallRequestType` | `PostInstallResponseType` |
| `SCHEDULED_DAILY` | `ScheduledDailyRequestType` | `AppActionResponseType` |
| `SCHEDULED_HOURLY` | `ScheduledHourlyRequestType` | `AppActionResponseType` |
| `SCHEDULED_WEEKLY` | `ScheduledWeeklyRequestType` | `AppActionResponseType` |
| `SMARTAPPLY_JOB_PAGE_VIEW` | `SmartApplyRequestType` | `ProfileViewResponseType` |
| `TA_PROFILE_VIEW` | `ProfileRequestType` | `ProfileViewResponseType` |
| `USER_APP_ACTION_EVENT` | `UserAppActionRequestType` | `AppActionResponseType` |
| `WEBHOOK_RECEIVE_EVENT` | `WebhookReceiveEventRequestType` | `WebhookReceiveEventResponseType` |

---

*Generated from EightfoldAI monorepo — `www/app_platform/core/`. Date: 2026-03-25.*
