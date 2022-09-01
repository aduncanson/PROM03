"""
    Existing Packages
"""
import numpy as np
import imutils
from pyzbar.pyzbar import decode
import cv2
import math


"""
    Proprietary Packages
"""
import Validate
import AA

# MM length for the individal squares that build up a QR code
qr_box_size = 10

"""
    Locates tiff image, loops through each page then subsequently checks for QRs then any specific auditing required for that page
"""
def image_page_looper(json_return, db_data):
    try:
        # Find tiff image
        scan_src_path = "received/{}.tiff".format(db_data["image_name"])
        scan_images = cv2.imreadmulti(scan_src_path, flags=cv2.IMREAD_GRAYSCALE)[1]
        
        original_src_path = "sent/{}.orig.tiff".format(db_data["image_name"])
        original_images = cv2.imreadmulti(original_src_path, flags=cv2.IMREAD_GRAYSCALE)[1]
        
        # List for pages that are checked for alterations during validation
        alterations_not_needed = []
        
        # List for page ordering of scanned images, in case they are out of order
        image_order = []
        
        # Check that all pages are returned as expected
        if len(scan_images) != db_data["page_meta_data"]["total_pages"]:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'image_page_looper()'. Error: Wrong number of pages returned"
            
            return

        # Loop through individual pages in tiff
        for i in range(0, db_data["page_meta_data"]["total_pages"]):
            scan_img = scan_images[i]
            
            # Find a QR on the image
            text, corrected_scan_image, new_corners = locate_qr_on_image(json_return, scan_img)
            
            if json_return["response"] is not None:
                return
                
            text_list = text.split("|")
            
            # Check the QR text is in the appropriate format
            text_dict = Validate.validateList(json_return, text_list, db_data)
            if json_return["response"] is not None:
                return

            # Check the QR text is as expected
            if text_dict["lan"] != db_data["contract_number"]:
                json_return["response"] = "Fail"
                json_return["result"] = "Failed at 'image_page_looper()'. Error: Wrong LAN detected on returned documentation."
                
                return
            if text_dict["copy"] != "B":
                json_return["response"] = "Fail"
                json_return["result"] = "Failed at 'image_page_looper()'. Error: Customer has not returned bank version of letter required."
                
                return
            
            # Get original page for reference
            original_page = original_images[text_dict["page"] - 1]
            
            AA.process_page(json_return, corrected_scan_image, text_dict["page"], db_data, new_corners, original_page, alterations_not_needed)
            if json_return["response"] is not None:
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return
            
            image_order.append(text_dict["page"])
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        # Check alterations on remaining pages
        for i in range(0, db_data["page_meta_data"]["total_pages"]):
            if (i + 1) not in alterations_not_needed:
                AA.check_for_alterations(json_return, scan_images[image_order.index(i + 1)], original_images[i])
                if json_return["response"] is not None:
                    return
        
        return
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'image_page_looper()'. Error: {}".format(str(e))
        
        return

"""
    Locates any QR codes on the page and re-orientates the pages to be upright and aligned properly
    Also determines the new coordinates of the corners of the QR code for audit purposes later
"""
def locate_qr_on_image(json_return, img):
    try:
        # Loop through all barcodes/QR codes on image
        det = cv2.QRCodeDetector()
        info, box_coordinates, _ = det.detectAndDecode(img)
        #print(info)

        if box_coordinates is None:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'locate_qr_on_image()'. Error: No QR Codes found"
            
            return None, None, None
        
        n = len(box_coordinates[0])
        for barcode in range(n):
            # Extract to data to string
            text = info
            # Find binding rectangle around QR code (orientated in x-y dimensions)
            polygon_Points = box_coordinates.astype(int)
            #print(polygon_Points)
            source_corners = polygon_Points[0]
            rect = cv2.minAreaRect(source_corners)
            
            # Find binding rectangle that exactly fits around QR code with no gaps
            img_crop, angle, og_qr_shape, M = crop_rect(json_return, img, rect, source_corners)
            # Resize image to expected size (21x21 unit QR code)
            img_rot_resized = cv2.resize(img_crop, (qr_box_size*21, qr_box_size*21))
        
        # Generate a sample image for the corners of a QR code where concentric squares reside, used to determine QR orientation
        pattern_finder_template = pattern_finder(json_return)

        # Expected positions of the populated corners
        corners = [[qr_box_size*14, qr_box_size*14], [qr_box_size*14, 0], [0, 0], [0, qr_box_size*14]]
        # List to hold value matching outcome
        corners_mag = [None, None, None, None]

        # Function to determine pattern matchings within an image based on sample image
        res = cv2.matchTemplate(img_rot_resized, pattern_finder_template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.75
        loc = np.where( res >= threshold)

        # Loop through each corner to find out how close it was to the nearest match
        for pt in zip(*loc[::-1]):
            for i in range(0, len(corners)):
                mag = math.sqrt((corners[i][0] - pt[0])**2 + (corners[i][1] - pt[1])**2)
                if corners_mag[i] is None:
                    corners_mag[i] = mag
                elif mag < corners_mag[i]:
                    corners_mag[i] = mag

        # Rotate image based on results of previous matcher to orientate the image to be upright
        rotate_val = corners_mag.index(max(corners_mag)) * 90
        img_final_qr = imutils.rotate_bound(img_rot_resized, rotate_val)
        img_temp = imutils.rotate_bound(img, rotate_val - angle)

        # Determine the new pixel locations of the corners of the QR code, needed for auditting later
        h, w = img.shape[:2]
        origin = (w/2, h/2)
        new_corners = rotate_corners(json_return, source_corners, np.radians(rotate_val - angle), origin, img_temp)
        
        if json_return["response"] is not None:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'locate_qr_on_image()'. Error: {}".format(str(e))
            
            return None, None, None


        # If the quality of the image is good, we should expect the results from the matcher to show one corner has a match far from the expected to location and the rest are close
        # If too many are found then we cannot determine the orientation and must fail the test
        h_new, w_new = img_temp.shape[:2]
        xoffset, yoffset = (w_new - w)/2, (h_new - h)/2

        distanced_corners = sum(1 for i in corners_mag if i > qr_box_size*7)
        if distanced_corners != 1:
            json_return["response"] = "Fail"
            json_return["result"] = "Failed at 'locate_qr_on_image()'. Error: Too many uncertain corners to determine orientation"
        return text, img_temp, new_corners
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'locate_qr_on_image()'. Error: {}".format(str(e))
        
        return None, None, None


"""
    Function to re-orientate the bounding rectangle around the QR code to remove empty space and make the fit as exact as possible
"""
def crop_rect(json_return, img, rect, source_corners):
    try:
        # get the parameter of the small rectangle
        center = rect[0]
        size = rect[1]
        angle = rect[2]
        center, size = tuple(map(int, center)), tuple(map(int, size))

        height, width = img.shape[0], img.shape[1]
        # Rotation matrix
        M = cv2.getRotationMatrix2D(center, angle, 1)
        # Apply warp to image based on matrix
        img_rot = cv2.warpAffine(img, M, (width, height))
        # Get new rectangle based on warped image
        img_crop = cv2.getRectSubPix(img_rot, size, center)

        return img_crop, angle, img_crop.shape, M
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'crop_rect()'. Error: {}".format(str(e))
        
        return None, None, None, None

"""
    The QR codes used have three corners populated with concentric squares. This function replicates those corners for pattern matching and determining the orientaion of the image
"""
def pattern_finder(json_return):
    try:
        # smallest square
        pattern_finder_1 = np.zeros((qr_box_size*3, qr_box_size*3), np.uint8)
        # medium square
        pattern_finder_2 = np.zeros((qr_box_size*5, qr_box_size*5), np.uint8)
        # largest square
        pattern_finder_2[:] = 255
        # nest squares within each other
        pattern_finder_2[qr_box_size:qr_box_size*4,qr_box_size:qr_box_size*4] = pattern_finder_1
        pattern_finder_3 = np.zeros((qr_box_size*7, qr_box_size*7), np.uint8)
        pattern_finder_3[qr_box_size:qr_box_size*6,qr_box_size:qr_box_size*6] = pattern_finder_2
        return pattern_finder_3
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'pattern_finder()'. Error: {}".format(str(e))
        
        return None

"""
    Function to determine the new pixel locations of the corners of the QR code, needed for auditting later
"""
def rotate_corners(json_return, pts, radians, origin, img_temp):
    try:
        new_corners = []
        for pt in pts:
            x, y = pt
            offset_x, offset_y = origin
            adjusted_x = (x - offset_x)
            adjusted_y = (y - offset_y)
            cos_rad = math.cos(radians)
            sin_rad = math.sin(radians)
            qx = int(offset_x + cos_rad * adjusted_x + sin_rad * adjusted_y)
            qy = int(offset_y + -sin_rad * adjusted_x + cos_rad * adjusted_y)
            new_corners.append([qx, qy])

        for corner in new_corners:
            if 'x_top' in locals():
                x_top = x_top if corner[0] > x_top else corner[0]
            else:
                x_top = corner[0]
            if 'x_bottom' in locals():
                x_bottom = x_bottom if corner[0] < x_bottom else corner[0]
            else:
                x_bottom = corner[0]

            if 'y_top' in locals():
                y_top = y_top if corner[1] > y_top else corner[1]
            else:
                y_top = corner[1]
            if 'y_bottom' in locals():
                y_bottom = y_bottom if corner[1] < y_bottom else corner[1]
            else:
                y_bottom = corner[1]

        return {'x_pos': x_top, 'y_pos': y_top, 'width': x_bottom - x_top, 'height': y_bottom - y_top}
    except Exception as e:
        json_return["response"] = "Fail"
        json_return["result"] = "Failed at 'rotate_corners()'. Error: {}".format(str(e))
        
        return None