import re
import json
import argparse
import os


# Get arguments
parser = argparse.ArgumentParser()
parser.add_argument("--method", default="A")
args = parser.parse_args()


# Get pages
list_of_pages = []
for file in os.listdir(r"..\input-extraction"):
    if file.endswith(".html"):
        with open(rf"..\input-extraction/{file}", "r", encoding="utf-8") as f:
            list_of_pages.append(f.read())


def rtv_with_regex(html_to_extract):
    title_match = re.search(r'<title>\s*(.+?)\s*</title>', html_to_extract)
    title = None
    if title_match:
        title = title_match.group(1)

    subtitle_match = re.search(r'<div class="subtitle">\s*(.+?)\s*</div>', html_to_extract)
    subtitle = None
    if subtitle_match:
        subtitle = subtitle_match.group(1)

    author_match = re.search(r'<div class="author-name">\s*(.+?)\s*</div>', html_to_extract)
    author = None
    if author_match:
        author = author_match.group(1)

    published_time_match = re.search(r'<div class="publish-meta">\s*(.+?)\s*<br>', html_to_extract)
    published_time = None
    if published_time_match:
        published_time = published_time_match.group(1)

    lead_match = re.search(r'<p class="lead">\s*(.+?)\s*</p>', html_to_extract)
    lead = None
    if lead_match:
        lead = lead_match.group(1)

    # TODO: write content regex
    content_match = re.search(r'<article class="article">\s*(.+?)\s*</article>', html_to_extract)
    content = None
    if content_match:
        content = content_match.group(1)

    return json.dumps({"title": title,
                       "subtitle": subtitle,
                       "author": author,
                       "published_time": published_time,
                       "lead": lead,
                       "content": content}, ensure_ascii=False)


if __name__ == '__main__':
    if args.method == "A" or args.method == "a":
        for page in list_of_pages:
            regex_json = rtv_with_regex(page)
            print(regex_json)

    elif args.method == "B" or args.method == "b":
        print("Not implemented")

    elif args.method == "C" or args.method == "c":
        print("Not implemented")

    else:
        print("Bad argument, this program only excepts the following arguments: \n"
              "'A' or 'a' for Regex, 'B' or 'b' for XPath and 'C' or 'c' for RoadRunner extraction")
