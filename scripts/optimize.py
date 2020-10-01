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
COMFORT_LUX=20

WEIGHT_METRIX={'a':{'a':53,'c':3},
               'b':{'b':14},
               'c':{'c':31,'d':8},
               'd':{'c':9,'d':35,'e':10,'f':34},
               # 'e':{'a':10,'c':6, 'e':17},
               # 'f':{'a':2,'b':12,'c':4,'d':11,'e':8,'f':13}
               }

WM={'a':{'a':53,'e':10, 'f':2},
    'b':{'b':14,'f':12},
    'c':{'c':31,'d':9,'e':6,'f':4},
    'd':{'c':8,'d':35,'f':11},
    # 'e':{'a':3,'c':31,'d':10,'e':17,'f':8},
    # 'f':{'d':34,'f':13}}
    }


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



def get_dc_for_deficit_lux(deficit_lux):
    # a = np.array([[53,0,0,0,10,2],
    #               [0,14,0,0,0,12],
    #               [0,0,31,9,6,4],
    #               [0,0,8,35,0,11],
    #               [3,0,31,10,17,8],
    #               [0,0,0,34,0,13]])
    # b = np.array(deficit_lux)
    # x=np.linalg.solve(a,b)
    # is_correct = np.allclose(np.dot(a,x),b)
    # print('is correct',is_correct)

    a = np.array([[53, 0, 0, 0, 10, 2],
                  [0, 14, 0, 0, 0, 12],
                  [0, 0, 31, 9, 6, 4],
                  [0, 0, 8, 35, 0, 11]])
    b=np.array([20,20,20,20])
    x=np.linalg.lstsq(a, b)
    print(x)

    return list(x[0])


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
        if ret_dc < -100:
            ret_dc = -100
        if ret_dc > 100:
            ret_dc = 100
        ret_dc_vector.append(ret_dc)
    return ret_dc_vector


def get_dc_for_deficit_lux1(b):
    A = np.array([[53, 0, 0, 0, 10, 2],
                  [0, 14, 0, 0, 0, 12],
                  [0, 0, 31, 9, 6, 4],
                  [0, 0, 8, 35, 0, 11]])
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

    # print("final", ret_sum, ret_list)
    return ret_list, ret_sum


def get_dc_for_deficit_lux2(b):
    A = np.array([[53, 0, 0, 0, 10, 2],
                  [0, 14, 0, 0, 0, 12],
                  [0, 0, 31, 9, 6, 4],
                  [0, 0, 8, 35, 0, 11]])
    c = np.array(b)
    x_lstsq = nnls(A, c)[0]
    # Compute the null space of `A`
    Z = qr_null(A)
    nullity = Z.shape[1]

    for _ in range(5):
        x_rand = x_lstsq + Z.dot(np.random.rand(nullity))
        # If `x_rand` is a solution then `||A·x_rand - b||` should be very small
        diff=np.linalg.norm(A.dot(x_rand) - b)
        print(x_rand, diff)

    # ret_list = x_lstsq
    # ret_sum = get_sum(ret_list)
    # ret=[float(i) for i in x[0]]
    # print(ret)


def get_the_deficit_lux(current_lux):
    ret={}
    # print('current lux', current_lux)
    for key in LUX_TO_BE.keys():
        ret[key]=LUX_TO_BE[key]-current_lux[key]
    return ret


def check(weight_matrix, dc_vector):
    for cubical_sensor, weights in weight_matrix.items():
        tot_lux=0
        for light_source,val in weights.items():
            lux=val*dc_vector.get(light_source)/100
            tot_lux+=lux
        print(cubical_sensor, tot_lux)


# current_lux = get_lux_from_db()
current_lux = {'a':0,'b':0,'c':0,'d':0}
LUX_TO_BE={'a':25, 'b':25, 'c':25, 'd':25}

def_lux = (get_the_deficit_lux(current_lux))
sorted(def_lux)
def_lux_list=list(def_lux.values())
# print(def_lux_list)
dc, dc_sum= get_dc_for_deficit_lux1(def_lux_list)
dc = [float(i) for i in dc]
print(dc_sum, list(def_lux.values()),"->", dc)

validated_dc = get_validated_dc(dc)
DC_TO_SET={'a':validated_dc[0], 'b':validated_dc[1], 'c':validated_dc[2], 'd':validated_dc[3], 'e':validated_dc[4],'f':validated_dc[5]}

print(DC_TO_SET)

check(WM,DC_TO_SET)



print("that's all folks")