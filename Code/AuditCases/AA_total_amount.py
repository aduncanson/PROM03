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
        text_extract = image_to_string(img_roi, lang='eng+NewsGothic', config='-c tessedit_char_whitelist=£,.0123456789')
        print("Actual value: {}".format(text_extract))
        CompResult.Compare_Y_or_N(json_return, text_extract, expect_value, "Total Amount")
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'AA_total_amount.Main()'. Error: {}".format(str(e))
