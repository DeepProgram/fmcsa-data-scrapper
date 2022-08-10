from bs4 import BeautifulSoup, ResultSet
import requests

file = open("data.txt", "a")


def get_html_from_url(url: str, url_params: dict) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/104.0.0.0 Safari/537.36 Edg/104.0.1293.47"
    }
    try:
        response = requests.get(url, params=url_params, headers=headers)
    except requests.exceptions.Timeout:
        print("Request Timed Out.. Please Check Internet Connection Or Use A Valid Proxy..")
        return "-1"
    except requests.exceptions.TooManyRedirects:
        print("Url Is Not Valid.. Please check the demo url in github and try url like that..")
        return "-1"
    except requests.exceptions.RequestException as e:
        print("Error Occurred While Fetching Data ", e)
        return "-1"
    return response.text


def process_html_with_soup(html_string: str, tag: str, attributes: dict, find_all: bool) -> ResultSet[BeautifulSoup]:
    soup = BeautifulSoup(html_string, "html.parser")
    processed_html = None
    if find_all:
        try:
            processed_html = soup.find_all(tag, attrs=attributes)
        except Exception as e:
            print("Could Not Found Desired Element..Try After Changing IP..", e)
    else:
        try:
            processed_html = soup.find(tag, attrs=attributes).contents
        except Exception as e:
            print("Could Not Found Desired Element..Try After Changing IP..", e)
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


def get_info_list(all_info: ResultSet[BeautifulSoup]) -> list:
    extracted_info_list = []
    for info_index in range(len(all_info)):
        try:
            label_value = all_info[info_index].label.text.strip()
            span_value = all_info[info_index].span.text.strip()
        except AttributeError:
            info_index += 1
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
                city = all_info[info_index].span.contents[2].split(",")[0]
                state = all_info[info_index].span.contents[2].split(",")[1].strip().split(" ")[0]
            except Exception as e:
                print("Could Not Find Desired Value....", e)
                return [-1]
            extracted_info_list.insert(4, city)
            extracted_info_list.insert(5, state)

    return extracted_info_list


if __name__ == "__main__":
    params = {
        "pv_choice": "FED_REG",
        "x": "9",
        "y": "14",
        "pv_vpath": "LIVIEW"
    }
    html = get_html_from_url("https://li-public.fmcsa.dot.gov/LIVIEW/pkg_menu.prc_menu", params)
    table_data = process_html_with_soup(html, "td", {"valign": "top"}, find_all=True)
    params = {
        "pd_date": table_data[0].input["value"],
        "pv_vpath": "LIVIEW"
    }
    html = get_html_from_url("https://li-public.fmcsa.dot.gov/LIVIEW/PKG_register.prc_reg_detail", params)

    mc_number_elements = process_html_with_soup(html, "th", {"scope": "row"}, True)
    mc_number_list = []

    for mc_number_element in mc_number_elements:
        mc_number_list.append(mc_number_element.text.split("-")[1].strip())

    one_day_users_list = []
    for mc_number in mc_number_list:
        params = {
            "searchtype": "ANY",
            "query_type": "queryCarrierSnapshot",
            "query_param": "MC_MX",
            "query_string": mc_number
        }

        html = get_html_from_url("https://safer.fmcsa.dot.gov/query.asp", params)
        if html == "-1":
            continue
        all_td_element = process_html_with_soup(html, "td", {"class": "queryfield", "valign": "top"}, True)
        if all_td_element is None:
            continue
        us_dot = found_us_dot(all_td_element)
        if us_dot == -1:
            print("\n\tUS_DOT NOT FOUND.. Checking Next MC_NUMBER")
            continue

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
        if html == "-1":
            continue
        info_elements = process_html_with_soup(html, "ul", {"class": "col1"}, False)
        if info_elements is None:
            print("Checking Next MC_NUMBER")
            continue
        info_list = get_info_list(info_elements)
        if info_list[0] == -1:
            print("Checking Next MC_NUMBER")
            continue

        file.write(str(info_list) + "\n")
        file.flush()
