import csv
import pickle
from os.path import isfile
from random import randrange, randint
import re
import cv2


def get_llnet_file_name(file_id_with_path):
    llnet_file_name = file_id_with_path.replace(file_id_with_path.split('/')[-1],
                                                'llnet/LLnet_inference_' + file_id_with_path.split('/')[
                                                    -1] + '_out.png')
    return llnet_file_name


def get_NMS_applied_coordinates(coordinates, confidences_raw, score_threshold, nms_threshold):
    confidences = [float(conf) for conf in confidences_raw]
    idxs = cv2.dnn.NMSBoxes(coordinates, confidences, score_threshold,
                            nms_threshold)
    box_out = []
    confidence_out = []

    # ensure at least one detection exists
    if len(idxs) > 0:
        # loop over the indexes we are keeping
        for i in idxs.flatten():
            # extract the bounding box coordinates
            (x, y) = (coordinates[i][0], coordinates[i][1])
            (w, h) = (coordinates[i][2], coordinates[i][3])
            box_out.append([x, y, x + w, y + h])
            confidence_out.append(confidences[i])

    return box_out, confidence_out


def convert_xy_min_max_to_xy_minWH(coordinates):
    xyWH = []
    for coordinate in coordinates:
        x, y = coordinate[0:2]
        W = coordinate[2] - coordinate[0]
        H = coordinate[3] - coordinate[1]
        xyWH.append([x, y, W, H])
    return xyWH


def get_annotations_from_file(image_file_path_file):
    if not isfile(image_file_path_file + '.pkl'):
        read_annotaion_file_and_store_in_pickle(image_file_path_file)
    with open(image_file_path_file + '.pkl', 'rb') as f:
        return pickle.load(f)

    print("returning annotations")
    return annotations


def read_annotaion_file_and_store_in_pickle(image_file_path_file):
    print("loading annotations...")
    with open(image_file_path_file, 'r') as f:
        all_files = f.readlines()
    file_ids_with_path = [f[:-5] for f in all_files]
    annotations = {}
    for i, file_id_with_path in enumerate(file_ids_with_path):
        print(i, '/', len(file_ids_with_path), end='\r')
        annotations[file_id_with_path] = []
        annotation_file_with_path = file_id_with_path + ".txt"
        image_file_with_path = file_id_with_path + ".jpg"
        image = cv2.imread(image_file_with_path)
        H, W = image.shape[:2]
        if not isfile(annotation_file_with_path):
            print("no such file skipping", annotation_file_with_path)
            continue
        with open(annotation_file_with_path, 'r') as a_file:
            for line in a_file.readlines():
                class_id, x, y, width, height = [float(i) for i in line.split()]
                x_min, y_min, x_mx, y_max = int((x - width / 2) * W), int((y - height / 2) * H), int(
                    (x + width / 2) * W), int((y + height / 2) * H)
                annotations[file_id_with_path].append([x_min, y_min, x_mx, y_max])
    with open(image_file_path_file + '.pkl', 'wb') as f:
        pickle.dump(annotations, f, pickle.HIGHEST_PROTOCOL)


def get_random_int(min, max):
    return randrange(min, max)


def get_a_random_number(low=10, high=245):
    random_int = randint(low, high)
    return random_int


def get_a_random_color():
    b = get_a_random_number()
    g = get_a_random_number()
    r = get_a_random_number()
    return b, g, r


def sorted_nicely(l):
    """ Sort the given iterable in the way that humans expect."""
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)


def get_natural_sorted_list(m_list):
    return sorted_nicely(m_list)


def is_valid_lux_reading(digit_list):
    if len(digit_list) is not 3 or '*' in digit_list:
        return False
    return True


def write_list_of_dicts_to_csv_file(m_results, m_file_name):
    print('writing results to', m_file_name)
    with open(m_file_name, 'w') as f:
        w = csv.DictWriter(f, m_results[0].keys())
        w.writeheader()
        w.writerows(m_results)