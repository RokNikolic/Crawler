import argparse
import os
from Regex import rtv_with_regex, overstock_with_regex
from XPath import rtv_with_xpath, overstock_with_xpath
from RoadRunner import rtv_with_road_runner, overstock_with_road_runner


# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument("--method", default="A")
args = parser.parse_args()

# Get RTV pages
list_of_rtv_pages = []
for file in os.listdir(r"..\input-extraction\rtv"):
    if file.endswith(".html"):
        with open(rf"..\input-extraction\rtv\{file}", "r", encoding="utf-8") as f:
            html = f.read()
            list_of_rtv_pages.append(html)

# Get Overstock pages
list_of_overstock_pages = []
for file in os.listdir(r"..\input-extraction\overstock"):
    if file.endswith(".html"):
        with open(rf"..\input-extraction\overstock\{file}", "r") as f:
            html = f.read()
            list_of_overstock_pages.append(html)


if __name__ == '__main__':
    if args.method == "A" or args.method == "a":
        for page in list_of_rtv_pages:
            json = rtv_with_regex(page)
            print(f"Regex RTV: {json}")

        for page in list_of_overstock_pages:
            json = overstock_with_regex(page)
            print(f"Regex Overstock: {json}")

    elif args.method == "B" or args.method == "b":
        for page in list_of_rtv_pages:
            json = rtv_with_xpath(page)
            print(f"XPath RTV: {json}")

        for page in list_of_overstock_pages:
            json = overstock_with_xpath(page)
            print(f"XPath Overstock: {json}")

    elif args.method == "C" or args.method == "c":
        for page in list_of_rtv_pages:
            json = rtv_with_road_runner(page)
            print(f"RoadRunner RTV: {json}")

        for page in list_of_overstock_pages:
            json = overstock_with_road_runner(page)
            print(f"RoadRunner Overstock: {json}")

    else:
        print("Bad argument, this program only excepts the following arguments: \n"
              "'A' or 'a' for Regex, 'B' or 'b' for XPath and 'C' or 'c' for RoadRunner extraction")
