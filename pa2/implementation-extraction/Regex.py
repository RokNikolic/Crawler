import re
import json


def rtv_with_regex(html_to_extract):
    html_to_extract = re.sub('\n', ' ', html_to_extract)

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

    # TODO: fix content regex?
    content = re.findall(r'<article class="article">\s*(.+?)\s*</article>', html_to_extract)

    return json.dumps({"title": title,
                       "subtitle": subtitle,
                       "author": author,
                       "published_time": published_time,
                       "lead": lead,
                       "content": content
                       }, ensure_ascii=False)


def overstock_with_regex(html_to_extract):
    html_to_extract = re.sub('\n', ' ', html_to_extract)

    titles = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    list_prices = re.findall(r'<b>List Price:</b>\s*.+?\s*<s>\s*(.+?)\s*</s>', html_to_extract)

    prices = re.findall(r'<b>Price:</b>\s*.+?\s*<b>\s*(.+?)\s*</b>', html_to_extract)

    savings = re.findall(r'<b>You Save:</b>\s*.+?\s*<span class="littleorange">\s*(.+?\s)\s*.+?\s*</span>', html_to_extract)

    saving_percent = re.findall(r'<b>You Save:</b>\s*.+?\s*<span class="littleorange">\s*.+?\s*(\s.+?)\s*</span>', html_to_extract)

    contents = re.findall(r'<span class="normal">\s*(.+?)\s*<br>', html_to_extract)

    return json.dumps({"titles": titles,
                       "list_price": list_prices,
                       "price": prices,
                       "saving": savings,
                       "saving_percent": saving_percent,
                       "content": contents
                       }, ensure_ascii=False)
