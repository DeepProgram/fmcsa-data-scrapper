import csv


def get_list_from_string(string: str) -> list:
    each_info_list = []
    for each_info in string.strip()[1:-1].split(","):
        each_info_list.append(each_info.strip()[1:-1])
    return each_info_list


with open("data.txt", "r") as file:
    info_dict = {}
    csd_file = csv.writer(open("user_info.csv", "w"), )
    csd_file.writerow(["ID", "NAME", "PHONE", "EMAIL", "CITY", "STATE"])
    for each_info_in_string in file.readlines():
        if not each_info_in_string.isspace():
            each_info_in_list = get_list_from_string(each_info_in_string)
            if each_info_in_list[0] not in info_dict:
                info_dict[each_info_in_list[0]] = each_info_in_list

    for keys, values in info_dict.items():
        csd_file.writerow(values)
