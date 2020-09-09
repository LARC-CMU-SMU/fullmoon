import operator
from datetime import datetime
import xml.etree.ElementTree as ET


from scipy.stats import pearsonr
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import PolynomialFeatures


def get_normalized(data_list):
    data_max=max(data_list)
    data_min=min(data_list)
    return_list=[]
    for x in data_list:
        try:
            return_val = (x-data_min)/(data_max-data_min)
        except ZeroDivisionError as e:
            return_val = 0.5
        return_list.append(return_val)
    return return_list
    # return [(x-data_min)/(data_max-data_min) for x in data_list]


def get_normalized_dict(data_dict, y_fields):
    return_dict = {}
    for k, v in data_dict.items():
        if k in y_fields:
            return_dict[k]=get_normalized(v)
        else:
            return_dict[k]=v
    return return_dict


def convert_str_list_to_int(str_list):
    return [int(x) for x in str_list]


def convert_file_name_to_time(str_list):
    return convert_str_list_to_time([x.split('/')[-1].split('.')[0] for x in str_list])


def convert_str_list_to_float(str_list):
    print(str_list)
    return [float(x) for x in str_list]


def convert_str_list_to_time(str_list):
    return [datetime.fromtimestamp(int(x)).isoformat() for x in str_list]


def fix_data_types(data_dict,float_fields,int_fields,time_fields):
    return_dict={}
    for k, v in data_dict.items():
        print(k)
        if k in float_fields:
            return_dict[k]=convert_str_list_to_float(v)
        elif k in int_fields:
            return_dict[k]=convert_str_list_to_int(v)
        elif k in time_fields:
            return_dict[k]=convert_str_list_to_time(v)
        else:
            return_dict[k]=v
    return return_dict


def get_pearson_correlation_coefficient(data_set_1, data_set_2):
    corr, _ = pearsonr(data_set_1, data_set_2)
    return corr


def load_coords_from_labelimg_xml(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    boxes={}
    for obj in root.iter("object"):
        name = obj.find('name').text
        bndbox = obj.find('bndbox')
        xmin = int(bndbox.find('xmin').text)
        xmax = int(bndbox.find('xmax').text)
        ymin = int(bndbox.find('ymin').text)
        ymax = int(bndbox.find('ymax').text)
        boxes[name]=((xmin,ymin),(xmax,ymax))
    return boxes


def get_r2_score_and_stuff(x, y, degree = 1):
    Y = np.array(x)
    X = np.array(y)

    Y = Y[:, np.newaxis]
    X = X[:, np.newaxis]

    polynomial_features = PolynomialFeatures(degree=degree)

    # print("data len", len(Y))

    # from sklearn.model_selection import train_test_split

    # Split the data into 80% training and 20% testing.
    # The random_state allows us to make the same random split every time.
    # X_train, X_test, y_train, y_test = train_test_split(X, Y, test_size=0.2, random_state=327)
    # print("test %d, train %d" % (len(y_test), len(y_train)))

    X_poly = polynomial_features.fit_transform(X)
    # X_test_poly = polynomial_features.fit_transform(X_test)

    regression_model = linear_model.LinearRegression()
    regression_model.fit(X_poly, Y)

    y_predict = regression_model.predict(X_poly)

    # The coefficients
    print('Coefficients: \n', regression_model.coef_)
    # The mean squared error
    print('Root Mean squared error: %.2f'
          % np.sqrt(mean_squared_error(Y, y_predict)))
    # The coefficient of determination: 1 is perfect prediction
    print('Coefficient of determination: %.2f'
          % r2_score(Y, y_predict))

    import matplotlib.pyplot as plt

    plt.scatter(X, Y)
    # sort the values of x before line plot
    sort_axis = operator.itemgetter(0)
    sorted_zip = sorted(zip(X, y_predict), key=sort_axis)
    X, y_predict = zip(*sorted_zip)
    plt.plot(X, y_predict, 'r', lw=2)
    plt.xlabel('pixel val')
    plt.ylabel('lux lux')
    plt.show()

    print("thal's all folks")
