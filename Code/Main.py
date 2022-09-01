"""
    Existing Packages
"""
import sys
from datetime import datetime
startTime = datetime.now()

"""
    Proprietary Packages
"""
import Database
import Validate
import QRFinder

"""
    Calls the Database packages to check the LAN passed exists on the database
    If so, pass on to Validation step
    If not, end and return error message
"""
def query_db_for_record(detected_client_id):
    try:
        # return object
        json_return = {
            "response": None,
            "result": None
        }
        
        # Check if record exists on database
        db_data_result = Database.request_data_from_db(json_return, detected_client_id)
        if json_return["response"] is not None:
            return json_return

        # Pass to validation step
        validate_json(json_return, db_data_result)
        if json_return["response"] is not None:
            return json_return

        # Pass to QR finding step (intermediary step to handle error)
        json_return["response"] = "Pass"
        
        return json_return
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'query_db_for_record()'. Error: {}".format(str(e))
        
        return json_return

"""
    Determines if the data returned by the database is in the expected format
    If so, pass on to Page scanning/QR finding step
    If not, end and return error message
"""
def validate_json(json_return, db_data):
    try:
        # Check if data is in expected format
        Validate.validate_json(json_return, db_data)
        if json_return["response"] is not None:
            return

        # Pass to QR finding step (intermediary step to handle error)
        qr_finder_image_morph(json_return, db_data)
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'validate_json()'. Error: {}".format(str(e))

"""
    Passes to the QR finding and page scanning package
    Used as an intermediary step to handle any errors and help debugging
"""
def qr_finder_image_morph(json_return, db_data):
    try:
        # Calls the QR Finding package passing LAN and database data
        QRFinder.image_page_looper(json_return, db_data)
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'qr_finder_image_morph()'. Error: {}".format(str(e))

"""
    Only execute functionality if the function is directly called
"""
if __name__ == "__main__":
    print(query_db_for_record(sys.argv[1]))
    print(datetime.now() - startTime)
