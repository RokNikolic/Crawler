import re
import json


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


def overstock_with_regex(html_to_extract):
    titles = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    # TODO: vsa data razen title
    list_price = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    price = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    saving = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    saving_percent = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    content = re.findall(r'<td valign="top">\s*<a href=\s*.+?\s*<b>\s*(.+?)\s*</b></a>', html_to_extract)

    return json.dumps({"titles": titles,
                       "list_price": list_price,
                       "price": price,
                       "saving": saving,
                       "saving_percent": saving_percent,
                       "content": content
                       }, ensure_ascii=False)
