import math
from pprint import pprint

from numpy import mean

from scripts.m_util import get_coords_from_labelimg_xml
from scripts.m_util import execute_sql_for_dict

PEARSON_CORR_THRESHOLD = .9
PATCH_SQL = "select patch_label, h_min, h_max from fp where cam_label=%s and lux_label=%s and pearson_corr > %s"
PIXEL_ANALYTICS_SQL = "select lux, h_mean from pixel_lux where cam_label=%s and lux_label=%s and patch_label > %s order by timestamp DESC LIMIT 1"

# OCCUPANCY_LIST = [{'x_min': 672, 'x_max': 704, 'y_min': 133, 'y_max': 292}, {'x_min': 589, 'x_max': 951, 'y_min': 243, 'y_max': 301}]
# PATCH_COORDINATES = get_coords_from_labelimg_xml("/Users/kasun/projects/fullmoon/ipcam/patch_coordinates/1598961600b.xml")


def get_above_threshold_patches_for_label(cam_label, lux_label):
    ret = []
    from_db = execute_sql_for_dict(PATCH_SQL, [cam_label, lux_label, PEARSON_CORR_THRESHOLD])
    for row in from_db:
        ret.append({"label": row["patch_label"], "h_min": row["h_min"], "h_max": row["h_max"]})
    return ret


def get_pixel_analytics_for_patch(cam_label, lux_label, patch_label):
    ret = {"lux": -1, "h_mean": -1}
    from_db = execute_sql_for_dict(PIXEL_ANALYTICS_SQL, [cam_label, lux_label, patch_label])
    if len(from_db) == 1:
        res = from_db[0]
        ret["lux"] = res["lux"]
        ret["h_mean"] = res["h_mean"]
    return ret


def is_hue_in_range(h, h_min, h_max):
    if h_min < h < h_max:
        return True
    return False


def get_pseudo_lux_for_label(cam_label, lux_label, occupancy_blocks, patch_coordinates):
    ret = {}
    patches = get_above_threshold_patches_for_label(cam_label, lux_label)
    for patch in patches:
        patch_label=patch["label"]
        hue_min = patch["h_min"]
        hue_max = patch["h_max"]
        message = "blocked"
        status = 1
        lux = -1
        is_blocked = is_patch_blocked(patch_label,patch_coordinates,occupancy_blocks)
        if not is_blocked:
            message = "not in hue range"
            status = 2
            pixel_analytics = get_pixel_analytics_for_patch(cam_label, lux_label, patch_label)
            hue = pixel_analytics["h_mean"]
            hue_in_range = is_hue_in_range(hue, hue_min, hue_max)
            if hue_in_range:
                message = "success"
                status = 0
                lux = pixel_analytics["lux"]
        ret[patch_label] = {"lux": lux, "status":status, "message":message}
    return ret


def is_patch_blocked(patch_label, patch_coordinates_dict, occupancy_blocks):
    (xmin, ymin), (xmax, ymax) = patch_coordinates_dict[patch_label]
    for occupancy_block in occupancy_blocks:
        occupant_block_x_min = occupancy_block["x_min"]
        occupant_block_y_min = occupancy_block["y_min"]
        occupant_block_x_max = occupancy_block["x_max"]
        occupant_block_y_max = occupancy_block["y_max"]
        if occupant_block_x_min < xmin < occupant_block_x_max:
            return True
        if occupant_block_x_min < xmax < occupant_block_x_max:
            return True
        if occupant_block_y_min < ymin < occupant_block_y_max:
            return True
        if occupant_block_y_min < ymax < occupant_block_y_max:
            return True
    return False


def get_avg_lux_value(all_lux_values):
    ret = {}
    for lux_sensor, pseudo_lux_values in all_lux_values.items():
        lux_value_list = []
        for patch_label, pseudo_lux_stat in pseudo_lux_values.items():
            pseudo_lux = pseudo_lux_stat["lux"]
            pseudo_lux_status = pseudo_lux_stat["status"]
            if pseudo_lux_status == 0:
                lux_value_list.append(pseudo_lux)
        if len(lux_value_list) > 0:
            ret[lux_sensor] = int(mean(lux_value_list))
        else:
            ret[lux_sensor] = -1
    return ret


def m_get_current_pseudo_lux(cam_label, lux_labels, occupancy_blocks, patch_coordinates_dict):
    inter_ret = {}
    for lux_label in lux_labels:
        inter_ret[lux_label]=get_pseudo_lux_for_label(cam_label, lux_label, occupancy_blocks, patch_coordinates_dict)
    ret = get_avg_lux_value(inter_ret)
    return ret


# current_pseudo_lux = get_current_pseudo_lux('b', ['a_tsl_0', 'b_tsl_3', 'c_tsl_0', 'd_tsl_0'], OCCUPANCY_LIST, PATCH_COORDINATES)
# pprint(current_pseudo_lux)