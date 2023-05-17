import json
from lxml import etree


def rtv_with_xpath(html_to_extract):
    # Parse the HTML using lxml
    root = etree.HTML(html_to_extract)

    title = root.xpath('//h1/text()')[0]

    subtitle = root.xpath('//div[@class="subtitle"]/text()')[0]

    author = root.xpath('//div[@class="author-name"]/text()')[0]

    published_time = root.xpath('//div[@class="publish-meta"]/text()')[0].strip()

    lead = root.xpath('//p[@class="lead"]/text()')[0]

    content = root.xpath('//article[@class="article"]//p/text()')

    return json.dumps({"title": title,
                       "subtitle": subtitle,
                       "author": author,
                       "published_time": published_time,
                       "lead": lead,
                       "content": content
                       }, ensure_ascii=False, indent=2)


def overstock_with_xpath(html_to_extract):
    # Parse the HTML using lxml
    root = etree.HTML(html_to_extract)

    titles = root.xpath('//td[@valign]/a/b/text()')

    list_prices = root.xpath('//td[@align="left" and @nowrap="nowrap"]/s/text()')

    prices = root.xpath('//td[@align="left" and @nowrap="nowrap"]/span[@class="bigred"]/b/text()')

    savings = root.xpath('//td[@align="left" and @nowrap="nowrap"]/span[@class="littleorange"]/text()')
    for i, item in enumerate(savings):
        savings[i] = item.split()[0]

    saving_percent = root.xpath('//td[@align="left" and @nowrap="nowrap"]/span[@class="littleorange"]/text()')
    for i, item in enumerate(saving_percent):
        saving_percent[i] = item.split()[1]

    contents = root.xpath('//td[@valign="top"]/span[@class="normal"]/text()')
    for i, item in enumerate(contents):
        contents[i] = item.replace('\n', '')

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
    return json.dumps(data, ensure_ascii=False, indent=2)


def nepremicnine_with_xpath(html_to_extract):
    root = etree.HTML(html_to_extract)

    location = root.xpath('//h2//span[@class="title"]/text()')
    listing_type = root.xpath('//span[contains(@class, "posr")]/text()')
    estate_type = root.xpath('//span[contains(@class, "vrsta")]/text()')
    year = root.xpath('//span[contains(@class, "atribut leto")]/strong/text()')
    price = root.xpath('//span[contains(@class, "cena")]/text()')
    area = root.xpath('//span[contains(@class, "velikost")]/text()')
    description = root.xpath('//div[contains(@class, "kratek") and contains(@itemprop, "description")]/text()')
    image_url = root.xpath('//a//img[1][@data-src]/@data-src')

    data = []
    for i in range(len(location)):
        data.append({
            "location": location[i].rsplit(",")[0],
            "listing_type": listing_type[i],
            "estate_type": estate_type[i],
            "year": int(year[i]),
            "price": float(price[i].rsplit(" ")[0].replace(".", "").replace(",", ".")),
            "area": float(area[i].rsplit(" ")[0].replace(".", "").replace(",", ".")),
            "description": description[i],
            "image_url": image_url[i] if "/images" not in image_url[i] else None
        })

    return json.dumps(data, ensure_ascii=False, indent=2)
