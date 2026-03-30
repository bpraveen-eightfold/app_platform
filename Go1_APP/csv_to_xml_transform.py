import argparse
import csv
import datetime
import json
import sys
import xml.etree.ElementTree as ET

import glog as log


COURSE_URL_FORMAT = 'https://eightfoldai-dp.mygo1.com/play/{course_id}'
xml_tag_to_csv_field = {
    'lms_course_id': 'id',
    'title': 'title',
    'description': 'description',
    'course_type': 'content_type',
    'language': 'language',
    'image_url': 'image_url',
    'provider': 'portal',
}


def generate_xml_element(element_name, value):
    if not value:
        return None
    xml_element = ET.Element(element_name)
    xml_element.text = value.strip()
    return xml_element


def convert_csv_row_to_xml(row):
    row_xml = ET.Element('EF_Course')

    for xml_tag, csv_field in xml_tag_to_csv_field.items():
        xml_element = generate_xml_element(xml_tag, row.get(csv_field))
        if xml_element is not None:
            row_xml.append(xml_element)

    # duration_hours need conversion from minutes to hours
    duration_min = round(int(row.get('duration')) / 60, 2)
    xml_element = generate_xml_element('duration_hours', str(duration_min))
    if xml_element is not None:
        row_xml.append(xml_element)

    # course_url need to be constructed
    course_url = COURSE_URL_FORMAT.format(course_id=row.get('id'))
    xml_element = generate_xml_element('course_url', course_url)
    if xml_element is not None:
        row_xml.append(xml_element)

    return row_xml


def build_and_write_xml(input_file, output_file):
    csv.field_size_limit(sys.maxsize)

    with open(input_file, newline='') as courses_csv:
        rows = csv.DictReader(courses_csv, delimiter=',')
        ef_xmltags = ET.Element('EF_Course_List')
        dupes = []
        dupes_cnt = 0

        # loop through each row from custom_field_row
        for row in rows:
            course_id = row['id']
            if course_id not in dupes:
                dupes.append(course_id)
                row_xml = convert_csv_row_to_xml(row)
                ef_xmltags.append(row_xml)
            else:
                dupes_cnt = dupes_cnt + 1

    if ef_xmltags != '':
        # Open XML file for writing
        output_xml_file = open(output_file, mode='w')
        log.info('Number of elements is %s', len(ef_xmltags))
        ef_xmltags = ET.tostring(ef_xmltags).decode("utf-8")
        output_xml_file.write(ef_xmltags)
        output_xml_file.close()
    log.info("Duplicates found: {0}".format(dupes_cnt))


def transform(input_file, output_file):
    now = datetime.datetime.now()
    log.info('Starting building Employee xml')
    log.info('START TIME', now.strftime('%Y-%m-%d %H:%M:%S'))

    build_and_write_xml(input_file, output_file)

    now = datetime.datetime.now()
    log.info('END TIME', now.strftime('%Y-%m-%d %H:%M:%S'))


def main():
    parser = argparse.ArgumentParser(description='Convert Course CSV File to Course XML.')
    parser.add_argument('--input_file', help='input Course file', dest='input_file')
    parser.add_argument('--output_file', help='output Course xml file', dest='output_file')
    args = parser.parse_args()
    log.info(args)

    with open(args.input_file, 'r') as fp:
        config_json = fp.read()
        log.info(config_json)
        config_dict = json.loads(config_json)
        
        course_filename = config_dict.get('input_filename_prefix')
        
        if not course_filename:
            log.info('Course file name is not shared in the employee_filename Argument')
            sys.exit(1)

        transform(course_filename, args.output_file)


if __name__ == '__main__':
    main()
