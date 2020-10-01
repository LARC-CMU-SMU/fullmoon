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
    print(coefficient_matrix)
    print(y_vector)
    # todo: use the coefficient_matrix passed to method
    A = np.array([53, 0, 0, 0, 10, 2],
            [0, 14, 0, 0, 0, 12],
            [0, 0, 31, 9, 6, 4],
            [0, 0, 8, 35, 0, 11])
    # todo: use the coefficient_matrix passed to method
    b = np.array([0,0,20,0])
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


def get_the_most_optimized_dc_vector(list_of_dc_vectors):
    dc_sum = float('inf')
    ret = None
    for dc_vector in list_of_dc_vectors:
        if is_all_elements_are_less_than_one(dc_vector):  # basic filtering based on individual dc
            current_sum = get_sum(dc_vector)
            if current_sum < dc_sum:  # find out the least costly(dc wise) setting
                dc_sum = current_sum
                ret = dc_vector
    return ret, dc_sum


def get_dry_run_results_for_dc_vector(weight_matrix, dc_vector):
    ret = {}
    for cubical_sensor, weights in weight_matrix.items():
        tot_lux = 0
        for light_source, val in weights.items():
            lux = val * dc_vector.get(light_source) / 100
            tot_lux += lux
        ret[cubical_sensor] = tot_lux
    return ret


def get_labeled_dc_vector(dc_vector, labels):
    ret = {}
    for i in range(len(labels)):
        ret[labels[i]] = dc_vector[i]
    return ret


def get_optimized_dc_vector(weight_matrix, lux_dict, logger):
    logger.debug("calculating most economical dc vector for lux dict {}".format(lux_dict))
    sorted(lux_dict)
    lux_vector = list(lux_dict.values())
    logger.debug("lux dict transformed to vector sorted by labels {}".format(lux_vector))
    dc_vector_list = solve_undetermined_system_of_linear_equations(weight_matrix, lux_vector, 10000)
    best_dc_vector, dc_sum = get_optimized_dc_vector(dc_vector_list)
    labeled_dc_vector = get_labeled_dc_vector(best_dc_vector, list(lux_dict.keys()))
    logger.debug("least costly dc vector {}".format(labeled_dc_vector))
    dry_run_results = get_dry_run_results_for_dc_vector(weight_matrix, labeled_dc_vector)
    logger.debug("dry run results {}".format(dry_run_results))
    return labeled_dc_vector, dc_sum
