import xml.etree.ElementTree as ET
from lxml import etree
from time import strftime, localtime, strptime
from datetime import datetime
import gnupg


def get_tag(element: str, value: str = '') -> ET.ElementTree:
    try:
        ef_tag = etree.Element(element)
        ef_tag.text = value
    except Exception:
        ef_tag = etree.Element(element)
        ef_tag.text = ""
    return ef_tag

def generate_xml_list(parent_tag, child_list_tag_element, child_tag_element, child_list_tag_value):
    if child_list_tag_value is not None:
        child_list_tag_value = child_list_tag_value.strip()
        if child_list_tag_value:
            child_list_tag = get_tag(child_list_tag_element)
            child_list_tag_value = child_list_tag_value.split(',')
            for child_tag_value in child_list_tag_value:
                generate_xml_tag(child_list_tag, child_tag_element, child_tag_value)
            parent_tag.append(child_list_tag)

def generate_xml_tag(parent_tag, child_tag_element, child_tag_value):
    if child_tag_value is not None:
        child_tag_value = child_tag_value.strip()
    child_tag = get_tag(child_tag_element, child_tag_value)
    parent_tag.append(child_tag)


def get_xml_str(data: ET.ElementTree) -> str:
    output_str = etree.tostring(data, encoding='utf-8', pretty_print=True).decode()
    return output_str

def generate_lang(data_rows, main_tag):
    for row in data_rows:
        ef_employee_tag = get_tag('employee')
        ef_language_proficiency_list_tag = get_tag('language_proficiency_list')
        ef_proficiency_list = get_tag('language_proficiency')
        generate_xml_list(ef_employee_tag, 'email_list', 'email', row[0])
        generate_xml_tag(ef_proficiency_list, 'language', row[1])
        generate_xml_tag(ef_proficiency_list, 'overall', row[2])

        ef_language_proficiency_list_tag.append(ef_proficiency_list)
        if len(ef_language_proficiency_list_tag):
            ef_employee_tag.append(ef_language_proficiency_list_tag)
        main_tag.append(ef_employee_tag)
        generate_xml_tag(ef_proficiency_list, 'language', row[1])

def write_to_file_exp(entity_field_data, result_filename_prefix, encryption_key, timestamp_format):
    date = datetime.now().date().strftime(timestamp_format)
    field_name = "EXPERIENCE"
    local_path = result_filename_prefix + field_name + '_' + date + ".xml"
    field_list = ["employeeId", "title", "work", "startTime", "endTime", "description", "location"]

    data_rows = []
    if entity_field_data:
        for key, values in entity_field_data.items():
            if values is None:
                continue
            if isinstance(values, str):
                data_rows.append([key, values])
            else:
                for value in values:
                    row = []
                    row.append(key)
                    for index in field_list[1:]:
                        row.append(value.get(index))
                    data_rows.append(row)

    main_tag = get_tag('employee_list')
    if entity_field_data:
        for key, values in entity_field_data.items():
            employee_tag = get_tag('employee')
            generate_xml_tag(employee_tag, 'employee_id', key)
            exp_list_tag = get_tag('experience_list')

            for value in values:
                exp_list = get_tag('experience')
                generate_xml_tag(exp_list, 'job_title', value.get('title'))
                generate_xml_tag(exp_list, 'job_company', value.get('work'))
                if value.get('startTime'):
                    generate_xml_tag(exp_list, 'start_date', datetime.fromtimestamp(value.get('startTime')).strftime('%m/%Y'))
                else:
                    generate_xml_tag(exp_list, 'start_date', "")
                if value.get('endTime'):
                    if value.get('isCurrent'):
                        generate_xml_tag(exp_list, 'end_date', "")
                    else:
                        generate_xml_tag(exp_list, 'end_date', datetime.fromtimestamp(value.get('endTime')).strftime('%m/%Y'))
                else:
                    generate_xml_tag(exp_list, 'end_date', "")
                generate_xml_tag(exp_list, 'resp_and_achiements', value.get('description'))
                generate_xml_tag(exp_list, 'job_location', value.get('location'))
                exp_list_tag.append(exp_list)

            if len(exp_list_tag):
                employee_tag.append(exp_list_tag)

            main_tag.append(employee_tag)

    output_xml_data = get_xml_str(main_tag)
    with open(local_path, 'w') as out:
        out.write(output_xml_data)

    if len(encryption_key):
        gpg = gnupg.GPG()
        import_result = gpg.import_keys(encryption_key)
        if import_result.count != 1:
            raise ValueError("Public Key import failed")
        key_id = import_result.fingerprints[0]
        key = gpg.list_keys().key_map[key_id]
        with open(local_path, 'rb') as f:
            local_path = local_path + ".pgp"
            status = gpg.encrypt_file(f, output=local_path, recipients="Eightfold_to_GDIT_PGPKeyPair", always_trust=True)
    return local_path


