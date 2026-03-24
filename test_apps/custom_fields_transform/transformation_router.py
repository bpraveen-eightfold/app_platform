from __future__ import absolute_import

import transformations

POST_FETCH_TRANSFORMATION_MAP = {
    # This first 4 are repeated to have the backward compatibility for fetching the right transformation function
    'position': transformations.fetch_customize_ef_position,
    'application': transformations.fetch_customize_ef_application,
    'candidate': transformations.fetch_customize_ef_candidate,
    'employee': transformations.fetch_customize_ef_employee,
    'fetch_position': transformations.fetch_customize_ef_position,
    'fetch_application': transformations.fetch_customize_ef_application,
    'fetch_candidate': transformations.fetch_customize_ef_candidate,
    'fetch_employee': transformations.fetch_customize_ef_employee,
    'fetch_employee_education': transformations.fetch_customize_ef_employee_education,
    'fetch_employee_additional_fields': transformations.fetch_customize_ef_employee_additional_fields,
    'fetch_employee_internal_experience': transformations.fetch_customize_ef_candidate_internal_experience,
    'fetch_employee_external_experience': transformations.fetch_customize_ef_candidate_external_experience,
    'fetch_hris_job_position': transformations.fetch_customize_ef_hris_job_position,
    'fetch_org_unit': transformations.fetch_customize_ef_org_unit,
    'fetch_role':transformations.fetch_customize_ef_role,
}

PRE_WRITE_BACK_TRANSFORMATION_MAP = {
    'add_application': transformations.writeback_customize_ats_application,
    'add_candidate': transformations.writeback_customize_ats_candidate,
    'ef_add_application': transformations.writeback_customize_ef_managed_ats_application,
    'ef_add_candidate': transformations.writeback_customize_ef_managed_ats_candidate,
    'change_application_stage': transformations.writeback_customize_ats_application_stage,
    'transform_ats_sync_activity': transformations.writeback_transform_ats_sync_activity,
    'add_hris_job_position': transformations.writeback_customize_hris_job_position,
    'change_job': transformations.writeback_customize_hris_internal_hire,
    'hire_employee': transformations.writeback_customize_hris_new_hire,
    'update_candidate': transformations.writeback_customize_ats_update_candidate,
}

def apply_post_fetch_transformation(ats_entity_dict, ef_entity_dict, transform_op):
    transformation_handler = POST_FETCH_TRANSFORMATION_MAP.get(transform_op)
    if not transformation_handler:
        raise Exception('Transformation handler not found for transform_op: {}'.format(transform_op))
    if isinstance(ats_entity_dict, list):
        for i in range(len(ats_entity_dict)):
            transformation_handler(ats_entity_dict[i], ef_entity_dict[i])
    else:
        transformation_handler(ats_entity_dict, ef_entity_dict)

def apply_pre_write_back_transformation(ef_entity_dict, ats_entity_dict, transform_op):
    transformation_handler = PRE_WRITE_BACK_TRANSFORMATION_MAP.get(transform_op)
    if not transformation_handler:
        raise Exception('Transformation handler not found for transform_op: {}'.format(transform_op))
    transformation_handler(ef_entity_dict, ats_entity_dict)
