# App Platform Triggers — EightfoldAI Codebase Reference

This document provides a comprehensive reference of all folders, classes, methods, and event types related to the **App Platform Triggers** system in the EightfoldAI monorepo. Intended for MCP/AI context ingestion.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Core App Platform Triggers](#2-core-app-platform-triggers)
3. [Workflow Automation Triggers](#3-workflow-automation-triggers)
4. [Automation Framework Triggers](#4-automation-framework-triggers)
5. [Data Propagation Trigger Events](#5-data-propagation-trigger-events)
6. [API Endpoints](#6-api-endpoints)
7. [Key Design Patterns](#7-key-design-patterns)
8. [Feature Gates](#8-feature-gates)
9. [Actions Reference](#9-actions-reference)
10. [File Path Reference](#10-file-path-reference)
11. [Summary Table](#11-summary-table)

**Related Files (for MCP ingestion):**
- `app_platform_trigger_schemas.md` — Full request/response field schemas for all 29 triggers
- `app_platform_actions.md` — Detailed reference for all 28 platform actions

---

## 1. System Overview

The EightfoldAI trigger system is multi-layered and handles everything from user-facing app platform extensibility to internal event-driven workflows. It consists of four primary subsystems:

| Subsystem | Scope | Mechanism |
|-----------|-------|-----------|
| **App Platform Triggers** | External app integrations | Registry + DB-backed loader |
| **Workflow Automation Triggers** | Business workflow automation | 40+ domain-specific event handlers |
| **Automation Framework Triggers** | Scheduled/recurring tasks | Cron and interval threads |
| **Data Propagation Events** | Internal event bus | Publisher/subscriber with registry |

---

## 2. Core App Platform Triggers

### 2.1 Abstract Base Class

**Path:** `www/app_platform/triggers/trigger_base.py`

```python
class TriggerBase(abc.ABC):

    @staticmethod
    @abstractmethod
    def get_name() -> str:
        """Returns the unique name/identifier for this trigger."""
        ...

    @staticmethod
    @abstractmethod
    def get_payload_format() -> dict:
        """Returns the expected payload format/schema for this trigger."""
        ...
```

---

### 2.2 Trigger Definitions Registry

**Path:** `www/app_platform/core/app_platform_trigger_definitions.py`

**Purpose:** Centralized registry of all supported app platform triggers with their request/response type mappings.

#### Defined Trigger Names (30 total)

| # | Trigger Name | Category |
|---|-------------|----------|
| 1 | `ASSESSMENT_FETCH_CANDIDATE_REPORT` | Assessment |
| 2 | `ASSESSMENT_GET_LOGO_URL` | Assessment |
| 3 | `ASSESSMENT_INVITE_CANDIDATE` | Assessment |
| 4 | `ASSESSMENT_IS_WEBHOOK_SUPPORTED` | Assessment |
| 5 | `ASSESSMENT_LIST_TESTS` | Assessment |
| 6 | `ASSESSMENT_PROCESS_WEBHOOK` | Assessment |
| 7 | `CAREER_HUB_HOME_SIDEBAR_VIEW` | CareerHub UI |
| 8 | `CAREER_HUB_PROFILE_VIEW` | CareerHub UI |
| 9 | `CAREER_PLANNER_RECOMMENDED_COURSES` | CareerHub |
| 10 | `CAREERHUB_APP_PLATFORM_CARD_CLICK` | CareerHub |
| 11 | `CAREERHUB_ENTITY_SEARCH_RESULTS` | CareerHub |
| 12 | `CAREERHUB_GET_ENTITY_DETAILS` | CareerHub |
| 13 | `CAREERHUB_PROFILE_COURSE_ATTENDANCE` | CareerHub |
| 14 | `CAREERHUB_STATIC_ENTITY` | CareerHub |
| 15 | `CH_PROFILE_VIEW_MAIN_CONTENT` | CareerHub UI |
| 16 | `CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND` | CareerHub UI |
| 17 | `INTERVIEW_GENERATE_SESSION_URL` | Interview |
| 18 | `INTERVIEW_ASSESSMENT_SCHEDULED` | Interview |
| 19 | `INTERVIEW_ASSESSMENT_SCHEDULE_CANCEL` | Interview |
| 20 | `POSITION_EXPORT` | Position |
| 21 | `POST_ASSESSMENT_WEBHOOK` | Assessment |
| 22 | `POST_INSTALL` | Lifecycle |
| 23 | `SCHEDULED_DAILY` | Scheduled |
| 24 | `SCHEDULED_HOURLY` | Scheduled |
| 25 | `SCHEDULED_WEEKLY` | Scheduled |
| 26 | `SMARTAPPLY_JOB_PAGE_VIEW` | SmartApply |
| 27 | `TA_PROFILE_VIEW` | Talent Acquisition |
| 28 | `USER_APP_ACTION_EVENT` | User Action |
| 29 | `WEBHOOK_RECEIVE_EVENT` | Webhook |

#### Definition Structure

```python
TRIGGER_DEFINITIONS = [
    {
        'trigger_name': TriggerEventType.<NAME>,
        'request_type': request_data_classes.<RequestClass>,
        'response_type': response_data_classes.<ResponseClass>,
    },
    ...
]
```

#### Key Functions

```python
def get_dev_portal_trigger_data() -> list:
    """Returns trigger metadata with sample requests for the developer portal."""

def validate_trigger_response(trigger_name: str, response_dict: dict) -> bool:
    """Validates that a response matches the expected schema for the given trigger."""
```

---

### 2.3 App Triggers DB Loader

**Path:** `www/app_platform/core/app_platform_app_triggers.py`

**Purpose:** Database-backed loader class that manages which apps are installed on which triggers. Provides reverse lookup by trigger name.

**Database Table:** `app_platform_app_triggers`

**Redis Cache:** Namespace `app_platform_app_triggers`, key format: `{group_id}:{trigger_name}`

#### Class: `AppPlatformAppTriggers`

```python
class AppPlatformAppTriggers(db_loader.DBLoader):

    # Fields
    id: int
    group_id: str           # Multi-tenant isolation key
    app_id: str
    name: str               # Human-readable app name
    trigger_name: str       # Trigger identifier
    status: str             # InstalledAppStatus enum value
    installed_by: str       # Email of user who installed
    t_create: timestamp
    t_update: timestamp
    deleted_at: timestamp

    # Methods
    def get_trigger(group_id, app_id, trigger_name) -> AppPlatformAppTriggers
    def get_triggers_for_group_id(group_id) -> List[AppPlatformAppTriggers]
    def get_app_ids_for_trigger(group_id, trigger_name) -> List[str]
    def add_trigger(group_id, app_id, name, trigger_name, status, installed_by)
    def add_trigger_from_trigger_info(trigger_info)
    def add_app_triggers(current_user, app_id, app_name, trigger_points)
    def delete_app_triggers(current_user, app_id, trigger_points)
    def delete_trigger()
    def post_save_hook()    # Clears Redis cache on save
```

**Constraints:**
- Maximum 10,000 rows per `group_id`
- Demo account (`eightfolddemo`) supports master app sharing across tenants

---

### 2.4 Interceptor Trigger

**Path:** `www/app_platform/interceptor/app_platform_interceptor_trigger.py`

**Purpose:** Evaluates whether a trigger condition is applicable before firing, supports delayed execution.

#### Class: `AppPlatformInterceptorTrigger`

```python
class AppPlatformInterceptorTrigger:

    # Properties
    trigger_name: str
    trigger_condition: str          # Template string with {{}} placeholders
    default_request_fields: List
    default_request_fields_previous: List
    schedule_delay_seconds: int     # Optional delay before trigger fires

    # Methods
    def is_trigger_applicable(
        current_user,
        db_loader_obj,
        old_db_loader_obj=None
    ) -> bool:
        """Evaluates template condition against current entity state."""
```

**Template Context Variables:**
- `current_user` — authenticated user object
- `db_loader_obj` — current state of the entity
- `old_db_loader_obj` — previous state of the entity (for update events)
- `env` — deployment environment string

---

## 3. Workflow Automation Triggers

### 3.1 Base Class

**Path:** `www/workflow_automation/triggers/workflow_trigger_base.py`

```python
class WorkflowTriggerBase(WorkflowComponentBase):

    @abstractmethod
    def get_table_name() -> str:
        """Returns the DB table this trigger monitors."""

    @abstractmethod
    def get_default_included_filters() -> List[str]:
        """Returns default filter names available for this trigger."""

    @abstractmethod
    def is_trigger_applicable(
        current_user,
        db_loader_obj,
        old_db_loader_obj=None
    ) -> bool:
        """Returns True if the trigger should fire for the given entity state."""

    def get_delay_time(group_id=None) -> int
    def get_reevaluate_seconds(group_id=None) -> int
    def get_excluded_filters(entity_id_field) -> List[str]
    def get_trigger_controllers(...) -> List[TriggerController]
    def is_visible(current_user, entity_id_field) -> bool
```

### 3.2 Trigger Implementations

**Path:** `www/workflow_automation/triggers/`

**Total:** 90+ trigger implementation files

| Trigger File | Event |
|---|---|
| `new_application_trigger.py` | New application received |
| `stage_change_trigger.py` | Candidate stage changed |
| `entity_stage_change_trigger.py` | Any entity stage transition |
| `entity_reject_candidate_trigger.py` | Entity rejected candidate |
| `offer_status_change_trigger.py` | Offer status changed |
| `offer_created_trigger.py` | New offer created |
| `offer_deleted_trigger.py` | Offer deleted |
| `new_position_trigger.py` | New position created |
| `position_status_change_trigger.py` | Position status changed |
| `position_unpublished_trigger.py` | Position unpublished |
| `position_reject_trigger.py` | Position rejected |
| `feedback_requested_trigger.py` | Feedback requested |
| `feedback_submitted_trigger.py` | Feedback submitted |
| `decision_submitted_trigger.py` | Hiring decision submitted |
| `profile_tag_added_trigger.py` | Profile tag added |
| `ats_profile_tags_added_trigger.py` | ATS profile tag added |
| `profile_marked_for_followup_trigger.py` | Profile marked for follow-up |
| `candidate_saved_to_another_pipeline_trigger.py` | Candidate saved to pipeline |
| `contact_trigger.py` | Contact event |
| `contact_replied_trigger.py` | Contact replied |
| `meeting_scheduled_trigger.py` | Meeting scheduled |
| `meeting_confirmed_by_candidate_trigger.py` | Candidate confirmed meeting |
| `booking_created_trigger.py` | Booking created |
| `booking_status_change_trigger.py` | Booking status changed |
| `booking_deleted_trigger.py` | Booking deleted |
| `assessment_completed_trigger.py` | Assessment completed |
| `preboarding_package_created_trigger.py` | Onboarding package created |
| `preboarding_package_status_change_trigger.py` | Onboarding status changed |
| `form_submission_status_change_trigger.py` | Form submission status changed |
| `employee_onboarded_to_careerhub_trigger.py` | Employee onboarded to CareerHub |
| `demand_time_state_change_trigger.py` | Demand/time state changed |
| `community_reject_trigger.py` | Community rejection |

### 3.3 Trigger Registry

**Path:** `www/workflow_automation/triggers/workflow_triggers_registry.py`

```python
TRIGGERS_REGISTRY = {
    # Maps trigger constant name (str) -> trigger class (WorkflowTriggerBase subclass)
    # 40+ entries
}
```

---

## 4. Automation Framework Triggers

**Path:** `www/automation_framework/workflow/triggers/`

### 4.1 Abstract Base

**File:** `base.py`

```python
class BaseTrigger(ABC):

    def __init__(self, config: Dict[str, Any], callback: Callable):
        ...

    @abstractmethod
    def start():
        """Start the trigger (spawns daemon thread)."""

    @abstractmethod
    def stop():
        """Stop the trigger gracefully."""
```

### 4.2 Cron Trigger

**File:** `cron.py`

```python
class CronTrigger(BaseTrigger):
    """Fires callback on a cron schedule."""

    # Config schema
    config = {
        'cron_expression': str,   # e.g. "0 10 * * 1"
        'timezone': str           # e.g. "Asia/Kolkata" (default: UTC)
    }

    # Event data emitted on fire
    event_data = {
        'timestamp': float,
        'trigger_type': 'cron',
        'cron_expression': str,
        'timezone': str,
        'scheduled_time': str     # ISO 8601 format
    }
```

**Cron Expression Format:**
```
* * * * *
| | | | +-- Day of week (0–6, Sunday=0, or MON–FRI)
| | | +---- Month (1–12)
| | +------ Day of month (1–31)
| +-------- Hour (0–23)
+---------- Minute (0–59)
```

**Examples:**
| Expression | Meaning |
|---|---|
| `*/5 * * * *` | Every 5 minutes |
| `0 * * * *` | Every hour |
| `0 10 * * 1` | Monday at 10:00 AM |
| `30 13 * * MON-FRI` | Weekdays at 1:30 PM |

### 4.3 Interval Trigger

**File:** `interval.py`

```python
class IntervalTrigger(BaseTrigger):
    """Fires callback on a fixed time interval."""

    # Config schema
    config = {
        'interval_seconds': int   # Default: 10 seconds
    }

    # Event data emitted on fire
    event_data = {
        'timestamp': float,
        'trigger_type': 'interval'
    }
```

---

## 5. Data Propagation Trigger Events

### 5.1 Trigger Event Types

**Path:** `www/data_propagation/trigger_event_type.py`

#### Profile Events
- `CANDIDATE_PROFILE_CREATED`
- `CANDIDATE_PROFILE_UPDATED`
- `EMPLOYEE_PROFILE_UPDATED`
- `EMPLOYEE_PROFILE_ONBOARDED`
- `EMPLOYEE_DATA_SOURCE_USER_CONSENT_CHANGED`
- `PROFILE_DATA_CHANGED`
- `DB_PROFILE_STAGE_DATA_UPDATE`
- `DB_PROFILE_ATS_DATA_UPDATE`

#### Candidate / Application Events
- `DB_CANDIDATE_CREATE`
- `DB_CANDIDATE_UPDATE`
- `DB_APPLICATION_CREATE`
- `DB_APPLICATION_UPDATE`
- `DB_CLAIMED_CANDIDATE_PROFILE_CHANGED`
- `CANDIDATE_STAGE_ADVANCE`

#### Position / Offer Events
- `DB_ATS_POSITION_CREATE`
- `DB_POSITION_CHANGED`
- `DB_POSITION_DATA_CHANGED`
- `DB_OFFERS_CHANGED`
- `POSITION_EXPORT`
- `POSITION_UNPUBLISHED`

#### Feedback Events
- `DB_FEEDBACK_REQUESTED`
- `DB_FEEDBACK_CANCELLED`
- `DB_FEEDBACK_SUBMITTED`
- `DB_FEEDBACK_REMINDER`

#### User Events
- `DB_USER_LOGIN_CREATE`
- `DB_USER_LOGIN_UPDATE`
- `DB_USER_LOGIN_DELETE`
- `USER_ACCOUNT_FIRST_LOGIN`
- `USER_ACCOUNT_DELETE`

#### UI / View Events
- `CAREER_HUB_PROFILE_VIEW`
- `CAREER_HUB_HOME_SIDEBAR_VIEW`
- `CH_PROFILE_VIEW_MAIN_CONTENT`
- `CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND`
- `TA_PROFILE_VIEW`
- `TM_PROFILE_VIEW`
- `SMARTAPPLY_JOB_PAGE_VIEW`
- `CAREERHUB_ENTITY_SEARCH_RESULTS`
- `CAREERHUB_GET_ENTITY_DETAILS`
- `CAREERHUB_STATIC_ENTITY`

#### Scheduled Events
- `SCHEDULED_HOURLY`
- `SCHEDULED_DAILY`
- `SCHEDULED_WEEKLY`

#### Assessment Events
- `ASSESSMENT_GET_LOGO_URL`
- `ASSESSMENT_IS_WEBHOOK_SUPPORTED`
- `ASSESSMENT_LIST_TESTS`
- `ASSESSMENT_INVITE_CANDIDATE`
- `ASSESSMENT_FETCH_CANDIDATE_REPORT`
- `ASSESSMENT_PROCESS_WEBHOOK`
- `POST_ASSESSMENT_WEBHOOK`
- `ASSESSMENT_AUTO_INVITE_CANDIDATE`

#### Interview Events
- `INTERVIEW_GENERATE_SESSION_URL`
- `INTERVIEW_ASSESSMENT_SCHEDULED`
- `INTERVIEW_ASSESSMENT_SCHEDULE_CANCEL`

#### Webhook / Action Events
- `WEBHOOK_RECEIVE_EVENT`
- `USER_APP_ACTION_EVENT`

#### Background Verification Events
- `BGV_LIST_PACKAGES`
- `BGV_INITIATE_BACKGROUND_VERIFICATION`
- `BGV_FETCH_REPORTS`
- `BGV_FETCH_CANDIDATE_REPORT`
- `BGV_PROCESS_WEBHOOK`

#### Miscellaneous Events
- `POST_INSTALL`
- `HIRING_COMPANY_CREATE`
- `HIRING_COMPANY_UPDATE`
- `FORM_SUBMISSION_CHANGED`
- `PROFILE_NOTE_CREATE`
- `PROFILE_TAG_CREATE`
- `EMAIL_RECIPIENT_VALIDATION`
- `DATA_STREAM_CHANGE`
- `ATS_ADAPTER_INTEGRATION`
- `SYNC_EXTERNAL_SKILLS`
- `WRITEBACK_EXTERNAL_SKILLS`
- `SEND_NOTIFICATION`
- `SYNC_CANDIDATE_TO_LINKEDIN`
- `GET_PUBLISHED_DOCUMENT`
- `GET_SIGNATURE_STATUS`
- `GET_SIGNING_URL`

---

### 5.2 TriggerEvent Object

**Path:** `www/data_propagation/trigger_event.py`

```python
class TriggerEvent:

    def __init__(self,
                 group_id: str,
                 entity_type: str,
                 system_id: str = None,
                 entity_id: str = None,
                 event_context: dict = None,
                 old_entity: dict = None,
                 new_entity: dict = None,
                 event_type: str = None):
        ...

    def get_json() -> str
    def to_dict() -> dict
    def get_entity_group_id() -> str | None
```

#### ProfileSectionUpdateRequest

```python
class ProfileSectionUpdateRequest:

    section_name: str
    section_item: dict
    section_id: str
    section_item_key: str
    all_section_items: list
    delete: bool
    external_profile_id: str
    section_config: dict

    # Computed properties
    @property
    def external_section_name(self) -> str
    @property
    def external_section_id(self) -> str
    @property
    def external_section_item_name(self) -> str
    @property
    def external_section_item_key_name(self) -> str
```

---

### 5.3 Trigger Event Registry

**Path:** `www/data_propagation/trigger_event_registry.py`

**Purpose:** Maps `TriggerEventType` constants to their `TriggerEventInfo` handler implementations (70+ entries).

**Notable EventInfo Implementations:**
- `CandidateUpdateTriggerEventInfo`
- `CandidateCreateTriggerEventInfo`
- `ApplicationUpdateTriggerEventInfo`
- `ApplicationCreateTriggerEventInfo`
- `AtsPositionCreateTriggerEventInfo`
- `UserLoginCreateTriggerEventInfo`
- `UserLoginUpdateTriggerEventInfo`
- `UserLoginDeleteTriggerEventInfo`
- `HiringCompanyCreateTriggerEventInfo`
- `HiringCompanyUpdateTriggerEventInfo`
- `FeedbackRequestedTriggerEventInfo`
- `FeedbackCancelledTriggerEventInfo`
- `FeedbackSubmittedTriggerEventInfo`
- `FeedbackReminderTriggerEventInfo`
- `ProfileStageDataUpdateTriggerEventInfo`
- `ProfileAtsDataUpdateTriggerEventInfo`
- `ClaimedCandidateProfileChangedTriggerEventInfo`
- `ProfileDataChangedTriggerEventInfo`
- `PositionChangedTriggerEventInfo`
- `PositionDataChangedTriggerEventInfo`
- `OffersChangedTriggerEventInfo`
- `OrgUnitChangedTriggerEventInfo`
- `FormSubmissionChangedTriggerEventInfo`
- `ProfileNoteCreateTriggerEventInfo`
- `ProfileTagCreateTriggerEventInfo`
- `UserMessageCreatedTriggerEventInfo`
- `CareerInterestSkillsUpdateTriggerEventInfo`
- `UserDetailsUpdateTriggerEventInfo`
- `EmployeeDemandLoggedHoursChangedTriggerEventInfo`
- `SyncCandidateToLinkedInTriggerEventInfo`

---

### 5.4 Supporting Data Propagation Files

| File | Purpose |
|------|---------|
| `trigger_event_config_utils.py` | Configuration utilities |
| `trigger_event_utils.py` | General helper utilities |
| `trigger_event_factory.py` | Factory for creating TriggerEvent instances |
| `trigger_event_info.py` | Metadata class for trigger events |
| `trigger_event_constants.py` | Constants and config values |
| `publisher/trigger_event_publisher.py` | Publishes events to the message bus |
| `publisher/trigger_event_publish_helper.py` | Publishing utility helpers |
| `consumers/trigger_assessment_on_stage_advance_consumer.py` | Consumer for assessment-on-stage-advance events |
| `processor/trigger_event_operation.py` | Processor integration for trigger events |

---

## 6. API Endpoints

**Path:** `www/apps/app_platform_app/app_platform_api.py`

**Base Namespace:** `/api/app_platform`

| Endpoint | Method | Purpose |
|---|---|---|
| `/create_app` | POST | Create a new app with trigger points |
| `/update_app` | POST | Update app version and trigger points |
| `/render_app` | POST | Invoke a trigger and render the app response |
| `/invoke_app` | POST | Invoke app by `app_id` and `trigger_name` (sync/async) |
| `/invoke_app_context` | GET | Fetch context data for a given app and trigger |
| `/test_app` | POST | Test app execution with a specific trigger |

**Trigger names supported in `/render_app`:**
- `CAREER_HUB_PROFILE_VIEW`
- `CAREER_HUB_HOME_SIDEBAR_VIEW`
- `CH_PROFILE_VIEW_MAIN_CONTENT`
- `CH_PROFILE_VIEW_MAIN_CONTENT_ON_EXPAND`
- `TA_PROFILE_VIEW`
- `TM_PROFILE_VIEW`
- `SMARTAPPLY_JOB_PAGE_VIEW`

**Features:**
- Async trigger support via `app_platform_utils.get_async_triggers()`
- Redis caching under namespace `app_platform`
- Multi-tenant isolation via `group_id`
- I18n support for error messages
- Error tracking and monitoring integration

---

## 7. Key Design Patterns

| Pattern | Where Used | Description |
|---------|-----------|-------------|
| **Registry Pattern** | `app_platform_trigger_definitions.py`, `workflow_triggers_registry.py`, `trigger_event_registry.py` | Central mappings of names → implementations |
| **Abstract Base Classes** | `TriggerBase`, `WorkflowTriggerBase`, `BaseTrigger` | Enforce interface contracts across all trigger types |
| **Multi-tenancy** | `AppPlatformAppTriggers`, all API endpoints | `group_id` used for complete tenant isolation |
| **Redis Caching** | `AppPlatformAppTriggers.post_save_hook()`, render_app | Performance optimization for trigger lookups |
| **Event Sourcing** | `TriggerEvent` | Captures both `old_entity` and `new_entity` state |
| **Template Evaluation** | `AppPlatformInterceptorTrigger` | `{{}}` placeholder substitution for trigger conditions |
| **Async Support** | `/invoke_app` API endpoint | Separate handling for long-running async triggers |
| **Daemon Threads** | `CronTrigger`, `IntervalTrigger` | Background execution for scheduled triggers |

---

## 8. Feature Gates

Feature gates are boolean flags per tenant (`group_id`) that enable or disable specific App Platform behaviors. Gates are checked via `app_platform_utils.py`.

**Source:** `www/app_platform/core/app_platform_constants.py`, `www/app_platform/core/app_platform_app_state.py`, `www/app_platform/actions/action_registry.py`

### 8.1 Core Platform Gates

| Gate Name | Constant | Purpose |
|-----------|----------|---------|
| `app_platform_dev_portal_partners_gate` | `APP_PLATFORM_DEV_PORTAL_PARTNER_GATE` | Allows partner apps to publish directly without Eightfold review |
| `app_platform_dev_portal_admin_view_gate` | `APP_PLATFORM_DEV_PORTAL_ADMIN_VIEW_GATE` | Enables admin-only views in the developer portal |
| `user_activity_app_platform_gate` | `USER_ACTIVITY_APP_PLATFORM_GATE` | Enables user activity tracking within app platform flows |
| `app_platform_ecs_apps_gate` | `APP_PLATFORM_ECS_APPS_GATE` | Routes fully async app execution to ECS Fargate instead of Lambda |
| `app_platform_candidate_stage_advance_trigger_gate` | `APP_PLATFORM_CANDIDATE_STAGE_ADVANCE_TRIGGER_GATE` | Enables the `CANDIDATE_STAGE_ADVANCE` trigger type |
| `app_platform_app_state_gate` | `APP_PLATFORM_APP_STATE_GATE` | Enables admin-level app state transitions (approve, publish, cross-group modify) |

### 8.2 Trigger-Specific Gates

| Gate Name | Trigger / Area | Behavior When Enabled |
|-----------|---------------|----------------------|
| `app_platform_candidate_stage_advance_trigger_gate` | `CANDIDATE_STAGE_ADVANCE` | Trigger is active and will fire on stage advance events |
| `app_platform_ecs_apps_gate` | `SCHEDULED_*`, async apps | Uses ECS Fargate for execution instead of Lambda |
| `external_skills_oauth_gate` | Viva / external skills apps | Passes OAuth flag to app; uses OAuth instead of certificate auth |

### 8.3 Action-Specific Gates

| Gate Name | Action | Behavior When Enabled |
|-----------|--------|----------------------|
| `download_profiles_to_pdf_gate` | `download_to_pdf` | Generates PDFs asynchronously via queue and returns a secure link |
| `etx_approval_status_gate` | `handle_profile_video_creation` | Auto-sets profile approval status to `approved` on video creation in talent exchange |
| `extract_highlights_from_traits_for_csv_gate` | `convert_data_to_csv` | Extracts profile highlights from traits section when building CSV export |
| `raise_exception_on_payrate_lookup_failure_gate` | `entity_update_action` | Raises exception (rather than silently failing) when payrate lookup fails |
| `app_platform_apps_metadata_broadcast_gate` | App metadata ops | Broadcasts app metadata changes to all relevant services |

---

## 9. Actions Reference

Actions are the side effects an app can trigger as part of its response. They are returned inside the `actions` field of trigger responses (e.g., `AppActionResponseType`, `AssessmentInviteCandidateResponseType`).

**Full details in:** `app_platform_actions.md`
**Source:** `www/app_platform/actions/action_registry.py`

### 9.1 Actions by Category

| Category | Action Name | Description |
|----------|-------------|-------------|
| **Data & Profile** | `save_to_profile_data` | Saves JSON data to candidate profile under a given namespace and subkey |
| | `save_profile_app_data` | Saves app-generated data under `APP_PROFILE_DATA` namespace with field validation |
| | `save_profile_highlights` | Saves profile highlights to profile data |
| | `save_assessment_to_profile_data` | Stores assessment test results and vendor data in candidate profile |
| | `save_practice_assessment_result_to_profile_data` | Saves practice assessment data without requiring prior invitation |
| | `save_interview_to_profile_data` | Saves interview report and metadata to candidate profile |
| | `save_app_data` | Saves general app data to `app_platform_apps_data` table |
| | `store_app_specific_data` | Stores app-specific profile data namespaced by `app_id` |
| | `store_employee_availability_data` | Saves employee availability data for resource planning |
| | `save_account_credentialed_data` | Saves OAuth account credential data to `user_auth_tokens` |
| | `token_deauthorized` | Marks OAuth token as deauthorized and clears access token |
| **Entity Operations** | `entity_update_action` | Updates position or candidate entities (custom fields, ATS data) |
| | `ats_entity_create_update_action` | Creates or updates ATS entities (positions/candidates) with sync tracking |
| **Communication** | `send_email` | Sends raw email (sender, recipient, subject, body, attachments) |
| | `send_email_with_template` | Sends email using a saved template with variable substitution |
| | `send_email_with_template_v2` | Enhanced template email with extra variables and attachments |
| | `add_user_message` | Adds a message to the user messaging system with conversation tracking |
| **Interview & Assessment** | `schedule_interview_action` | Schedules interviews for candidates using scheduling templates |
| | `assessment_auto_invite_candidate` | Triggers automatic assessment invitations for candidates |
| **Media & Content** | `handle_profile_video_creation` | Processes profile video creation with talent exchange approval status updates |
| | `handle_profile_video_flagging` | Flags/manages profile videos with exchange admin notifications |
| | `persist_content` | Saves app-generated content (files, documents) to S3 with base64 encoding |
| | `download_to_pdf` | Exports profiles to PDF with optional masking and resume inclusion |
| **Data Export** | `convert_data_to_csv` | Converts data rows to CSV format and uploads to S3 |
| **Administrative** | `stage_advance` | Placeholder for candidate stage advancement (currently no-op) |
| | `schedule_app_notification` | Schedules async app notifications via queue |
| **Utility** | `open_url` | Opens a URL in a new browser tab with optional message |
| | `echo` | Test action for e2e testing of action infrastructure |

### 9.2 Triggers That Return Actions

| Trigger | Response Type | Actions Field |
|---------|--------------|---------------|
| `ASSESSMENT_INVITE_CANDIDATE` | `AssessmentInviteCandidateResponseType` | `actions: List[AppActionSingleResponse]` |
| `POSITION_EXPORT` | `AppActionResponseType` | `actions: List[AppActionSingleResponse]` |
| `POST_ASSESSMENT_WEBHOOK` | `AppActionResponseType` | `actions: List[AppActionSingleResponse]` |
| `SCHEDULED_HOURLY` | `AppActionResponseType` | `actions: List[AppActionSingleResponse]` |
| `SCHEDULED_DAILY` | `AppActionResponseType` | `actions: List[AppActionSingleResponse]` |
| `SCHEDULED_WEEKLY` | `AppActionResponseType` | `actions: List[AppActionSingleResponse]` |
| `USER_APP_ACTION_EVENT` | `AppActionResponseType` | `actions: List[AppActionSingleResponse]` |
| `WEBHOOK_RECEIVE_EVENT` | `WebhookReceiveEventResponseType` | `actions: List[AppActionSingleResponse]` |

---

## 10. File Path Reference

### Core App Platform
```
www/app_platform/triggers/trigger_base.py
www/app_platform/triggers/__init__.py
www/app_platform/core/app_platform_trigger_definitions.py
www/app_platform/core/app_platform_app_triggers.py
www/app_platform/interceptor/app_platform_interceptor_trigger.py
```

### Workflow Automation
```
www/workflow_automation/triggers/workflow_trigger_base.py
www/workflow_automation/triggers/workflow_triggers_registry.py
www/workflow_automation/triggers/<trigger_name>_trigger.py   (90+ files)
```

### Automation Framework
```
www/automation_framework/workflow/triggers/base.py
www/automation_framework/workflow/triggers/cron.py
www/automation_framework/workflow/triggers/interval.py
www/automation_framework/workflow/triggers/__init__.py
www/automation_framework/workflow/triggers/tests/
```

### Data Propagation
```
www/data_propagation/trigger_event_type.py
www/data_propagation/trigger_event.py
www/data_propagation/trigger_event_registry.py
www/data_propagation/trigger_event_factory.py
www/data_propagation/trigger_event_info.py
www/data_propagation/trigger_event_constants.py
www/data_propagation/trigger_event_config_utils.py
www/data_propagation/trigger_event_utils.py
www/data_propagation/publisher/trigger_event_publisher.py
www/data_propagation/publisher/trigger_event_publish_helper.py
www/data_propagation/consumers/trigger_assessment_on_stage_advance_consumer.py
www/data_propagation/processor/trigger_event_operation.py
```

### API & Supporting
```
www/apps/app_platform_app/app_platform_api.py
www/apps/app_platform_app/app_platform_api_utils.py
www/apps/app_platform_app/app_store_api.py
www/apps/app_platform_app/dev_portal_api.py
www/interceptors/trigger_event_interceptor.py
www/monitoring/alarms/dp/trigger_event_alarms.py
www/candidate_preboarding/trigger_event/preboarding_event_handler.py
www/candidate_preboarding/trigger_event/ats_offer_event_handler.py
```

### Frontend
```
www/react/src/apps/helixa/components/RetriggerPanel.tsx
```

---

## 9. Summary Table

| Component | Path | Purpose | Key Artifacts |
|-----------|------|---------|---------------|
| **App Platform Base** | `www/app_platform/triggers/` | Abstract trigger interface | `TriggerBase` |
| **Trigger Definitions** | `www/app_platform/core/app_platform_trigger_definitions.py` | Registry of 30 app platform triggers | `TRIGGER_DEFINITIONS`, `validate_trigger_response()` |
| **App Triggers DB** | `www/app_platform/core/app_platform_app_triggers.py` | Track installed app–trigger mappings | `AppPlatformAppTriggers` |
| **Interceptor Trigger** | `www/app_platform/interceptor/` | Conditional trigger evaluation + delay | `AppPlatformInterceptorTrigger` |
| **Workflow Triggers** | `www/workflow_automation/triggers/` | 40+ domain-specific event triggers | `WorkflowTriggerBase`, 90+ implementations |
| **Automation Framework** | `www/automation_framework/workflow/triggers/` | Cron & interval scheduling | `BaseTrigger`, `CronTrigger`, `IntervalTrigger` |
| **Event Types** | `www/data_propagation/trigger_event_type.py` | 100+ trigger event type constants | `TriggerEventType` |
| **Event Objects** | `www/data_propagation/trigger_event.py` | Event data structures | `TriggerEvent`, `ProfileSectionUpdateRequest` |
| **Event Registry** | `www/data_propagation/trigger_event_registry.py` | Maps events → handlers (70+ entries) | `TRIGGER_EVENT_INFO_REGISTRY` |
| **API Endpoints** | `www/apps/app_platform_app/app_platform_api.py` | REST API for app platform triggers | `/render_app`, `/invoke_app`, `/create_app` |

---

*Generated from EightfoldAI monorepo — `www/` directory. Date: 2026-03-24.*
