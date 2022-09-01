"""
    Existing Packages
"""
import cx_Oracle
import OracleConfig
from json import loads as j_loads

"""
    Proprietary Packages
"""
# N/A

"""
    Directly queries the database calling an Oracle Function object preventing database structure being seen externally
"""
def request_data_from_db(json_return, client_id):
    try:
        # SQL to be called, pass in CLIENT_ID
        sql = "SELECT * FROM TABLE(GET_CCA_DATA_PTF('{}'))".format(client_id)

        # Expected format of results to be returned in
        data_dict = {'contract_number': None,
            'name': None,
            'address': {
                'line1': None,
                'line2': None,
                'line3': None,
                'line4': None,
                'line5': None,
                'post_code': None,
            },
            'sort_code': None,
            'account_number': None,
            'account_name': None,
            'total_amount': None,
            'effective_date': None,
            'page_meta_data': None,
            'image_name': None
        }

        # Connect to and query database
        with cx_Oracle.connect(
                    OracleConfig.username,
                    OracleConfig.password,
                    OracleConfig.dsn,
                    encoding=OracleConfig.encoding) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql)
                while True:
                    row = cursor.fetchone()
                    # If nothing is returned, stop connection
                    if row is None:
                        break
                    
                    # If data is returned, marry up fields to dictionary format
                    data_dict['contract_number'] = row[0]
                    data_dict['name'] = row[1]
                    data_dict['address']['line1'] = row[2]
                    data_dict['address']['line2'] = row[3]
                    data_dict['address']['line3'] = row[4]
                    data_dict['address']['line4'] = row[5]
                    data_dict['address']['line5'] = row[6]
                    data_dict['address']['post_code'] = row[7]
                    data_dict['sort_code'] = row[8]
                    data_dict['account_number'] = row[9]
                    data_dict['account_name'] = row[10]
                    data_dict['total_amount'] = row[11]
                    data_dict['effective_date'] = row[12]
                    data_dict['page_meta_data'] = j_loads(row[13].replace("'", "\""))
                    data_dict['image_name'] = row[14]
        return data_dict
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'request_data_from_db()'. Error: {}".format(str(e))
        return None
