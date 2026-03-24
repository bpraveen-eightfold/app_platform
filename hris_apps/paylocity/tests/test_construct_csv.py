import lambda_function
import pandas as pd


if __name__ == '__main__':
    client_id = ''
    client_secret = ''
    company_id = ''
    email_domain = ''
    csv_file_name = 'employee_data'
    employee_types = []
    bu_mapping = {}
    override_entries = {}
    max_termination_days = 30

    pc = lambda_function.PaylocityConnector(company_id, client_id, client_secret, employee_types, bu_mapping, max_termination_days, override_entries)
    pc.get_employees()
    all_employees = pc.active_employee_ids + pc.terminated_employee_ids
    pc.get_employees_results(all_employees)

    employee_rows = []
    employee_ids = []

    for employee_id in all_employees:
        employee_details = pc.get_employee_details(employee_id)
        employee_row = pc.get_employee_row(employee_details, email_domain, employee_types)
        if not employee_row:
            print(f'Could not find employee_row for {employee_id}')
            continue
        employee_rows.append(employee_row)
        employee_ids.append(employee_id)

    df_all_employee_details = pd.DataFrame(employee_rows, columns=lambda_function.column_list, index=employee_ids)
    for employee_id, row in df_all_employee_details.iterrows():
        manager_id = row['MANAGER_ID']
        overrides = override_entries.get(employee_id, {})
        manager_fullname = ''
        manager_email = ''
        if manager_id and manager_id in df_all_employee_details.index:
            manager_details = df_all_employee_details.loc[manager_id]
            manager_fullname = '{}, {}'.format(manager_details['LAST_NAME'], manager_details['FIRST_NAME'])
            manager_email = manager_details['EMAIL']
        df_all_employee_details.loc[employee_id, 'MANAGER_FULLNAME'] = overrides.get('MANAGER_FULLNAME') or manager_fullname
        df_all_employee_details.loc[employee_id, 'MANAGER_EMAIL'] = overrides.get('MANAGER_EMAIL') or manager_email
    employee_filename = pc.generate_csv(df_all_employee_details, csv_file_name)
