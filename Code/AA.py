"""
    Existing Packages
"""
import cv2
import numpy as np

"""
    Proprietary Packages
"""
from AuditCases import *

"""
    Landing function for beginning auditting on screen
"""
def process_page(json_return, corrected_scan_image, page, db_data, new_corners, original_page, alterations_not_needed):
    try:
        # Copy object to not affect it future auditting
        page_meta_data = db_data["page_meta_data"].copy()
        del page_meta_data["total_pages"]
        page_qr = page_meta_data.pop("qr")[str(page)]
        # Extract address as it is a sub-dictionary
        address = page_meta_data.pop("address")
        # Find checks to be performed on each key-value as page location is stored on key-value level
        value_page_identifier(json_return, corrected_scan_image, page_meta_data, page, db_data, page_qr, new_corners, original_page, alterations_not_needed)
        # Repeat for address
        value_page_identifier(json_return, corrected_scan_image, address, page, db_data['address'], page_qr, new_corners, original_page, alterations_not_needed)
        
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'process_page()'. Error: {}".format(str(e))

def value_page_identifier(json_return, corrected_scan_image, dict_to_process, page, db_data, page_qr, new_corners, original_page, alterations_not_needed):
    try:
        for key, value in dict_to_process.items():
            if value["page"] == page:
                if "signature" in key: 
                    get_roi_for_element_no_expected(json_return, corrected_scan_image, page_qr, value, key, new_corners, page, original_page)
                    alterations_not_needed.append(page)
                else:
                    get_roi_for_element(json_return, corrected_scan_image, page_qr, value, key, db_data[key], new_corners)
                
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'value_page_identifier()'. Error: {}".format(str(e))

def get_roi_for_element(json_return, corrected_scan_image, qr_location, attribute_location, attribute_name, expect_value, new_corners):
    try:
        vert_border = 20
        hori_border = 40
        x_ratio = (attribute_location['x_pos'] - qr_location['x_pos']) / qr_location['width']
        y_ratio = (attribute_location['y_pos'] - qr_location['y_pos']) / qr_location['height']
        qx = int(new_corners['x_pos'] + new_corners['width'] * x_ratio) - hori_border
        qy = int(new_corners['y_pos'] + new_corners['height'] * y_ratio) - vert_border

        w_ratio = (attribute_location['x_pos'] + attribute_location['width'] - qr_location['x_pos']) / qr_location['width']
        h_ratio = (attribute_location['y_pos'] + attribute_location['height'] - qr_location['y_pos']) / qr_location['height']
        qw = int(new_corners['x_pos'] + new_corners['width'] * w_ratio) + hori_border
        qh = int(new_corners['y_pos'] + new_corners['height'] * h_ratio) + vert_border

        img_roi = corrected_scan_image[qy:qh, qx:qw]
        print("Field checked: {}".format(attribute_name))
        print("Expected value: {}".format(expect_value))
        eval("AuditCases.AA_{}.Main(json_return, img_roi, expect_value)".format(attribute_name))
        
        cv2.imshow('img_roi_{}'.format(attribute_name), img_roi)
        
        #print("-----------")
        #corrected_scan_image = cv2.resize(corrected_scan_image, None, fx=0.3, fy=0.3, interpolation=cv2.INTER_AREA)
        #cv2.imshow('img_roi_{}'.format(attribute_name), img_roi)
        
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'get_roi_for_element()'. Error: {}".format(str(e))

def get_roi_for_element_no_expected(json_return, corrected_scan_image, qr_location, attribute_location, attribute_name, new_corners, page, original_page):
    try:
        vert_border = 20
        hori_border = 40
        #print(new_corners)
        x_ratio = (attribute_location['x_pos'] - qr_location['x_pos']) / qr_location['width']
        y_ratio = (attribute_location['y_pos'] - qr_location['y_pos']) / qr_location['height']
        qx = int(new_corners['x_pos'] + new_corners['width'] * x_ratio) - hori_border
        qy = int(new_corners['y_pos'] + new_corners['height'] * y_ratio) - vert_border

        w_ratio = (attribute_location['x_pos'] + attribute_location['width'] - qr_location['x_pos']) / qr_location['width']
        h_ratio = (attribute_location['y_pos'] + attribute_location['height'] - qr_location['y_pos']) / qr_location['height']
        qw = int(new_corners['x_pos'] + new_corners['width'] * w_ratio) + hori_border
        qh = int(new_corners['y_pos'] + new_corners['height'] * h_ratio) + vert_border

        corrected_scan_image_copy = corrected_scan_image.copy()[0:original_page.shape[0], 0:original_page.shape[1]]
        
        img_roi = corrected_scan_image_copy[qy:qh, qx:qw]
        og_img_roi = original_page[qy:qh, qx:qw]
        
        img_roi_display = img_roi.copy()
        
        
        (thresh, bandwimage2) = cv2.threshold(img_roi, 240, 255, cv2.THRESH_BINARY)
        
        (thresh, bandwimage) = cv2.threshold(og_img_roi, 240, 255, cv2.THRESH_BINARY)
        
        diff = cv2.bitwise_xor(bandwimage2, bandwimage)
        diff = cv2.bitwise_not(diff)
        
        kernel = np.ones((3, 3), np.uint8)
        diff = cv2.dilate(diff, kernel)
        canny = cv2.Canny(diff, 50, 120)
        kernel = np.ones((23, 23), np.uint8)
        canny = cv2.morphologyEx(canny, cv2.MORPH_CLOSE, kernel)
        contours, hierarchy = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        diff_size = 0
        
        for c in contours:
            if cv2.contourArea(c) < 100:
                continue
            diff_size += 1
            hull = cv2.convexHull(c)
            cv2.drawContours(img_roi, [hull], 0, (0, 255, 0), 2)
        
        canny = cv2.resize(canny, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        diff = cv2.resize(diff, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        img_roi = cv2.resize(img_roi, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        img_roi_display = cv2.resize(img_roi_display, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        og_img_roi = cv2.resize(og_img_roi, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
        
        
        
        #cv2.imshow('receieved', img_roi_display)
        #cv2.imshow('sent', og_img_roi)
        #cv2.imshow('diff', diff)
        #cv2.imshow('canny', canny)
        cv2.imshow('img_roi_{}'.format(attribute_name), img_roi)
        
        if diff_size < 1:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'get_roi_for_element_no_expected()'. Error: No signature mark has been detected"
            return
        

        #cv2.waitKey(0)
        #cv2.destroyAllWindows()
        
        (thresh, bandwimage2) = cv2.threshold(corrected_scan_image_copy, 240, 255, cv2.THRESH_BINARY)
        
        (thresh, bandwimage) = cv2.threshold(original_page, 240, 255, cv2.THRESH_BINARY)
        
        diff = cv2.bitwise_xor(bandwimage2, bandwimage)
        diff = cv2.bitwise_not(diff)
        
        diff = cv2.rectangle(diff, (qx, qy), (qw, qh), (255, 255, 255), -1)
        
        kernel = np.ones((3, 3), np.uint8)
        diff = cv2.dilate(diff, kernel)
        canny = cv2.Canny(diff, 50, 120)
        kernel = np.ones((23, 23), np.uint8)
        canny = cv2.morphologyEx(canny, cv2.MORPH_CLOSE, kernel)
        contours, hierarchy = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        diff_size = 0
        
        for c in contours:
            if cv2.contourArea(c) < 100:
                continue
            diff_size += 1
            hull = cv2.convexHull(c)
            cv2.drawContours(corrected_scan_image_copy, [hull], 0, (0, 255, 0), 2)
        
        if diff_size > 0:
            cv2.imshow('img_roi_alteration', corrected_scan_image_copy)
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'get_roi_for_element_no_expected()'. Error: An alteration has been detected"
        
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'get_roi_for_element_no_expected()'. Error: {}".format(str(e))

def check_for_alterations(json_return, corrected_scan_image, original_page):
    try:
        (thresh, BW_scan_image) = cv2.threshold(corrected_scan_image, 240, 255, cv2.THRESH_BINARY)
        
        (thresh, BW_original_page) = cv2.threshold(cv2.resize(original_page, (corrected_scan_image.shape[1], corrected_scan_image.shape[0]), interpolation=cv2.INTER_AREA), 240, 255, cv2.THRESH_BINARY)
        
        diff = cv2.bitwise_xor(BW_scan_image, BW_original_page)
        diff = cv2.bitwise_not(diff)
        
        kernel = np.ones((3, 3), np.uint8)
        diff = cv2.dilate(diff, kernel)
        canny = cv2.Canny(diff, 50, 120)
        kernel = np.ones((23, 23), np.uint8)
        canny = cv2.morphologyEx(canny, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
        diff_size = 0
        for c in contours:
            if cv2.contourArea(c) < 100:
                continue
            diff_size += 1
            hull = cv2.convexHull(c)
            cv2.drawContours(corrected_scan_image, [hull], 0, (0, 255, 0), 4)
        if diff_size != 0:
            corrected_scan_image = cv2.resize(corrected_scan_image, None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)
            cv2.imshow('img_roi_alteration', corrected_scan_image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'check_for_alterations()'. Error: An alteration has been detected"

    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'check_for_alterations()'. Error: {}".format(str(e))