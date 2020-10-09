import numpy as np
from scipy.linalg import qr


def qr_null(A, tol=None):
    """Computes the null space of A using a rank-revealing QR decomposition"""
    Q, R, P = qr(A.T, mode='full', pivoting=True)
    tol = np.finfo(R.dtype).eps if tol is None else tol
    rnk = min(A.shape) - np.abs(np.diag(R))[::-1].searchsorted(tol)
    return Q[:, rnk:].conj()


def get_sum(m_list):
    return sum(m_list)


def is_all_elements_are_less_than_one(m_list):
    for x in m_list:
        if abs(x) > 1:
            return False
    return True


def solve_undetermined_system_of_linear_equations(coefficient_matrix, y_vector, num_of_results=10000):
    ret = []
    A = np.array(coefficient_matrix)
    b = np.array(y_vector)

    # Find an initial solution using `np.linalg.lstsq`
    x_lstsq = np.linalg.lstsq(A, b, rcond=None)[0]

    # Compute the null space of `A`
    Z = qr_null(A)
    nullity = Z.shape[1]

    # Sample some random solutions
    for _ in range(num_of_results):
        x_rand = x_lstsq + Z.dot(np.random.rand(nullity))
        diff = np.linalg.norm(A.dot(x_rand) - b)
        # If `x_rand` is a solution then `||A·x_rand - b||` should be very small
        if diff < 1e-10:  # basic filtering based on resulting dc vector
            ret.append(x_rand)

    return ret


def get_positive_dc_vector(dc_vector):
    return [x if x > 0 else 0 for x in dc_vector]


def get_least_costly_dc_vector(list_of_dc_vectors):
    dc_sum = float('inf')
    ret = None
    for dc_vector in list_of_dc_vectors:
        if is_all_elements_are_less_than_one(dc_vector):  # basic filtering based on individual dc
            dc_vector = get_positive_dc_vector(dc_vector)  # can't set negative dc values in the system
            current_sum = get_sum(dc_vector)
            if current_sum < dc_sum:  # find out the least costly(dc wise) setting
                dc_sum = current_sum
                ret = dc_vector
    return ret, dc_sum


def get_dry_run_results_for_dc_vector(weight_dict, dc_vector):
    ret = {}
    for cubical_sensor, weights in weight_dict.items():
        tot_lux = 0
        for light_source, val in weights.items():
            lux = val * dc_vector.get(light_source) / 100
            tot_lux += lux
        ret[cubical_sensor] = tot_lux
    return ret


def get_labeled_and_upscaled_dc_vector(dc_vector, labels):
    ret = {}
    # todo :optimize below
    ret['a'] = dc_vector[0]*1000000
    ret['b'] = dc_vector[1] * 1000000
    ret['c'] = dc_vector[2] * 1000000
    ret['d'] = dc_vector[3] * 1000000
    ret['e'] = dc_vector[4] * 1000000
    ret['f'] = dc_vector[5] * 1000000
    return ret


def opt_get_optimized_dc_dict(weight_matrix, weight_dict, lux_dict, logger):
    labeled_dc_vector = None
    logger.debug("calculating most economical dc vector for lux dict {}".format(lux_dict))
    sorted(lux_dict)
    lux_values_vector = list(lux_dict.values())
    lux_key_list=list(lux_dict.keys())
    logger.debug("lux dict transformed to vector[{}] sorted by labels [{}]".format(lux_values_vector, lux_key_list))
    dc_vector_list = solve_undetermined_system_of_linear_equations(weight_matrix, lux_values_vector, 10000)
    best_dc_vector, dc_sum = get_least_costly_dc_vector(dc_vector_list)
    if best_dc_vector is not None:
        # logger.debug("best dc vector [{}]".format(best_dc_vector))
        labeled_dc_vector = get_labeled_and_upscaled_dc_vector(best_dc_vector, lux_key_list)
        logger.debug("least costly dc vector {}".format(labeled_dc_vector))
        dry_run_results = get_dry_run_results_for_dc_vector(weight_dict, labeled_dc_vector)
        logger.debug("dry run results {}".format(dry_run_results))
    return labeled_dc_vector, dc_sum
