import threading
from psycopg2.pool import ThreadedConnectionPool


lock = threading.Lock()
pool = ThreadedConnectionPool(1, 1000, host="localhost", user="user", password="secret")


def get_connection():
    return pool.getconn()


def get_page(conn, url):
    cur = conn.cursor()
    query = f"SELECT * FROM crawldb.page WHERE url = {url}"
    result = cur.execute(query)
    return result


def get_site(conn, domain):
    cur = conn.cursor()
    query = f"SELECT * FROM crawldb.site WHERE \"domain\" = {domain}"
    result = cur.execute(query)
    return result


def insert_site(conn, site_json):
    with lock:
        cur = conn.cursor()
        query = f"""
        -- Insert a new site into the database
        INSERT INTO crawldb.site ("domain", robots_content, sitemap_content)
        VALUES (
            {site_json['domain']},
            {site_json['robots']},
            {site_json['sitemap']}
        );
        """
        cur.execute(query)


def insert_page(conn, page_json):
    with lock:
        cur = conn.cursor()
        query = f"""
        -- Insert a new page for the given domain and page type code
        INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) 
        VALUES (
            (SELECT id FROM crawldb.site WHERE "domain" = {page_json['domain']}),
            {page_json['page_type_code']},
            {page_json['url']}, -- Replace with actual URL for the new page
            {page_json['html_content']}, -- Replace with actual HTML content for the new page
            {page_json['http_status_code']}, -- Replace with actual HTTP status code for the new page
            {page_json['accessed_time']}
        );
        """
        cur.execute(query)


def insert_image(conn, image_json):
    with lock:
        cur = conn.close()
        query = f"""
        -- Insert a new image for a given page
        INSERT INTO crawldb.image (page_id, filename, content_type, "data", accessed_time)
        VALUES (
            {image_json['page_id']},
            {image_json['filename']},
            {image_json['content_type']},
            {image_json['data']},
            {image_json['accessed_time']}
        );
        """
        cur.execute(query)


def insert_page_data(conn, page_data_json):
    with lock:
        cur = conn.close()
        query = f"""
        -- Insert a new page data object for a given page
        INSERT INTO crawldb.page_data (page_id, data_type_code, "data")
        VALUES (
            {page_data_json['page_id']},
            {page_data_json['data_type_code']},
            {page_data_json['data']}
        );
        """
        cur.execute(query)


def insert_link(conn, link_json):
    with lock:
        cur = conn.close()
        query = f"""
        -- Insert a new link
        INSERT INTO crawldb.link (from_page, to_page)
        VALUES (
            {link_json['from_page']},
            {link_json['to_page']}
        );
        """
        cur.execute(query)



