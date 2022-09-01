"""
    Existing Packages
"""
from pytesseract import image_to_string

"""
    Proprietary Packages
"""
import AuditCases.CompareResults as CompResult

def Main(json_return, img_roi, expect_value):
    try:
        text_extract = image_to_string(img_roi, lang='eng+NewsGothic')
        print("Actual value: None".format(text_extract))
        if expect_value is not None:
            CompResult.Compare_Y_or_N(json_return, text_extract, expect_value, "Address Line 3")
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'AA_line3.Main()'. Error: {}".format(str(e))
