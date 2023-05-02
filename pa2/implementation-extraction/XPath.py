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

    # TODO: what does content actually have to return? also it returns nothing for the second page
    content = root.xpath('//article[@class="article"]//p[@class="Body"]/text()')

    return json.dumps({"title": title,
                       "subtitle": subtitle,
                       "author": author,
                       "published_time": published_time,
                       "lead": lead,
                       "content": content
                       }, ensure_ascii=False)


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

    return json.dumps({"titles": titles,
                       "list_price": list_prices,
                       "price": prices,
                       "saving": savings,
                       "saving_percent": saving_percent,
                       "content": contents
                       }, ensure_ascii=False)

