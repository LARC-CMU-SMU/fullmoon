import xml.etree.ElementTree as ET
import numpy as np
import cv2


def get_coords_from_labelimg_xml(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    boxes = {}
    for obj in root.iter("object"):
        name = obj.find('name').text
        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        xmax = int(bndbox.find('xmax').text)
        ymin = int(bndbox.find('ymin').text)
        ymax = int(bndbox.find('ymax').text)
        boxes[name] = ((xmin, ymin), (xmax, ymax))
    return boxes


def get_mask(points, mask_size):
    pt1, pt2 = points
    mask = np.zeros(mask_size, np.uint8)
    cv2.rectangle(mask, pt1, pt2, [255, 255, 255], cv2.FILLED)
    return mask


def get_pixel_statics_for_bgr_image(m_image, m_mask):
    m_gray_image = cv2.cvtColor(m_image, cv2.COLOR_BGR2GRAY)
    m_mean, m_stddev = get_mean_and_stddev_from_gray_image_for_mask(m_gray_image, m_mask)
    m_mask_size = get_non_zero_pixels_for_mask(m_mask)
    m_min, m_max = get_min_max_from_gray_image_for_mask(m_gray_image, m_mask)
    m_hsv_image = cv2.cvtColor(m_image, cv2.COLOR_BGR2HSV)
    get_mean_and_stddev_from_hsv_image_for_mask(m_hsv_image, m_mask)
    return {
        'mean': m_mean,
        'stddev': m_stddev,
        'mask_size': m_mask_size,
        'min': m_min,
        'max': m_max
    }


def get_mean_and_stddev_from_hsv_image_for_mask(img, mask):
    m_mean, m_stddev = cv2.meanStdDev(img, mask=mask)
    print("mean", m_mean)
    print("stddev", m_stddev)


def get_mean_and_stddev_from_gray_image_for_mask(img, mask):
    m_mean, m_stddev = cv2.meanStdDev(img, mask=mask)
    return m_mean[0][0], m_stddev[0][0]


def get_min_max_from_gray_image_for_mask(m_image, m_mask):
    m_min, m_max, _, _ = cv2.minMaxLoc(m_image, mask=m_mask)
    return m_min, m_max


def get_non_zero_pixels_for_mask(mask):
    return cv2.countNonZero(mask)
