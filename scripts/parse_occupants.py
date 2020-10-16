import json

from scripts.m_util import execute_sql_for_dict

SQL="""select o.timestamp, o.occupancy, o.label, o.occupant_coordinates
from occupancy o
inner join (
    select label, max(timestamp) as MaxTs
    from occupancy
    group by label
) tm on o.label = tm.label and o.timestamp = tm.MaxTs"""



def get_latest_occupancy():
    ret = {}
    from_db=execute_sql_for_dict(SQL, [])
    for row in from_db:
        ts = row.get("timestamp")
        occupancy = row.get("occupancy")
        label = row.get("label")
        occupant_coordinates = row.get("occupant_coordinates")
        occupant_coordinates_json = None
        if occupant_coordinates and len(occupant_coordinates) > 0:
            # print(occupant_coordinates)
            occupant_coordinates_json = json.loads(occupant_coordinates)
        ret[label]={"timestamp": ts, "occupancy": occupancy, "occupants": occupant_coordinates_json}
    return ret


occupancy = get_latest_occupancy()
print(occupancy)
