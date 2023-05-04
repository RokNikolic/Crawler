import argparse
import os
from Regex import rtv_with_regex, overstock_with_regex
from XPath import rtv_with_xpath, overstock_with_xpath
from RoadRunner import create_site_wrapper


# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument("--method", default="a")
args = parser.parse_args()

# Get RTV pages
list_of_rtv_pages = []
path_to_rtv = os.path.join(os.getcwd(), '..', 'input-extraction', 'rtv')

for file in os.listdir(path_to_rtv):
    if file.endswith(".html"):
        with open(os.path.join(path_to_rtv, f'{file}'), "r", encoding="utf-8") as f:
            html = f.read()
            list_of_rtv_pages.append(html)

# Get Overstock pages
list_of_overstock_pages = []
path_to_overstock = os.path.join(os.getcwd(), '..', 'input-extraction', 'overstock')

for file in os.listdir(path_to_overstock):
    if file.endswith(".html"):
        with open(os.path.join(path_to_overstock, f'{file}'), "r", encoding='windows-1252') as f:
            html = f.read()
            list_of_overstock_pages.append(html)


if __name__ == '__main__':
    if args.method == "A" or args.method == "a":
        for i, page in enumerate(list_of_rtv_pages):
            json = rtv_with_regex(page)
            print(f"RTV page {i} with Regex: {json} \n")

        for i, page in enumerate(list_of_overstock_pages):
            json = overstock_with_regex(page)
            print(f"Overstock page {i} with Regex: {json} \n")

    elif args.method == "B" or args.method == "b":
        for i, page in enumerate(list_of_rtv_pages):
            json = rtv_with_xpath(page)
            print(f"RTV page {i} with XPath: {json} \n")

        for i, page in enumerate(list_of_overstock_pages):
            json = overstock_with_xpath(page)
            print(f"Overstock page {i} with XPath: {json} \n")

    elif args.method == "C" or args.method == "c":
        create_site_wrapper(list_of_overstock_pages, "overstock")
        print(f"Overstock page with RoadRunner \n")
        create_site_wrapper(list_of_rtv_pages, "rtvslo")
        print(f"RTV page with RoadRunner \n")

    else:
        print("Bad argument, this program only excepts the following arguments: \n"
              "'A' or 'a' for Regex, 'B' or 'b' for XPath and 'C' or 'c' for RoadRunner extraction, \n"
              "you must also use the --method flag to input these arguments in this manor: \n"
              "python run-extraction.py --method A")
