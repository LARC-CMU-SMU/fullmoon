from scripts.m_util import execute_sql_for_dict
import numpy as np
from scipy.optimize import nnls
from scipy.linalg import qr

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
COMFORT_LUX=30

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
    return sum(m_list)


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
    A_=np.array(get_matrix_from_weight_dict(WM))
    print("from dict", A_)
    A = np.array([[53.333332, 0.8333333, 0.41666666, 0, 9.583333, 1.6666666],
                  [0.41666666, 15.416667, 0, 1.6666666, 0, 12.083333],
                  [1.25, 0, 31.666666, 10, 6.25, 4.1666665],
                  [0.41666666, 0.8333333, 8.75, 37.083332, 0.41666666, 11.25]])
    print("hand written", A)
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

    return ret_list, ret_sum


def get_the_deficit_lux(current_lux, already_added_lux, future_lux):
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


def add_dicts(exisisting_lux, adding_lux):
    ret = {}
    for cubical_sensor, existing_lux in exisisting_lux.items():
        ret[cubical_sensor] = existing_lux+adding_lux[cubical_sensor]
    return ret


def myround(x, base=10):
    return base * round(x/base)


def round_the_dict(m_dict):
    ret={}
    for k,v in m_dict.items():
        ret[k]=myround(v)
    return ret
# def get_artificialy_added_lux(weight_matrix, dc_vector)


future_lux={'a':SAFETY_LUX, 'b':COMFORT_LUX, 'c':SAFETY_LUX, 'd':COMFORT_LUX}
print("future lux", future_lux)

current_lux = {'a':70,'b':34,'c':58,'d':59}
rounded_current_lux= round_the_dict(current_lux)
print("current lux", rounded_current_lux)

existing_dc={'a':100, 'b':100, 'c':100, 'd':100, 'e':100,'f':100}

already_added_lux =check(WM,existing_dc)
rounded_already_added_lux = round_the_dict(already_added_lux)
print("already added lux via dc", rounded_already_added_lux)

new_lux_to_add = get_the_deficit_lux(current_lux, already_added_lux, future_lux)
rounded_new_lux_to_add=round_the_dict(new_lux_to_add)
print("new lux to set", rounded_new_lux_to_add)

sorted(rounded_new_lux_to_add)
new_lux_list=list(rounded_new_lux_to_add.values())
dc, dc_sum= get_optimized_dc_vector(new_lux_list)
dc = [float(i) for i in dc]

print("optimizer returned",dc_sum, dc)

validated_dc = get_validated_dc(dc)

DC_TO_SET={'a':validated_dc[0], 'b':validated_dc[1], 'c':validated_dc[2], 'd':validated_dc[3], 'e':validated_dc[4],'f':validated_dc[5]}

print("========================")
print("dc to set", DC_TO_SET)
print("========================")

new_lux_will_be_set=check(WM, DC_TO_SET)
rounded_new_lux_will_be_set=round_the_dict(new_lux_will_be_set)
print("new lux will be ..", rounded_new_lux_will_be_set)

# final_lux=add_dicts(additional_lux_to_be_setted, current_lux)
# print("after setting lux will be", final_lux)






print("that's all folks")