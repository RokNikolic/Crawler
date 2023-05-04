import re
import json


def rtv_with_regex(html_to_extract):
    html_to_extract = re.sub('\n', ' ', html_to_extract)

    title_match = re.search(r'<h1>\s*(.+?)\s*</h1>', html_to_extract)
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

    content = re.findall(r'<article class="article">.*?<p[^>]*>(.*?)</p>[\s\n\t]*(?:\t|<figure class="mceNonEditable)', html_to_extract, re.DOTALL)
    for i, item in enumerate(content):
        content[i] = re.sub(r'<.*?>', '', item.strip())

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

    data = []
    for i in range(len(titles)):
        data.append({
            "title": titles[i],
            "list_price": list_prices[i],
            "price": prices[i],
            "saving": savings[i],
            "saving_percent": saving_percent[i],
            "content": contents[i]
        })
    return json.dumps(data, ensure_ascii=False)


def nepremicnine_with_regex(html_to_extract):
    html_to_extract = re.sub('\n', ' ', html_to_extract)

    print(html_to_extract)

    location = re.findall(r'<h2.*?<span class="title".*?>(.*?)[<|,]', html_to_extract)

    listing_type = re.findall(r'<span class="posr.*?>(.+?):', html_to_extract)

    estate_type = re.findall(r'<span class="vrsta.*?>(.+?)<', html_to_extract)

    year = re.findall(r'<span class="atribut leto.*?<strong>(.+?)<', html_to_extract)

    price = re.findall(r'<span class="cena.*?>(.+?)\s', html_to_extract)

    area = re.findall(r'<span class="velikost.*?><span></span>(.+?)\s', html_to_extract)

    description = re.findall(r'<div class="kratek.*?itemprop="description.*?>(.+?)<', html_to_extract)

    image_url = re.findall(r'<a.*?data-src="(.*?)"', html_to_extract)

    data = []
    for i in range(len(location)):
        data.append({
            "location": location[i],
            "listing_type": listing_type[i],
            "estate_type": estate_type[i],
            "year": int(year[i]),
            "price": float(price[i].replace(".", "").replace(",", ".")),
            "area": float(area[i].replace(".", "").replace(",", ".")),
            "description": description[i],
            "image_url": image_url[i] if "/images" not in image_url[i] else None
        })

    return data

