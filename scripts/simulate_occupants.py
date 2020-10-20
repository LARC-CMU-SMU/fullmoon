import random
import time
from pprint import pprint
import json

from scripts.m_util import execute_sql_for_dict

OCCUPANCY_SQL= """INSERT INTO occupancy(timestamp, occupancy, cam_label, cubical_label, occupant_coordinates) VALUES (%s, %s, %s, %s, %s)"""
OCCUPANCY_CACHE_SQL = "INSERT INTO occupancy_cache(timestamp, occupancy, cam_label, cubical_label, occupant_coordinates) VALUES (%s, %s, %s, %s, %s)" \
                        "ON CONFLICT (cam_label,cubical_label) DO UPDATE " \
                      "SET timestamp = excluded.timestamp, occupancy = excluded.occupancy, occupant_coordinates = excluded.occupant_coordinates;"

cubicles = {
    'a': {"x_min": 1139, "y_min": 240, "x_max": 1616, "y_max": 592},
    'b': {"x_min": 330, "y_min": 640, "x_max": 1315, "y_max": 1080},
    'c': {"x_min": 573, "y_min": 99, "x_max": 954, "y_max": 435},
    'd': {"x_min": 123, "y_min": 297, "x_max": 572, "y_max": 637},
}

CAM_LABEL="b"


def get_time():
    return(int(time.time()))


def get_random_occupancy():
    rand_int = random.randint(0, 5)
    if rand_int % 2 == 0:
        return True
    return False


def get_random_occupants(boundry, max_occupancy=2):
    ret = []
    for i in range(random.randint(1,max_occupancy)):
        x_min, x_max = sorted([random.randint(boundry["x_min"], boundry["x_max"]), random.randint(boundry["x_min"], boundry["x_max"])])
        y_min, y_max = sorted([random.randint(boundry["y_min"], boundry["y_max"]), random.randint(boundry["y_min"], boundry["y_max"])])
        ret.append({"x_min":x_min, "x_max":x_max, "y_min":y_min, "y_max":y_max})
    return json.dumps(ret)


def to_db():
    ret = {}
    for key, boundry in cubicles.items():
        occupancy = get_random_occupancy()
        occupancy_coord = None
        if occupancy:
            occupancy_coord=get_random_occupants(boundry)
        ret[key]={"timestamp":get_time(), "label":key, "occupancy":occupancy, "occupant_coordinates":occupancy_coord}
    return ret


def insert_to_db(data):
    for values in data.values():
        print(values)
        sql_values=[values["timestamp"], values["occupancy"], CAM_LABEL, values["label"], values["occupant_coordinates"]]
        execute_sql_for_dict(OCCUPANCY_SQL, sql_values)
        execute_sql_for_dict(OCCUPANCY_CACHE_SQL, sql_values)


occupancy_data = to_db()
pprint(occupancy_data)

insert_to_db(occupancy_data)
