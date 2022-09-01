def Compare_Y_or_N(json_return, returned_data, expect_value):
    try:
        #print("Exp: " + expect_value)
        #print("Act: " + returned_data)
        if expect_value not in returned_data:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'Compare_Y_or_N({})'. Error: Values do not match".format(expect_value)
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'Compare_Y_or_N()'. Error: {}".format(str(e))
