from scripts.util import db

QUERY_FP_SELECT = "SELECT * FROM fp"
FINGER_PRINTS = {}


def load_finger_prints():
    fp_dict_list = db.execute_sql_for_dict(QUERY_FP_SELECT,[])
    print(fp_dict_list)
    for fp in fp_dict_list:
        patch_label = fp['patch_label']
        if not FINGER_PRINTS.get(patch_label):
            FINGER_PRINTS[patch_label]={}
        lux_label = fp['lux_label']
        FINGER_PRINTS[patch_label][lux_label]={'x2':float(fp['x2']),
                                               'x1':float(fp['x1']),
                                               'x0':float(fp['x0']),
                                               'pearson_corr':float(fp['pearson_corr'])}
    print('done loading finger prints')


load_finger_prints()
print("that's all folks")