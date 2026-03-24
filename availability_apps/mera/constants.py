class AppSettingsAttributes:
    API_URL = 'api_url'
    OAUTH_SETTINGS = 'oauth_settings'

    @staticmethod
    def get_required_attrs():
        return [AppSettingsAttributes.API_URL, AppSettingsAttributes.OAUTH_SETTINGS]


class RequestDataAttributes:
    EMPLOYEE_IDS = 'employee_ids'
    START_DATE = 'start_date'
    END_DATE = 'end_date'

    @staticmethod
    def get_required_attrs():
        return [
            RequestDataAttributes.EMPLOYEE_IDS,
            RequestDataAttributes.START_DATE,
            RequestDataAttributes.END_DATE
        ]


class MeraRequestAttributes:
    GPNIDS = 'gpniDs'
    START_DATE = 'dtStartDate'
    END_DATE = 'dtEndDate'


class MeraResponseAttributes:
    GPN = 'GPN'
    GUI = 'GUI'
    EXTERNAL_CONFIRMED_AVL_PCT = 'ExternalConfirmedAvlPct'
    EXTERNAL_AVL_PCT = 'ExternalAvlPct'
    TOTAL_CONFIRMED_AVL_PCT = 'TotalConfirmedAvlPct'


class EFResponseAttributes:
    EMPLOYEE_ID = 'employee_id'
    EXTERNAL_AVL_PCT = 'external_avl_pct'
    EXTERNAL_CONFIRMED_AVL_PCT = 'external_confirmed_avl_pct'
    TOTAL_CONFIRMED_AVL_PCT = 'total_confirmed_avl_pct'

    @staticmethod
    def get_ef_to_mera_response_map():
        return {
            EFResponseAttributes.EMPLOYEE_ID: MeraResponseAttributes.GPN,
            EFResponseAttributes.EXTERNAL_AVL_PCT: MeraResponseAttributes.EXTERNAL_AVL_PCT,
            EFResponseAttributes.EXTERNAL_CONFIRMED_AVL_PCT: MeraResponseAttributes.EXTERNAL_CONFIRMED_AVL_PCT,
            EFResponseAttributes.TOTAL_CONFIRMED_AVL_PCT: MeraResponseAttributes.TOTAL_CONFIRMED_AVL_PCT
        }
