import csv
import os
from typing import IO


def get_list_from_string(string: str) -> list:
    each_info_list = []
    for each_info in string.strip()[1:-1].split(","):
        each_info_list.append(each_info.strip()[1:-1])
    return each_info_list


def get_dictionary_from_string_list(file: IO) -> dict:
    info_dict = {}
    for each_info_in_string in file.readlines():
        if not each_info_in_string.isspace():
            each_info_in_list = get_list_from_string(each_info_in_string)
            if each_info_in_list[0] not in info_dict:
                info_dict[each_info_in_list[0]] = each_info_in_list
    return info_dict


def main(file_name: str):
    file = open(file_name, "r")
    csv_file = csv.writer(open("user_info.csv", "w"), )
    csv_file.writerow(["ID", "NAME", "PHONE", "EMAIL", "CITY", "STATE"])
    user_info_dict = get_dictionary_from_string_list(file)
    for keys, values in user_info_dict.items():
        csv_file.writerow(values)
    os.remove(file_name)
