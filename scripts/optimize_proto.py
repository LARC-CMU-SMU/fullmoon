import time

from scripts.m_util import execute_sql_for_dict
import numpy as np
from scipy.optimize import nnls
from scipy.linalg import qr
import random
import plotly.graph_objs as go




LUX_QUERY = '''select l.label, l.pin,l.timestamp, l.lux
from lux l
inner join (
    select label, pin, max(timestamp) as MaxTs
    from lux
    group by label, pin
) tm on l.label = tm.label and l.pin=tm.pin and l.timestamp = tm.MaxTs'''

# MIN_LUX=10
# COMFORT_LUX=20

SAFETY_LUX=10
COMFORT_LUX=20

WM={'a':{'a':53.3,'b':0.8,'c':0.4,'d':0,'e':9.6, 'f':1.7},
    'b':{'a':0.4,'b':15.4,'c':0,'d':1.7,'e':0,'f':12.1},
    'c':{'a':1.25,'b':0,'c':31.7,'d':10,'e':6.25,'f':4.2},
    'd':{'a':0.4,'b':0.8,'c':8.75,'d':37.1,'e':0.4,'f':11.25}
    }


def get_matrix_from_weight_dict(weight_dict):
    ret=[]
    sorted(weight_dict)
    for section_label, section_weights in weight_dict.items():
        current_row=[]
        sorted(section_weights)
        for light_soure_id, light_source_weight in section_weights.items():
            current_row.append(light_source_weight)
        ret.append(current_row)
    return ret


def get_lux_from_db():
    ret ={}
    lux=execute_sql_for_dict(LUX_QUERY,[])
    for row in lux:
        label = row['label']
        pin=row['pin']
        lux=row['lux']
        composite_label="{}_{}".format(label,pin)
        if composite_label=='a_tsl_0':
            ret['a']=lux
        if composite_label=='b_tsl_2':
            ret['b']=lux
        if composite_label=='c_tsl_0':
            ret['c']=lux
        if composite_label=='d_tsl_0':
            ret['d']=lux
        if composite_label == 'e_tsl_0':
            ret['e'] = lux
        if composite_label == 'f_tsl_0':
            ret['f'] = lux
    return ret



def qr_null(A, tol=None):
    """Computes the null space of A using a rank-revealing QR decomposition"""
    Q, R, P = qr(A.T, mode='full', pivoting=True)
    tol = np.finfo(R.dtype).eps if tol is None else tol
    rnk = min(A.shape) - np.abs(np.diag(R))[::-1].searchsorted(tol)
    return Q[:, rnk:].conj()


def is_less_than_one(m_list):
    for x in m_list:
        if x>1:
            return False
    return True


def get_sum(m_list):
    return sum([x if x >0 else 0 for x in m_list])


def get_validated_dc(m_dc_vector):
    ret_dc_vector=[]
    for m_dc in m_dc_vector:
        ret_dc = m_dc * 100
        if ret_dc < 0:
            ret_dc = 0
        if ret_dc > 100:
            ret_dc = 100
        ret_dc_vector.append(ret_dc)
    return ret_dc_vector


def get_optimized_dc_vector(b):
    start= time.time()
    A=np.array(get_matrix_from_weight_dict(WM))
    # print("from dict", A_)
    # A = np.array([[53.333332, 0.8333333, 0.41666666, 0, 9.583333, 1.6666666],
    #               [0.41666666, 15.416667, 0, 1.6666666, 0, 12.083333],
    #               [1.25, 0, 31.666666, 10, 6.25, 4.1666665],
    #               [0.41666666, 0.8333333, 8.75, 37.083332, 0.41666666, 11.25]])
    # print("hand written", A)
    c = np.array(b)
    # Find an initial solution using `np.linalg.lstsq`
    x_lstsq = np.linalg.lstsq(A, c, rcond=None)[0]

    # Compute the null space of `A`
    Z = qr_null(A)
    nullity = Z.shape[1]

    ret_list=x_lstsq
    ret_sum = get_sum(ret_list)
    # print("initial", ret_sum, ret_list)
    # Sample some random solutions
    for _ in range(10000):
        x_rand = x_lstsq + Z.dot(np.random.rand(nullity))
        diff = np.linalg.norm(A.dot(x_rand) - b)
        # If `x_rand` is a solution then `||A·x_rand - b||` should be very small
        if diff < 1e-10:  # basic filtering based on resulting dc vector
            if is_less_than_one(x_rand):  # basic filtering based on individual dc
                current_sum = get_sum(x_rand)
                if ret_sum > current_sum:  # find out the least costly(dc wise) setting
                    ret_sum = current_sum
                    ret_list = x_rand
    print("time used for optimization \t\t\t\t\t\t\t\t\t", time.time()-start)
    return ret_list, ret_sum


def get_the_new_lux_values_should_be_added_by_system(current_lux, already_added_lux, future_lux):
    ret={}
    # print('current lux', current_lux)
    for key in future_lux.keys():
        ret[key]= future_lux[key] - current_lux[key] + already_added_lux[key]
    return ret


def check(weight_matrix, dc_vector):
    ret = {}
    for cubical_sensor, weights in weight_matrix.items():
        tot_lux=0
        for light_source,val in weights.items():
            lux=val*dc_vector.get(light_source)/100
            tot_lux+=lux
        ret[cubical_sensor] = tot_lux
    return ret


def add_dicts(dict_1, dict_2):
    ret = {}
    for k in dict_1.keys():
        ret[k] = dict_1[k] + dict_2[k]
    return ret


def myround(x, base=10):
    return base * round(x/base)


def round_the_dict(m_dict):
    ret={}
    for k,v in m_dict.items():
        ret[k]=myround(v)
    return ret
# def get_artificialy_added_lux(weight_matrix, dc_vector)


def get_dict_with_rand_values(m_dict,low, high):
    ret_dict={}
    for k in m_dict.keys():
        ret_dict[k]=round(random.uniform(low,high))
    return ret_dict


def get_should_be_lux_for_occupancy(occupancy):
    ret_dict={}
    for k,v in occupancy.items():
        ret_dict[k]=COMFORT_LUX if v == 1 else SAFETY_LUX
    return ret_dict


def get_dict_diff(dict_1,dict_2):
    ret ={}
    for k in dict_1.keys():
        ret[k]=dict_1[k]-dict_2[k]
    return ret


def should_add_lux(new_lux_to_set):
    for v in new_lux_to_set.values():
        if v > 0:
            return True
    return False


def get_random_natural_lux(sample_dict, is_night=False):
    if is_night:
        return get_dict_with_rand_values(sample_dict, 0, 0)
    else:
        return get_dict_with_rand_values(sample_dict, 0, 30)


def get_positive_only_dict(m_dict):
    ret = {}
    for k, v in m_dict.items():
        ret[k] = v if v>0 else 0
    return ret


before_lux_list=[]
occupancy_list=[]
dc_list=[]
after_lux_list=[]
# derrived_natural_lux_list=[]
should_be_lux_list=[]
art_lux_list=[]
cost_list=[]
natural_lux_list=[]

dict_of_lists={"before_lux":before_lux_list,
               "occupancy":occupancy_list,
               "dc":dc_list,
               "after_lux":after_lux_list,
               # "derrived_natural_lux":derrived_natural_lux_list,
               "should_be_lux":should_be_lux_list,
               "art_lux":art_lux_list,
               "cost":cost_list,
               "true_natural_lux":natural_lux_list,
               }
before_lux = {'a': 0, 'b': 0, 'c': 0, 'd': 0}
existing_dc = {'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0}
# added_art_lux={'a': 0, 'b': 0, 'c': 0, 'd': 0}
is_night=True

for i in range(10):
    occupancy_dict = {'a': 1, 'b': 0, 'c': 1, 'd': 1}
    occupancy_dict = get_dict_with_rand_values(occupancy_dict, 0, 1)
    occupancy_list.append(occupancy_dict)
    print("occupancy(now)\t\t\t\t\t\t\t\t\t\t\t\t", occupancy_dict)

    future_lux = get_should_be_lux_for_occupancy(occupancy_dict)
    should_be_lux_list.append(future_lux)
    print("required lux based on occupancy\t\t\t\t\t\t\t\t", future_lux)

    already_added_lux = check(WM, existing_dc)
    rounded_already_added_lux = round_the_dict(already_added_lux)
    art_lux_list.append(rounded_already_added_lux)
    print("added lux via dc in prev step (derived from dc values)\t\t", rounded_already_added_lux)

    # rounded_before_lux = round_the_dict(before_lux)
    #
    # derived_natural_lux = get_dict_diff(rounded_before_lux, rounded_already_added_lux)
    # # derrived_natural_lux_list.append(derived_natural_lux)
    # print("derived natural_lux\t\t\t\t\t\t\t\t\t\t", derived_natural_lux)

    new_natural_lux = round_the_dict(get_random_natural_lux(already_added_lux, is_night))
    print("changed natural_lux to (playing god)\t\t\t\t\t\t", new_natural_lux)

    natural_lux_list.append(new_natural_lux)

    # this will come from system
    rounded_current_lux= add_dicts(rounded_already_added_lux, new_natural_lux)

    before_lux_list.append(rounded_current_lux)
    print("current (total) lux\t\t\t\t\t\t\t\t\t\t\t", rounded_current_lux)

    lux_deficit = get_the_new_lux_values_should_be_added_by_system(rounded_current_lux, already_added_lux, future_lux)
    rounded_lux_deficit = round_the_dict(lux_deficit)

    print("new artificial lux values needed to be set by system\t\t", rounded_lux_deficit)

    if (should_add_lux(rounded_lux_deficit)):
        sorted(rounded_lux_deficit)
        new_lux_list = list(rounded_lux_deficit.values())
        dc, dc_sum = get_optimized_dc_vector(new_lux_list)
        dc = [float(i) for i in dc]

        print("optimizer returned \t\t\t\t\t\t\t\t\t\t\t", dc_sum, dc)

        validated_dc = get_validated_dc(dc)

        DC_TO_SET = {'a': validated_dc[0], 'b': validated_dc[1], 'c': validated_dc[2], 'd': validated_dc[3],
                     'e': validated_dc[4], 'f': validated_dc[5]}

    else:
        DC_TO_SET = {'a':0,'b':0,'c':0,'d':0,'e':0,'f':0}
        dc_sum=0

    print("dc levels to set\t\t\t\t\t\t\t\t\t\t\t", DC_TO_SET)

    dc_list.append(DC_TO_SET)
    cost_list.append({"all":dc_sum})
    new_lux_will_be_set = check(WM, DC_TO_SET)
    rounded_new_lux_will_be_set = round_the_dict(new_lux_will_be_set)
    print("new artificial lux added to the system will be\t\t\t\t", rounded_new_lux_will_be_set)
    added_art_lux=rounded_new_lux_will_be_set
    final_lux=round_the_dict(add_dicts(new_natural_lux, rounded_new_lux_will_be_set))
    print("final new lux will be\t\t\t\t\t\t\t\t\t\t", final_lux)
    after_lux_list.append(final_lux)

    existing_dc=DC_TO_SET
    before_lux=final_lux
    print("------------------------")


fig = go.Figure()

for name, m_list in dict_of_lists.items():
    # print(name,m_list)
    for key in m_list[0].keys():
        y=[d[key] for d in m_list]
        x=list(range(len(m_list)))
        fig.add_trace(go.Scatter(y=y,
                                 x=x,
                                 mode='lines',
                                 name="{}_{}".format(name, key)))

# fig.write_html("optimizer_with_natural.html")
# fig.show()


print("that's all folks")