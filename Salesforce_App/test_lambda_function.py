from lambda_function import app_handler

event = {'app_settings': {"instance_url": "https://eightfold.my.salesforce.com",
                         "business_unit_to_query_info": {
                            'SALES': {
                                'current_quarter_opportunity_query': "select id,name,closeDate,amount,owner.Name from opportunity where (owner.email='{{ employeeEmail }}' OR owner.manager.email='{{ employeeEmail }}' OR owner.manager.manager.email='{{ employeeEmail }}' OR owner.manager.manager.manager.email='{{ employeeEmail }}' OR owner.manager.manager.manager.manager.email='{{ employeeEmail }}') AND StageName != '7. Closed Lost' AND CloseDate = THIS_FISCAL_QUARTER order by closedate DESC",
                                'last_quarter_won_query': "select id,name,closeDate,amount,owner.Name from opportunity where (owner.email='{{ employeeEmail }}' OR owner.manager.email='{{ employeeEmail }}' OR owner.manager.manager.email='{{ employeeEmail }}' OR owner.manager.manager.manager.email='{{ employeeEmail }}' OR owner.manager.manager.manager.manager.email='{{ employeeEmail }}') AND StageName = '7. Closed Won' AND CloseDate = LAST_FISCAL_QUARTER order by closedate DESC",
                                'variable_name': 'employeeEmail'},
                            'MARKETING': {
                                "query": "select id, Company, status, CreatedDate from lead where owner.email='{{ employeeEmail }}' and status = 'working' and CreatedDate = THIS_FISCAL_QUARTER order by CreatedDate DESC",
                                'variable_name': 'employeeEmail'},
                            'PROFESSIONAL SERVICES': {
                                "query": "select id, MPM4_BASE__Account__r.name,Overall_Project_Status__c,MPM4_BASE__Deadline__c from MPM4_BASE__Milestone1_Project__c where owner.email='{{ employeeEmail }}' AND MPM4_BASE__Kickoff__c < today AND MPM4_BASE__Deadline__c > today order by MPM4_BASE__Deadline__c DESC",
                                'variable_name': 'employeeEmail'}
                            }
                        },
        'request_data': {'email': 'jgriggs@eightfold.ai',
                         'business_unit': 'SALES',
                         'firstname': 'Jeff',
                         'fullname': 'Jeff Griggs',
                         'oauth_toke': '<FIX_ME>'}
        #'request_data': {'email': 'ewoodley@eightfold.ai',
        #                 'business_unit': 'Marketing',
        #                 'firstname': 'Emily',
        #                 'fullname': 'Emily Woodley'}
        #'request_data': {'email': 'epalacios@eightfold.ai',
        #'request_data': {'email': 'cturner@eightfold.ai',
        #                 'business_unit': 'PROFESSIONAL SERVICES',
        #                 'firstname': 'Thoma',
        #                 'fullname': 'Thomas Delaporte'}
       }
data = app_handler(event, {})
print(data)
