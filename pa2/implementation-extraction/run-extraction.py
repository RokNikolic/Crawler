import argparse
import os
from Regex import rtv_with_regex, overstock_with_regex, nepremicnine_with_regex
from XPath import rtv_with_xpath, overstock_with_xpath, nepremicnine_with_xpath
from RoadRunner import create_site_wrapper



def load_pages(site_dir, encoding="utf-8"):

    pages = []
    for file in os.listdir(site_dir):
        if file.endswith(".html"):
            with open(os.path.join(site_dir, f'{file}'), "r", encoding=encoding) as f:
                html = f.read()
                pages.append(html)

    return pages



if __name__ == '__main__':

    # Get arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", default="a")
    args = parser.parse_args()


    # Load HTML pages
    base_dir = os.path.join(os.getcwd(), '..', 'input-extraction')
    rtv_pages = load_pages(os.path.join(base_dir, 'rtv'))
    overstock_pages = load_pages(os.path.join(base_dir, 'overstock'), encoding='windows-1252')
    nepremicnine_pages = load_pages(os.path.join(base_dir, 'nepremicnine'))

    # Run extraction
    if args.method in ["A", "a"]:
        print("hello")
        for i, page in enumerate(rtv_pages):
            print("world")
            json = rtv_with_regex(page)
            print(f"RTV page {i} with Regex: {json} \n")

        for i, page in enumerate(overstock_pages):
            json = overstock_with_regex(page)
            print(f"Overstock page {i} with Regex: {json} \n")

        for i, page in enumerate(nepremicnine_pages):
            json = nepremicnine_with_regex(page)
            print(f"Nepremicnine page {i} with Regex: {json} \n")

    elif args.method in ["B", "b"]:
        for i, page in enumerate(rtv_pages):
            json = rtv_with_xpath(page)
            print(f"RTV page {i} with XPath: {json} \n")

        for i, page in enumerate(overstock_pages):
            json = overstock_with_xpath(page)
            print(f"Overstock page {i} with XPath: {json} \n")

        for i, page in enumerate(nepremicnine_pages):
            json = nepremicnine_with_xpath(page)
            print(f"Nepremicnine page {i} with XPath: {json} \n")   

    elif args.method in ["C", "c"]:
        create_site_wrapper(overstock_pages, "overstock")
        print(f"Overstock page with RoadRunner \n")
        create_site_wrapper(rtv_pages, "rtvslo")
        print(f"RTV page with RoadRunner \n")

    else:
        print("Bad argument, this program only excepts the following arguments: \n"
              "'A' or 'a' for Regex, 'B' or 'b' for XPath and 'C' or 'c' for RoadRunner extraction, \n"
              "you must also use the --method flag to input these arguments in this manor: \n"
              "python run-extraction.py --method A")
