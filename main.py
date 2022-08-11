from typing import Optional, IO
from bs4 import BeautifulSoup, ResultSet
import requests
from save_csv import main as save_into_csv


def get_html_from_url(url: str, url_params: dict) -> Optional[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/104.0.0.0 Safari/537.36 Edg/104.0.1293.47"
    }
    try:
        response = requests.get(url, params=url_params, headers=headers)
    except requests.exceptions.Timeout:
        print("Request Timed Out.. Please Check Internet Connection Or Use A Valid Proxy..")
        return None
    except requests.exceptions.TooManyRedirects:
        print("Url Is Not Valid.. Please check the demo url in github and try url like that..")
        return None
    except requests.exceptions.RequestException as e:
        print("Error Occurred While Fetching Data ", e)
        return None
    except Exception as e:
        print("Error Occurred While Fetching Data ", e)
        return None
    return response.text


def process_html_with_soup(html: str, tag: str, attributes: dict, find_all: bool) -> Optional[ResultSet[BeautifulSoup]]:
    try:
        soup = BeautifulSoup(html, "html.parser")
    except TypeError:
        print("Got Invalid Response.... Please Change IP Or Check Internet Connection")
        return None

    if find_all:
        try:
            processed_html = soup.find_all(tag, attrs=attributes)
        except Exception as e:
            print("Could Not Found Desired Element..Try After Changing IP..", e)
            return None
    else:
        try:
            processed_html = soup.find(tag, attrs=attributes).contents
        except Exception as e:
            print("Could Not Found Desired Element..Try After Changing IP..", e)
            return None
    return processed_html


def found_us_dot(td_elements: list) -> int:
    extracted_us_dot = -1
    for td_element in td_elements:
        try:
            extracted_us_dot = int(td_element.text)
            break
        except ValueError:
            pass
    return extracted_us_dot


def get_info_list(all_info: ResultSet[BeautifulSoup]) -> Optional[list]:
    extracted_info_list = []
    for info_index, info in enumerate(all_info):
        try:
            label_value = info.label.text.strip()
            span_value = info.span.text.strip()
        except AttributeError:
            continue
        if label_value == "Legal Name:":
            extracted_info_list.insert(1, span_value)
        elif label_value == "U.S. DOT#:":
            extracted_info_list.insert(0, span_value)
        elif label_value == "Telephone:":
            extracted_info_list.insert(2, span_value)
        elif label_value == "Email:":
            extracted_info_list.insert(3, span_value)
        elif label_value == "Address:":
            try:
                city = info.span.contents[2].split(",")[0]
                state = info.span.contents[2].split(",")[1].strip().split(" ")[0]
            except Exception as e:
                print("Could Not Find Desired Value....", e)
                return None
            extracted_info_list.insert(4, city)
            extracted_info_list.insert(5, state)

    return extracted_info_list


def get_today_mc_register_menu() -> ResultSet[BeautifulSoup]:
    params = {
        "pv_choice": "FED_REG",
        "x": "9",
        "y": "14",
        "pv_vpath": "LIVIEW"
    }
    html = get_html_from_url("https://li-public.fmcsa.dot.gov/LIVIEW/pkg_menu.prc_menu", params)
    register_table = process_html_with_soup(html, "td", {"valign": "top"}, find_all=True)
    return register_table


def get_selected_register_list(date_in_string: str) -> ResultSet[BeautifulSoup]:
    params = {
        "pd_date": date_in_string,
        "pv_vpath": "LIVIEW"
    }
    html = get_html_from_url("https://li-public.fmcsa.dot.gov/LIVIEW/PKG_register.prc_reg_detail", params)

    mc_number_elements = process_html_with_soup(html, "th", {"scope": "row"}, True)
    return mc_number_elements


def get_mc_id_list_from_html(mc_html_elements: ResultSet[BeautifulSoup]) -> list:
    return [mc_number_element.text.split("-")[1].strip() for mc_number_element in mc_html_elements]


def get_mc_record_from_mc_id(mc_id: str) -> Optional[ResultSet[BeautifulSoup]]:
    params = {
        "searchtype": "ANY",
        "query_type": "queryCarrierSnapshot",
        "query_param": "MC_MX",
        "query_string": mc_id
    }

    html = get_html_from_url("https://safer.fmcsa.dot.gov/query.asp", params)
    if html is None:
        return None
    all_td_element = process_html_with_soup(html, "td", {"class": "queryfield", "valign": "top"}, True)
    return all_td_element


def get_mc_id_user_info(us_dot: int) -> Optional[ResultSet[BeautifulSoup]]:
    params = {
        "SearchType": "DOT",
        "DOTNumber": us_dot,
        "Name": "",
        "ServiceCenter": "",
        "USState": "",
        "Country": "",
        "submit": "Search"
    }
    html = get_html_from_url(f"https://ai.fmcsa.dot.gov/SMS/Carrier/{us_dot}/CarrierRegistration.aspx", params)
    if html is None:
        return None
    info_elements = process_html_with_soup(html, "ul", {"class": "col1"}, False)
    if info_elements is None:
        return None
    return info_elements


def save_info_in_file(file: IO, user_info: list, mc_id: str):
    print(f"Downloading Info From MC_ID {mc_id}")
    file.write(str(user_info) + "\n")
    file.flush()


def get_user_info_list(file: IO, mc_number_list: list):
    for mc_number in mc_number_list:
        all_td_element = get_mc_record_from_mc_id(mc_number)
        if all_td_element is None:
            print("MC RECORDS NOT FOUND.. Checking Next MC_ID")
            continue
        us_dot = found_us_dot(all_td_element)
        if us_dot == -1:
            print("US_DOT NOT FOUND.. Checking Next MC_ID")
            continue
        info_elements = get_mc_id_user_info(us_dot)
        if info_elements is None:
            print("User Info Not Found.... Checking Next MC_ID")
            continue
        info_list = get_info_list(info_elements)
        if info_list is None:
            print("Checking Next MC_NUMBER")
            continue
        save_info_in_file(file, info_list, mc_number)


def main(file: IO):
    table_data = get_today_mc_register_menu()
    try:
        mc_number_elements = get_selected_register_list(table_data[0].input["value"])
    except Exception as e:
        print("Couldn't Get Desired Page....Change IP And Try Again....", e)
        return
    mc_number_list = get_mc_id_list_from_html(mc_number_elements)
    get_user_info_list(file, mc_number_list)


if __name__ == "__main__":
    file_name = "data.txt"
    file = open(file_name, "a")
    main(file)
    print("Saving File To CSV....")
    save_into_csv(file_name)
