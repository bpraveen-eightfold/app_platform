import csv
import logging
from pprint import pprint as pp

KEYS = [
    'FIRST_NAME', 'LAST_NAME', 'FULL_NAME', 'PREFERRED_FIRST_NAME', 'EMAIL', 'HIRING_DATE', 'LOCATION', 'EMPLOYEE_ID', 'TITLE', 'JOB_LEVEL', 'BUSINESS_UNIT', 'CURRENT_ROLE_START_DATE',
    'TERMINATION_DATE', 'MANAGER_FULLNAME', 'MANAGER_EMAIL'
]


class Comparator:

    @classmethod
    def default(cls, orig, new):
        return str.__eq__(orig.upper(), new.upper())

    @classmethod
    def email(cls, old, new):
        h, g = old.split('@')[0].lower(), new.split('@')[0].lower()
        return h == g

    @classmethod
    def phone(cls, old, new):
        h = old.replace(' ', '')
        g = new.replace(' ', '')
        h1, g1 = h[1:] if h.startswith('+') else h, g[1:] if g.startswith('+') else g
        h1 = h1.replace('(', '').replace(')', '').replace('-', '')
        g1 = g1.replace('(', '').replace(')', '').replace('-', '')
        return h1 == g1

    @classmethod
    def location(cls, old, new):
        h, g = old.lower(), new.lower()
        if h == 'india' and g == 'ind - bangalore':
            g = 'india'
        return h == g

    def __init__(self):
        self.registered = {}

    def register(self, key, func):
        self.registered[key] = func

    def call_registered(self, key, a, b):
        return self.registered[key](a, b)

    def call_all_registered(self, orig, new):
        result = []
        for key in self.registered:
            if not self.call_registered(key, orig[key], new[key]):
                result.append([orig['FULL_NAME'], orig['EMPLOYEE_ID'], key, orig[key], new[key]])
        return result


def do_compare(origrows, genrows, gen_override_config=True):
    cmp = Comparator()
    cmp.register('FIRST_NAME', Comparator.default)
    cmp.register('LAST_NAME', Comparator.default)
    cmp.register('FULL_NAME', Comparator.default)
    cmp.register('PREFERRED_FIRST_NAME', Comparator.default)
    cmp.register('EMAIL', Comparator.email)
    cmp.register('HIRING_DATE', Comparator.default)
    cmp.register('LOCATION', Comparator.location)
    cmp.register('EMPLOYEE_ID', Comparator.default)
    cmp.register('TITLE', Comparator.default)
    cmp.register('JOB_LEVEL', Comparator.default)
    cmp.register('BUSINESS_UNIT', Comparator.default)
    cmp.register('CURRENT_ROLE_START_DATE', Comparator.default)
    cmp.register('TERMINATION_DATE', Comparator.default)
    cmp.register('MANAGER_FULLNAME', Comparator.default)
    cmp.register('MANAGER_EMAIL', Comparator.email)
    cmp.register('LOCATION', Comparator.location)
    cmp.register('PHONE', Comparator.phone)
    for k, v in genrows.items():
        if k not in origrows:
            logging.error('employee id {} does not exist in hr'.format(k))
    for k, v in origrows.items():
        if k not in origrows:
            logging.error('employee id {} does not exist in generated'.format(k))

    not_present_ids = []
    mismatch_rows = []
    for empid in origrows:
        if empid not in genrows:
            not_present_ids.append(empid)
            continue

    for empid, row in origrows.items():
        if empid not in genrows:
            not_present_ids.append(empid)
            continue
        diffs = cmp.call_all_registered(row, genrows[empid])
        for diff in diffs:
            mismatch_rows.append(diff)

    mismatch_rows = sorted(mismatch_rows, key=lambda x: x[2])
    with open('result.csv', 'w', newline='') as resultcsv:
        writer = csv.writer(resultcsv)
        writer.writerow(['employee_name', 'employee_id', 'field', 'orig', 'generated'])
        writer.writerows(mismatch_rows)

    with open('error.txt', 'w', encoding='utf_8') as errfile:
        errfile.write('Employee exist in HR but not Generated\n')
        errfile.write('\n'.join(not_present_ids))


def config(filepath: str):
    '''Get config from filepath csv
    
    :param filepath: path of diff file
    '''
    from collections import defaultdict
    config = defaultdict(lambda: defaultdict(str))
    with open(filepath, 'r') as f:
        for row in csv.DictReader(f):
            for k, v in row.items():
                print(80 * '~')
                print(k, '|', v)
                config[row['employee_id']][row['field']] = row['orig'] if row['choose'] == 'orig' else row['generated']
    print(80 * '#')
    print(config)
    import json
    import os
    outfile = os.path.splitext(filepath)[0] + '.json'
    with open(outfile, 'w') as f:
        json.dump(config, f, indent=4)


def readfiles(origfile: str, genfile: str):
    origrows = {}
    with open(origfile, 'r') as f:
        for row in csv.DictReader(f):
            origrows[row['EMPLOYEE_ID']] = row
    genrows = {}
    with open(genfile, 'r') as f:
        for row in csv.DictReader(f):
            genrows[row['EMPLOYEE_ID']] = row
    return origrows, genrows


def diffs(original: str, generated: str):
    """
    Compares the data given by hr and we generated via paylocity
    :param original: path of csv file provided by hr.
    :param generated: path of csv file generated by paylocity
    """
    origrows, genrows = readfiles(original, generated)
    do_compare(origrows, genrows)


import defopt


def main():
    """ 
    Compares the data given by hr and we generated via paylocity
    :param original: path of csv file provided by hr.
    :param generated: path of csv file generated by paylocity
    """
    defopt.run([diffs, config])


if __name__ == '__main__':
    main()
