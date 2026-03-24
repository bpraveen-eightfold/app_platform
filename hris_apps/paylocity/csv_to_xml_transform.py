from __future__ import absolute_import
import argparse
import sys
import json
import datetime as dt
import glog as log
import csv
from lxml import etree

EMAILS = {}
dupe_email_count = 0


def generate_empty_xml_tag(parent_tag, child_tag_element, child_tag_value):
    child_tag_value = child_tag_value.strip()
    
    child_tag = etree.Element(child_tag_element)
    if child_tag_value:
        creation_dt_obj = dt.datetime.strptime(child_tag_value,'%m/%d/%y')
        child_tag.text = creation_dt_obj.strftime('%Y-%m-%d')
    else: 
        child_tag.text = child_tag_value
    parent_tag.append(child_tag)



def generate_ef_childtags(current_row, element_name, col_name, islower):
    try:
        ef_childtag = etree.Element(element_name)
        if islower == "Lowercase":
            ef_childtag.text = current_row.get(col_name).strip().lower()
        else:
            ef_childtag.text = current_row.get(col_name).strip()
    except Exception as e:
        log.info("generate_ef_childtags function has error: ", current_row.get(col_name), e)
    return ef_childtag

def generate_ef_childtags_value(current_row, element_name, col_name):
    try:
        ef_childtag = etree.Element(element_name)
        ef_childtag.text = col_name.lower()

    except Exception as e:
        log.info("generate_ef_childtags_value function has error: ", col_name, e)
    return ef_childtag



def generate_ef_childtags_list_email(current_row):

    ef_t_tag = ''
    email = current_row.get('EMAIL')
    print(email)
    if 'unknown@eightfold.ai' in email:
        return ef_t_tag
    
    if not email:
        email = 'empty@' + 'eightfold.ai'

    print(email)
    if email in EMAILS:
        global dupe_email_count
        print('dupe', email)
        dupe_email_count += 1
        return ef_t_tag
    else:
        EMAILS[email] = current_row['TERMINATION_DATE']
        ef_t_tag = etree.Element('email_list')
        ef_email = generate_ef_childtags_parm('email', email)
        ef_t_tag.append(ef_email)

    return ef_t_tag


def get_tag_custom(ef_tag_custom, field_value, field_name):
    
    ef_tag_custom_field = etree.Element('custom_field')
    ef_tag_custom_field_name = etree.Element('field_name')
    ef_tag_custom_data_type = etree.Element('data_type')
    ef_tag_custom_field_value = etree.Element('field_value')

    ef_tag_custom_field_name.text = field_name
    ef_tag_custom_data_type.text = 'string'
    ef_tag_custom_field_value.text = field_value

    ef_tag_custom_field.append(ef_tag_custom_field_name)
    ef_tag_custom_field.append(ef_tag_custom_data_type)
    ef_tag_custom_field.append(ef_tag_custom_field_value)

    ef_tag_custom.append(ef_tag_custom_field)

    return ef_tag_custom

    

def generate_ef_fieldname_tags(element_name, col_name):
    try:
        ef_fieldname_tags = etree.Element(element_name)
        ef_fieldname_tags.text = col_name
    except Exception as e:
        log.info("ef_fieldname_tags function has error: ", element_name, col_name, e)
    return ef_fieldname_tags

def generate_ef_childtags_parm(element_name, col_name):
    try:
        ef_grandchildtags_list = etree.Element(element_name)
        ef_grandchildtags_list.text = col_name

    except Exception as e:
        print("generate_ef_childtags_parm function has error: ", col_name, e)
    finally:
        return ef_grandchildtags_list

def generate_ef_childtags_dt(current_row, element_name, col_name):
    try:
        ef_childtags_dt = etree.Element(element_name)
        childtags_dt = current_row.get(col_name).strip()

        if childtags_dt.strip() != '':
            creation_dt_obj = dt.datetime.strptime(childtags_dt, '%Y-%m-%dT%H:%M:%S')
            ef_childtags_dt.text = creation_dt_obj.strftime('%Y-%m-%dT%H:%M:%S')
        else:
            ef_childtags_dt.text = ''
    except Exception as e:
        log.info("generate_ef_childtags_dt function has error: ", e)
    return ef_childtags_dt


def generate_ef_childtags_small_dt(current_row, element_name, col_name):
    try:
        ef_childtags_small_dt = etree.Element(element_name)
        childtags_dt = current_row.get(col_name).strip()
        if(childtags_dt.strip() != ''):
            creation_dt_obj = dt.datetime.strptime(childtags_dt,'%m/%d/%y')
            ef_childtags_small_dt.text = creation_dt_obj.strftime('%Y-%m-%d')
        else:
            ef_childtags_small_dt.text = ''
    except Exception as e:
        print("generate_ef_childtags_small_dt function has error: ",  ef_childtags_small_dt  ,e  )
    finally:
        return ef_childtags_small_dt


def generate_ef_childtags_small_dt2(current_row, element_name, col_name):
    try:
        ef_childtags_small_dt = etree.Element(element_name)
        childtags_dt = current_row.get(col_name).strip()

        if(childtags_dt.strip() != ''):
            creation_dt_obj = dt.datetime.strptime(childtags_dt,'%Y-%m-%dT%H:%M:%S')
            ef_childtags_small_dt.text = creation_dt_obj.strftime('%Y-%m-%d')
        else:
            ef_childtags_small_dt.text = ''

    except Exception as e:
        print("generate_ef_childtags_small_dt2 function has error: ",  ef_childtags_small_dt  ,e  )
    finally:
        return ef_childtags_small_dt


def generate_ef_childtags_concat(current_row, element_name, col_name1, col_name2):
    try:
        ef_childtags_concat = etree.Element(element_name)
        ef_childtags_concat.text = current_row.get(col_name1).strip() + '-' + current_row.get(col_name2).strip()

    except Exception as e:
        log.info("generate_ef_childtags_concat function has error: ", current_row[col_name1], e)
    return ef_childtags_concat


def generate_ef_childtags_list(current_row, element_list_name, element_name, col_name):
    try:
        ef_childtags_list = etree.Element(element_list_name)
        ef_grandchildtags_list = etree.Element(element_name)
        ef_grandchildtags_list.text = current_row.get(col_name).strip()
        ef_childtags_list.append(ef_grandchildtags_list)

    except Exception as e:
        log.info("generate_ef_childtags_list function has error: ", current_row[col_name], e)
    return ef_childtags_list


def generate_ef_childtags_locationtype(current_row, element_list_name, element_address1, element_address2,
                                       element_city, element_state, element_country, element_postal_code, col_address1,
                                       col_address2,
                                       col_city, col_state, col_country, col_postal_code):
    try:
        ef_childtags_locationtype = etree.Element(element_list_name)

        ef_childtags_element_address1 = etree.Element(element_address1)
        ef_childtags_element_address1.text = current_row.get(col_address1).strip()

        ef_childtags_element_address2 = etree.Element(element_address2)
        ef_childtags_element_address2.text = current_row.get(col_address2).strip()

        ef_childtags_element_city = etree.Element(element_city)
        ef_childtags_element_city.text = current_row.get(col_city).strip()

        ef_childtags_element_state = etree.Element(element_state)
        ef_childtags_element_state.text = current_row.get(col_state).strip()

        ef_childtags_element_country = etree.Element(element_country)
        ef_childtags_element_country.text = current_row.get(col_country).strip()

        ef_childtags_element_postal_code = etree.Element(element_postal_code)
        ef_childtags_element_postal_code.text = current_row.get(col_postal_code).strip()

        if ef_childtags_element_address1.text != '':
            ef_childtags_locationtype.append(ef_childtags_element_address1)
        if ef_childtags_element_address2.text != '':
            ef_childtags_locationtype.append(ef_childtags_element_address2)
        if ef_childtags_element_city.text != '':
            ef_childtags_locationtype.append(ef_childtags_element_city)
        if ef_childtags_element_state.text != '':
            ef_childtags_locationtype.append(ef_childtags_element_state)
        if ef_childtags_element_country.text != '':
            ef_childtags_locationtype.append(ef_childtags_element_country)
        if ef_childtags_element_postal_code.text != '':
            ef_childtags_locationtype.append(ef_childtags_element_postal_code)

    except Exception as e:
        log.info("generate_ef_childtags_locationtype function has error: ", current_row[col_address1], current_row[col_address2],
                 current_row[col_city], e)

    return ef_childtags_locationtype


def generate_ef_employee_customfields(current_row, csv_data_custom_fields):

    candidate_custom_rowtoxml_tree = etree.Element('custom_info')
    # loop through each row from csvData_Position
    for custom_field_row in range(len(csv_data_custom_fields)):

        if current_row['EMPLOYEE_ID'] == csv_data_custom_fields[custom_field_row]['EMPLOYEE_ID']:
            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'PERFORMANCE_RATING_1', 'noLowercase')
            if ef_t_tag_field_value.text != '':
                employee_performance_rating_1 = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'performance_rating_1')
                if ef_t_tag.text != '':
                    employee_performance_rating_1.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'string')
                if ef_t_tag.text != '':
                    employee_performance_rating_1.append(ef_t_tag)

                employee_performance_rating_1.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_performance_rating_1)

            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'PERFORMANCE_RATING_2', 'noLowercase')
            if ef_t_tag_field_value.text != '':

                employee_performance_rating_2 = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'performance_rating_2')
                if ef_t_tag.text != '':
                    employee_performance_rating_2.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'string')
                if ef_t_tag.text != '':
                    employee_performance_rating_2.append(ef_t_tag)

                employee_performance_rating_2.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_performance_rating_2)

            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'PERFORMANCE_RATING_3', 'noLowercase')
            if ef_t_tag_field_value.text != '':

                employee_performance_rating_3 = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'performance_rating_3')
                if ef_t_tag.text != '':
                    employee_performance_rating_3.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'string')
                if ef_t_tag.text != '':
                    employee_performance_rating_3.append(ef_t_tag)

                employee_performance_rating_3.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_performance_rating_3)

            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'REVIEW_DATE1', 'noLowercase')
            if ef_t_tag_field_value.text != '':

                employee_review_date_1 = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'review_date_1')
                if ef_t_tag.text != '':
                    employee_review_date_1.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'string')
                if ef_t_tag.text != '':
                    employee_review_date_1.append(ef_t_tag)

                employee_review_date_1.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_review_date_1)

            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'REVIEW_DATE2', 'noLowercase')
            if ef_t_tag_field_value.text != '':

                employee_review_date_2 = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'review_date_2')
                if ef_t_tag.text != '':
                    employee_review_date_2.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'string')
                if ef_t_tag.text != '':
                    employee_review_date_2.append(ef_t_tag)

                employee_review_date_2.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_review_date_2)

            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'REVIEW_DATE3', 'noLowercase')
            if ef_t_tag_field_value.text != '':

                employee_review_date_3 = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'review_date_3')
                if ef_t_tag.text != '':
                    employee_review_date_3.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'string')
                if ef_t_tag.text != '':
                    employee_review_date_3.append(ef_t_tag)

                employee_review_date_3.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_review_date_3)

            ef_t_tag_field_value = generate_ef_childtags(csv_data_custom_fields[custom_field_row],
                                                         'field_value', 'HEADCOUNT', 'noLowercase')
            if ef_t_tag_field_value.text != '':

                employee_head_count = etree.Element('custom_field')

                ef_t_tag = generate_ef_fieldname_tags('field_name', 'head_count')
                if ef_t_tag.text != '':
                    employee_head_count.append(ef_t_tag)

                ef_t_tag = generate_ef_fieldname_tags('data_type', 'int')
                if ef_t_tag.text != '':
                    employee_head_count.append(ef_t_tag)

                employee_head_count.append(ef_t_tag_field_value)
                candidate_custom_rowtoxml_tree.append(employee_head_count)

    return candidate_custom_rowtoxml_tree



# This function holds & build all position xml columns for the customer "SSI"
def experience_field_names(current_applicant):

    current_applicant = current_applicant
    element_application_list = etree.Element('experience_list')


    for current_candidate_row in range(len(current_applicant)):

        current_row = current_applicant[current_candidate_row]

        converted_rowtoxml = etree.Element('experience')

        ef_t_tag = generate_ef_childtags(current_row, 'company', 'COMPANY', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        ef_t_tag = generate_ef_childtags(current_row, 'title', 'TITLE', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        ef_t_tag = generate_ef_childtags(current_row, 'description', 'DESCRIPTION', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        ef_t_tag = generate_ef_childtags(current_row, 'location', 'LOCATION', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        ef_t_tag = generate_ef_childtags(current_row, 'is_current', 'IS_CURRENT', 'Lowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        ef_t_tag = generate_ef_childtags(current_row, 'start_date', 'START_DATE', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        ef_t_tag = generate_ef_childtags(current_row, 'end_date', 'END_DATE', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)

        element_application_list.append(converted_rowtoxml)

    return element_application_list



def employee_field_names(current_employee_row):
    current_row = current_employee_row
    converted_rowtoxml = etree.Element('EF_Employee')
    ef_tag_custom = etree.Element('custom_info')


    ef_t_tag = generate_ef_childtags(current_row, 'employee_id', 'EMPLOYEE_ID', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_tTag = generate_ef_childtags_parm('group_id', 'volkscience.com')
    if (ef_tTag.text != ''):
        converted_rowtoxml.append(ef_tTag)


    ef_tTag = generate_ef_childtags_parm('system_id', 'volkscience')
    if (ef_tTag.text != ''):
        converted_rowtoxml.append(ef_tTag)



    ef_t_tag = generate_ef_childtags_dt(current_row, 'last_activity_ts', 'LAST_ACTIVITY_TS')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)


    if current_row.get('PREFERRED_FIRST_NAME'):
        
        ef_t_tag = generate_ef_childtags(current_row, 'first_name', 'PREFERRED_FIRST_NAME', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)
    
    else:
        
        ef_t_tag = generate_ef_childtags(current_row, 'first_name', 'FIRST_NAME', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)
        
    
    if current_row.get('PREFERRED_LAST_NAME'):
        
        ef_t_tag = generate_ef_childtags(current_row, 'last_name', 'PREFERRED_LAST_NAME', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)
    
    
    else:
        ef_t_tag = generate_ef_childtags(current_row, 'last_name', 'LAST_NAME', 'noLowercase')
        if ef_t_tag.text != '':
            converted_rowtoxml.append(ef_t_tag)
        

    ef_t_tag = generate_ef_childtags_list_email(current_row)
    if ef_t_tag :
        converted_rowtoxml.append(ef_t_tag)
    else:
        return
    

    ef_t_tag = generate_ef_childtags(current_row, 'company_name', 'COMPANY_NAME', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'title', 'TITLE', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags_small_dt(current_row, 'hiring_date', 'HIRING_DATE')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags_small_dt(current_row, 'role_change_date', 'CURRENT_ROLE_START_DATE')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'level', 'JOB_LEVEL', 'noLowercase')
    if ef_t_tag is not None and ef_t_tag.text:
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'manager_userid', 'MANAGER_ID', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'manager_email', 'MANAGER_EMAIL', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'manager_fullname', 'MANAGER_FULLNAME', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'business_unit', 'BUSINESS_UNIT', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    generate_empty_xml_tag(converted_rowtoxml, 'termination_date', current_row['TERMINATION_DATE'])


    if current_row['PHONE'].strip() != '':
        ef_t_tag = generate_ef_childtags_list(current_row, 'phone_list', 'phone', 'PHONE')
        converted_rowtoxml.append(ef_t_tag)

    ef_tag = generate_ef_childtags(current_employee_row, 'location', 'LOCATION', 'noLowercase')
    converted_rowtoxml.append(ef_tag)
    if current_row.get('EF_CUSTOM_JOB_CODE'):
        ef_tag = get_tag_custom(ef_tag_custom, current_row['EF_CUSTOM_JOB_CODE'], 'ef_custom_job_code')
        
    
    if current_row.get('EFCUSTOM_TEXT_SUB_DEPT'):
        ef_tag = get_tag_custom(ef_tag_custom, current_row['EFCUSTOM_TEXT_SUB_DEPT'], 'efcustom_text_sub_dept')
        
    if current_row.get('EFCUSTOM_TEXT_SUB_DEPT2'):
        ef_tag = get_tag_custom(ef_tag_custom, current_row['EFCUSTOM_TEXT_SUB_DEPT2'], 'efcustom_text_sub_dept2')
    
    if ef_tag_custom:
        converted_rowtoxml.append(ef_tag_custom)
    ef_t_tag = generate_ef_childtags(current_row, 'job_code', 'JOB_CODE', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    ef_t_tag = generate_ef_childtags(current_row, 'employee_type', 'EMPLOYEE_TYPE', 'noLowercase')
    if ef_t_tag.text != '':
        converted_rowtoxml.append(ef_t_tag)

    return converted_rowtoxml


# Experience Map
def create_exp_map(employee_exp_filename):
    dict_exp = {}
    csv.field_size_limit(sys.maxsize)
    with open(employee_exp_filename, mode='rb') as csv_data_experience:
        exp_list = list(csv.DictReader(csv_data_experience, delimiter='|'))

    for index in range(len(exp_list)):
        cell_value_class = str(exp_list[index]['EMPLOYEE_ID'])
        if cell_value_class:
            if cell_value_class in dict_exp:
                get_value = dict_exp.get(cell_value_class)
                get_value.append(index)
                dict_exp.update({cell_value_class: get_value})
            else:
                set_value = []
                set_value.append(index)
                dict_exp.update({cell_value_class: set_value})

    # return dict_exp
    exp_map = {}
    exp_map['dict'] = dict_exp
    exp_map['list'] = exp_list

    return exp_map


# customfield Map
def create_customfield_map(employee_custom_filename):
    dict_custom_field = {}
    csv.field_size_limit(sys.maxsize)
    with open(employee_custom_filename, mode='rb') as csv_data_custom_field:
        customfield_list = list(csv.DictReader(csv_data_custom_field, delimiter='|'))

    for index in range(len(customfield_list)):
        cell_value_class = str(customfield_list[index]['EMPLOYEE_ID'])
        if cell_value_class:
            if cell_value_class in dict_custom_field:
                get_value = dict_custom_field.get(cell_value_class)
                get_value.append(index)
                dict_custom_field.update({cell_value_class: get_value})
            else:
                set_value = []
                set_value.append(index)
                dict_custom_field.update({cell_value_class: set_value})

    # return dict_app
    customfield_map = {}
    customfield_map['dict'] = dict_custom_field
    customfield_map['list'] = customfield_list

    return customfield_map

def build_and_write_xml(employee_filename, output_file):

    csv.field_size_limit(sys.maxsize)
    with open(employee_filename, mode='r+', encoding='utf-8') as custom_field_row:
        custom_field_row = list(csv.DictReader(custom_field_row, delimiter=','))

    # Open XML file for writing
    produce_xml_file = open(output_file, mode='w')
    ef_xmltags = etree.Element('EF_Employee_List')

    dupes = []
    dupes_cnt = 0

    # loop through each row from custom_field_row
    for current_row in range(len(custom_field_row)):
        # print("current row: ", current_row)
        emp_id = custom_field_row[current_row]['EMPLOYEE_ID']
        if emp_id not in dupes:
            dupes.append(emp_id)
            log.info('Processing', current_row, ' of ', len(custom_field_row))
            current_xml_employee = employee_field_names(custom_field_row[current_row])
            if current_xml_employee:
                ef_xmltags.append(current_xml_employee)
            else:
                continue

        else:
            dupes_cnt = dupes_cnt + 1
    # print(EMAILS)
    if ef_xmltags != '':
        log.info('Number of elements is %s', len(ef_xmltags))
        ef_xmltags = etree.tostring(ef_xmltags, pretty_print=True).decode("utf-8")
        produce_xml_file.write(ef_xmltags)
        produce_xml_file.close()

    log.info("Duplicates employee ids found: {0}".format(dupes_cnt))
    log.info("Duplicates employee emails found: {0}".format(dupe_email_count))


def transform(employee_filename, output_file):

    '''' This is the main method that builds the data map for adjacent tables. And builds xml in a streaming way.'''
    now = dt.datetime.now()
    log.info('Starting building Employee xml')
    log.info('START TIME', now.strftime('%Y-%m-%d %H:%M:%S'))

    build_and_write_xml(employee_filename, output_file)

    now = dt.datetime.now()
    log.info('END TIME', now.strftime('%Y-%m-%d %H:%M:%S'))


def main():
    parser = argparse.ArgumentParser(description='Convert Candidate CSV File to Candidate XML.')
    parser.add_argument('--input_file', help='input Employee file', dest='input_file')
    parser.add_argument('--output_file', help='output Employee xml file', dest='output_file')

    args = parser.parse_args()
    log.info(args)
    print(args.input_file)
    with open(args.input_file, 'r') as fp:
        config_json = fp.read()

        log.info(config_json)
        config_dict = json.loads(config_json)
        employee_filename = config_dict.get('employee_filename')
        if not employee_filename:
            log.info('Employee file name is not shared in the employee_filename Argument')
            sys.exit(1)

        transform(employee_filename, args.output_file)

if __name__ == '__main__':
    main()
