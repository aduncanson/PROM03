"""
    Existing Packages
"""
from jsonschema import validate

"""
    Proprietary Packages
"""
# N/A

"""
    An existing template called 'schema' of how each data field should be formatted is compared against the database data
    If they match, return and pass onto the next stage
    If they do not match, return and show error message
"""
def validate_json(json_return, db_data):
    try:
        # Extract expected number of pages for CCA
        total_pages = db_data["page_meta_data"]["total_pages"]
        # Empty QR dictionary to be populated later
        qr_properties_dict = {}
        # Empty QR list to be populated later
        qr_properties_arr = []

        # All QRs require the same format, but may be dynamic in volume so loop over QR count
        for i in range(1, total_pages):
            qr_properties_dict[str(i)] = {
                "type" : "object",
                "properties" : {
                    "x_pos" : {"type": "integer"},
                    "y_pos" : {"type": "integer"},
                    "width" : {"type": "integer"},
                    "height" : {"type": "integer"}
                },
                "required" : ["x_pos", "y_pos", "width", "height"],
            }
            qr_properties_arr.append(str(i))

        # All meta data has same format, so template made for reuse
        meta_dict = {
            "type" : "object",
            "properties" : {
                "page" : {"type" : "integer"},
                "x_pos" : {"type" : "integer"},
                "y_pos" : {"type" : "integer"},
                "width" : {"type" : "integer"},
                "height" : {"type" : "integer"},
            },
            "required": ["page", "x_pos", "y_pos", "width", "height"],
        }

        # Main schema template
        schema = {
            "type" : "object",
            "properties" : {
                "contract_number" : {
                    "type" : "string",
                    "minLength" : 12,
                    "maxLength" : 12,
                    "pattern" : "[0-9]{12}",
                },
                "name" : {"type" : "string"},
                "address" : {
                    "type" : "object",
                    "properties" : {
                        "line1" : {"type" : "string"},
                        "line2" : {"type" : "string"},
                        "line3" : {"type" : ["string", "null"]},
                        "line4" : {"type" : ["string", "null"]},
                        "line5" : {"type" : ["string", "null"]},
                        "post_code" : {"type" : "string"},
                    },
                    "required": ["line1", "line2", "post_code"],
                },
                "sort_code" : {
                    "type" : "string",
                    "minLength" : 6,
                    "maxLength" : 6,
                    "pattern" : "[0-9]{6}",
                },
                "account_number" : {
                    "type" : "string",
                    "minLength" : 8,
                    "maxLength" : 8,
                    "pattern" : "[0-9]{6}",
                },
                "account_name" : {"type" : "string"},
                "total_amount" : {
                    "type" : "string",
                    "minLength" : 5,
                    "maxLength" : 10,
                    "pattern" : "^\£(\d{1,3}(\,\d{3})*|(\d+))(\.\d{2})?$",
                },
                "effective_date" : {
                    "type" : "string",
                    "minLength" : 11,
                    "maxLength" : 11,
                    "pattern" : "[0-9]{2} [A-Z][a-z]{2} [0-9]{4}",
                },
                "image_name" : {
                    "type" : "string",
                },
                "page_meta_data" : {
                    "type" : "object",
                    "properties" : {
                        "total_pages" : {"type" : "integer"},
                        "qr" : {
                            "type" : "object",
                            "properties" : qr_properties_dict,
                            "required": qr_properties_arr,
                        },
                        "address" : {
                            "type" : "object",
                            "properties" : {
                                "line1" : meta_dict,
                                "line2" : meta_dict,
                                "line3" : meta_dict,
                                "line4" : meta_dict,
                                "line5" : meta_dict,
                                "post_code" : meta_dict,
                            },
                            "required": ["line1", "line2", "post_code"],
                        },
                        "name" : meta_dict,
                        "sort_code" : meta_dict,
                        "account_number" : meta_dict,
                        "account_name" : meta_dict,
                        "total_amount" : meta_dict,
                        "ddm_signature" : meta_dict,
                        "cca_signature" : meta_dict,
                    },
                    "required": ["total_pages", "qr", "address", "name", "sort_code", "account_number", "account_name", "total_amount", "ddm_signature", "cca_signature"],
                },
            },
            "required": ["contract_number", "name", "address", "sort_code", "account_number", "account_name", "total_amount", "effective_date", "image_name", "page_meta_data"],
        }

        try:
            # Actual validation occurs
            validate(instance=db_data, schema=schema)
        except Exception as e:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'validate_json(), validation failed'. Error: {}".format(str(e))

    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'validate_json()'. Error: {}".format(str(e))

"""
    An existing template called 'schema' of how each QR embedded text should be formatted is compared against the actual QR embedded text
    If they match, return and pass onto the next stage
    If they do not match, return and show error message
"""
def validateList(json_return, text_list, db_data):
    try:
        if len(text_list) != 3:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'validateList()'. Error: Must have 3 elements"
            
            return
        total_pages = db_data["page_meta_data"]["total_pages"]
        text_dict = {}
        text_dict["lan"] = text_list[0]
        text_dict["copy"] = text_list[1]
        text_dict["page"] = int(text_list[2])

        # Main schema template
        schema = {
            "type" : "object",
            "properties" : {
                "lan" : {
                    "type" : "string",
                    "minLength" : 12,
                    "maxLength" : 12,
                    "pattern" : "[0-9]{12}",
                },
                "copy" : {
                    "type" : "string",
                    "minLength" : 1,
                    "maxLength" : 1,
                    "pattern" : "B|C",
                },
                "page" : {
                    "type" : "integer",
                    "minimum" : 1,
                    "maximum" : total_pages,
                },
            },
            "required": ["lan", "copy", "page"],
        }
        try:
            # Actual validation occurs
            validate(instance=text_dict, schema=schema)
        except Exception as e:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'validateList(), validation failed'. Error: {}".format(str(e))
        
        return text_dict
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'validateList()'. Error: {}".format(str(e))
        return None