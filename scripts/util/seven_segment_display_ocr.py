# -*- coding:utf-8 -*-

import cv2
import numpy as np

from util.file_util import write_dictionary_to_csv_file, get_files_with_file_type_from_dir_starting_with
from util.image_util import get_warp_applied_image
from util.util import is_valid_lux_reading

FILE_TYPE = "jpg"

DIGITS_LOOKUP = {
    (1, 1, 1, 1, 1, 1, 0): 0,
    (1, 1, 0, 0, 0, 0, 0): 1,
    (1, 0, 1, 1, 0, 1, 1): 2,
    (1, 1, 1, 0, 0, 1, 1): 3,
    (1, 1, 0, 0, 1, 0, 1): 4,
    (0, 1, 1, 0, 1, 1, 1): 5,
    (0, 1, 1, 1, 1, 1, 1): 6,
    (1, 1, 0, 0, 0, 1, 0): 7,
    (1, 1, 1, 1, 1, 1, 1): 8,
    (1, 1, 1, 0, 1, 1, 1): 9
    # (0, 0, 0, 0, 0, 1, 1): '-'
}
H_W_Ratio = 1.9
SSD_READING_THRESHOLD_DEFAULT = 75
arc_tan_theta = 6.0


# below values needs to be manually adjusted depending on the image size
line_width = 4
digit_height_threshold = 30
black_threshold = 1000

# img_path = '/media/kasun/b6473291-3674-4adc-bc71-f6c16459baf3/data/smart_building/2dec_20_lux/a/1576838335a.jpg'
img_folder_path = '/media/kasun/b6473291-3674-4adc-bc71-f6c16459baf3/data/smart_building/jan3/lux_cam/'
start_file = img_folder_path+'1578046619a.jpg'
error_file = img_folder_path+'errors.err'

SHOW_DEBUG_IMAGE = 1
failed = 0
wait_key_time_out = 10
results=[]
result_file_name=img_folder_path+'lux_readings.csv'


# convert to gray, apply warp, blur and threshold
def get_processed_image(m_image, threshold, show=False):
    m_image = cv2.cvtColor(m_image, cv2.COLOR_BGR2GRAY)
    # lux meter digits have a skew, so apply correction there
    m_image = get_warp_applied_image(m_image, [[7, 0], [114, 0], [0, 64], [109, 64]])
    m_image = cv2.GaussianBlur(m_image, (3, 3), 0)
    _, m_image = cv2.threshold(m_image, threshold, 255, cv2.THRESH_BINARY_INV)
    if show:
        cv2.imshow('1.processed_image', m_image)
    return m_image


def helper_extract(one_d_array, threshold=20):
    res = []
    flag = 0
    temp = 0
    for i, value in enumerate(one_d_array):
        if value < black_threshold:  # not 1(black) enough
            if flag > threshold:  # aha! got a digit (hopefully)
                start = i - flag
                end = i
                temp = end
                # if end - start > 20:  # digit is long enough, cool
                res.append((start, end))
            flag = 0  # set the trap again to capture another digit
        else:  # mostly 1, means mostly black
            flag += 1

    else:  # redundant else, since there is no break in matching for loop, execution will go in to this block anyways
        if flag > threshold:
            start = temp
            end = len(one_d_array)
            if end - start > 50:  # why this digit is longer?
                res.append((start, end))
    return res


def find_digits_positions(img, reserved_threshold=20):
    # cnts = cv2.findContours(img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # digits_positions = []
    # for c in cnts[1]:
    #     (x, y, w, h) = cv2.boundingRect(c)
    #     cv2.rectangle(img, (x, y), (x + w, y + h), (128, 0, 0), 2)
    #     cv2.imshow('test', img)
    #     cv2.waitKey(0)
    #     cv2.destroyWindow('test')
    #     if w >= reserved_threshold and h >= reserved_threshold:
    #         digit_cnts.append(c)
    # if digit_cnts:
    #     digit_cnts = contours.sort_contours(digit_cnts)[0]

    digits_positions = []
    img_array = np.sum(img, axis=0)
    horizon_position = helper_extract(img_array, threshold=line_width)
    img_array = np.sum(img, axis=1)
    vertical_position = helper_extract(img_array, threshold=digit_height_threshold)
    # make vertical_position has only one element (get the first and and last row y coordinates
    if len(vertical_position) > 1:
        vertical_position = [(vertical_position[0][0], vertical_position[len(vertical_position) - 1][1])]
    for h in horizon_position:  # build the actual digit positions
        for v in vertical_position:
            digits_positions.append(list(zip(h, v)))
    if len(digits_positions) < 0:
        print("Failed to find digits's positions")

    return digits_positions


# not in use
def recognize_digits_area_method(digits_positions, output_img, input_img):
    digits = []
    for c in digits_positions:
        x0, y0 = c[0]
        x1, y1 = c[1]
        roi = input_img[y0:y1, x0:x1]
        h, w = roi.shape
        suppose_W = max(1, int(h / H_W_Ratio))
        if w < suppose_W / 2:
            x0 = x0 + w - suppose_W
            w = suppose_W
            roi = input_img[y0:y1, x0:x1]
        width = (max(int(w * 0.15), 1) + max(int(h * 0.15), 1)) // 2
        dhc = int(width * 0.8)

        small_delta = int(h / arc_tan_theta) // 4
        segments = [
            # # version 1
            # ((w - width, width // 2), (w, (h - dhc) // 2)),
            # ((w - width - small_delta, (h + dhc) // 2), (w - small_delta, h - width // 2)),
            # ((width // 2, h - width), (w - width // 2, h)),
            # ((0, (h + dhc) // 2), (width, h - width // 2)),
            # ((small_delta, width // 2), (small_delta + width, (h - dhc) // 2)),
            # ((small_delta, 0), (w, width)),
            # ((width, (h - dhc) // 2), (w - width, (h + dhc) // 2))

            # # version 2
            ((w - width - small_delta, width // 2), (w, (h - dhc) // 2)),
            ((w - width - 2 * small_delta, (h + dhc) // 2), (w - small_delta, h - width // 2)),
            ((width - small_delta, h - width), (w - width - small_delta, h)),
            ((0, (h + dhc) // 2), (width, h - width // 2)),
            ((small_delta, width // 2), (small_delta + width, (h - dhc) // 2)),
            ((small_delta, 0), (w + small_delta, width)),
            ((width - small_delta, (h - dhc) // 2), (w - width - small_delta, (h + dhc) // 2))
        ]

        on = [0] * len(segments)

        for (i, ((xa, ya), (xb, yb))) in enumerate(segments):
            seg_roi = roi[ya:yb, xa:xb]
            total = cv2.countNonZero(seg_roi)
            area = (xb - xa) * (yb - ya) * 0.9
            print(total / float(area))
            if total / float(area) > 0.45:
                on[i] = 1

        if tuple(on) in DIGITS_LOOKUP.keys():
            digit = DIGITS_LOOKUP[tuple(on)]
        else:
            digit = '*'
        digits.append(digit)
        cv2.rectangle(output_img, (x0, y0), (x1, y1), (0, 128, 0), 2)
        cv2.putText(output_img, str(digit), (x0 - 10, y0 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 128, 0), 2)

    return digits


def recognize_digits_line_method(digits_positions, input_img, output_img):
    digits = []
    for c in digits_positions:
        x0, y0 = c[0]
        x1, y1 = c[1]
        roi = input_img[y0:y1, x0:x1]
        h, w = roi.shape
        suppose_W = max(1, int(h / H_W_Ratio))  # this helps detecting 1

        if x1 - x0 < 25 and cv2.countNonZero(roi) / ((y1 - y0) * (x1 - x0)) < 0.2:  # see how many black in int roi
            continue

        if w < suppose_W / 2:
            x0 = max(x0 + w - suppose_W, 0)
            roi = input_img[y0:y1, x0:x1]
            w = roi.shape[1]

        center_y = h // 2
        quater_y_1 = h // 4
        quater_y_3 = quater_y_1 * 3
        center_x = w // 2
        # line_width = 5  # line's width
        width = (max(int(w * 0.15), 1) + max(int(h * 0.15), 1)) // 2
        small_delta = int(h / arc_tan_theta) // 4
        segments = [
            ((w - 2 * width, quater_y_1 - line_width), (w, quater_y_1 + line_width)),
            ((w - 2 * width, quater_y_3 - line_width), (w, quater_y_3 + line_width)),
            ((center_x - line_width - small_delta, h - 2 * width), (center_x - small_delta + line_width, h)),
            ((0, quater_y_3 - line_width), (2 * width, quater_y_3 + line_width)),
            ((0, quater_y_1 - line_width), (2 * width, quater_y_1 + line_width)),
            ((center_x - line_width, 0), (center_x + line_width, 2 * width)),
            ((center_x - line_width, center_y - line_width), (center_x + line_width, center_y + line_width)),
        ]
        on = [0] * len(segments)

        for (i, ((xa, ya), (xb, yb))) in enumerate(segments):
            seg_roi = roi[ya:yb, xa:xb]
            total = cv2.countNonZero(seg_roi)
            area = (xb - xa) * (yb - ya) * 0.9
            if total / float(area) > 0.5:
                on[i] = 1
        if tuple(on) in DIGITS_LOOKUP.keys():
            digit = DIGITS_LOOKUP[tuple(on)]
        else:
            digit = '*'

        digits.append(digit)

        color = (0,0,0)

        # put the rectangles around digits, because we like some visual feedback
        if cv2.countNonZero(roi[h - int(3 * width / 4):h, w - int(3 * width / 4):w]) / (9. / 16 * width * width) > 0.65:
            # digits.append('.')
            cv2.rectangle(output_img,
                          (x0 + w - int(3 * width / 4), y0 + h - int(3 * width / 4)),
                          (x1, y1), color, 2)
            cv2.putText(output_img, 'dot',
                        (x0 + w - int(3 * width / 4), y0 + h - int(3 * width / 4) - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

        cv2.rectangle(output_img, (x0, y0), (x1, y1), color, 2)
        cv2.putText(output_img, str(digit), (x0 + 3, y0 + 10), cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)
    return digits


def get_the_the_lux_reading_as_int(lux_value):
    if '*' in lux_value:
        lux_value = -1
    elif len(lux_value) != 3:
        lux_value = -1
    else:
        lux_value=[str(i) for i in lux_value]
        lux_value = ''.join(lux_value)
    return lux_value


def get_lux_reading_from_image(m_image, threshold=SSD_READING_THRESHOLD_DEFAULT):
    # print('reading at threshold', threshold)
    m_image = get_processed_image(m_image, threshold, show=SHOW_DEBUG_IMAGE)
    output = cv2.bitwise_not(m_image)
    digits_positions = find_digits_positions(m_image)
    digits = recognize_digits_line_method(digits_positions, m_image, output)
    if SHOW_DEBUG_IMAGE:
        cv2.imshow('output', output)
        cv2.waitKey(wait_key_time_out)
    return digits


def get_optimal_threshold_for_ssd_reading(m_image):
    m_threshold = 20
    m_max_threshold = 200
    while m_threshold < m_max_threshold:
        m_digits = get_lux_reading_from_image(m_image, m_threshold)
        # print('digits from threshold detection', m_digits)
        if not is_valid_lux_reading(m_digits):
            m_threshold += 5
        else:
            return m_threshold+10


def main():
    total = 0
    failed = 0
    img_path_list = get_files_with_file_type_from_dir_starting_with(img_folder_path, FILE_TYPE, start_file)
    for img_path in img_path_list:
        total += 1
        image = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        digits = get_lux_reading_from_image(image)
        print(img_path, digits)
        lux_reading = get_the_the_lux_reading_as_int(digits)
        results.append({'file_name': img_path, 'lux_value': lux_reading})
        if lux_reading == -1:
            failed+=1
            # cv2.waitKey()
    print('total',total)
    print('failed', failed)
    write_dictionary_to_csv_file(results, result_file_name)


if __name__ == '__main__':
    main()
