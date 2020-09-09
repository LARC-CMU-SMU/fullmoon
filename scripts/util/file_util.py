import csv
import json
import os
from os import listdir
from os.path import join, isfile


def write_dictionary_to_csv_file(m_results, m_file_name):
    with open(m_file_name, 'w') as f:
        w = csv.DictWriter(f, m_results[0].keys())
        w.writeheader()
        w.writerows(m_results)


def get_all_files_in_dir(dir):
    all_files = [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]
    return sorted(all_files)


def get_files_with_file_type_from_dir(dir, file_type):
    all_files = get_all_files_in_dir(dir)
    files_from_file_type = [f for f in all_files if f.split(".")[-1] == file_type]
    return files_from_file_type


def get_files_with_file_type_from_dir_starting_with(dir, file_type, start):
    files = get_files_with_file_type_from_dir(dir, file_type)
    start_index = 0
    try:
        start_index = files.index(start)
    except ValueError as e:
        print("warning", str(e))
    return files[start_index:]


def get_data_dictionary_from_csv(m_file_name):
    data = {}
    with open(m_file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for header in reader.fieldnames:
            data[header] = []
        for row in reader:
            for k, v in row.items():
                data[k].append(v)
    return data


def get_dict_list_from_csv(m_file_name):
    data = None
    with open(m_file_name) as f:
        data = [{k: int(v) for k, v in row.items()} for row in csv.DictReader(f, skipinitialspace=True)]
    return data



def dump_dict_to_file(data_dict, file_name):
    with open(file_name, 'w') as fp:
        json.dump(data_dict, fp)


def load_json_to_dict(file_name):
    with open(file_name) as f:
        data = json.load(f)
    return data


def get_time_stamp_from_file_name(file_name):
    return int(file_name.split('/')[-1].split('.')[0][:-1])


def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)