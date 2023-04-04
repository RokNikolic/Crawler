import datetime
import threading

import psycopg2
from psycopg2.pool import ThreadedConnectionPool


# NOTE: This runs at import time, which is bad practice
# NOTED rewriten as a class db connection object

class DBManager:
    """
    This should be used as a singleton class that manages Database connections
    """

    lock = threading.Lock()

    def __init__(self):
        try:
            self.pool = ThreadedConnectionPool(1, 1000, host="localhost", user="crawler_db", password="crawler_db")
        except Exception as e:
            print(f"Failed to establish connection to database")
            exit(-1)

    def get_connection(self):
        """
        This function should be used upon creating a WebCrawler to establish a connection to the database
        :return: connection
        """
        try:
            connection = self.pool.getconn()
            connection.autocommit = True
            return connection
        except psycopg2.Error:
            print(f"Trouble returning a connection to threaded pool.")
            return None

    @staticmethod
    def get_page(conn, url):
        cur = conn.cursor()
        cur.execute("SELECT * FROM crawldb.page WHERE url = %s;", (url,))
        rows = cur.fetchone()
        return rows

    @staticmethod
    def get_crawled_urls(conn, url):
        cur = conn.cursor()
        cur.execute("SELECT url FROM crawldb.page WHERE page_type_code = 'HTML';", (url,))


    @staticmethod
    def get_site(conn, domain):
        cur = conn.cursor()
        cur.execute("SELECT * FROM crawldb.site WHERE \"domain\"  = %s", (domain,))
        site = cur.fetchone()
        return site

    @staticmethod
    def get_all_data_types(conn):
        cur = conn.cursor()
        cur.execute("SELECT code FROM crawldb.data_type;")
        rows = cur.fetchall()
        return rows

    @staticmethod
    def get_all_page_types(conn):
        cur = conn.cursor()
        cur.execute("SELECT code FROM crawldb.page_type;")
        rows = cur.fetchall()
        return rows

    @staticmethod
    def check_if_page_exists(conn, hashcode, url):
        """Returns page_url if there exists a page with the same hashcode but different url otherwise returns False."""
        cur = conn.cursor()
        cur.execute(f"""SELECT * from crawldb.page
            WHERE hashcode = %s AND url != %s;""", (hashcode, url))
        out = cur.fetchone()
        if out is None:
            return False
        return out[3]

    @staticmethod
    def insert_site(conn, site_json):
        """ Inserts Site into DB and returns site_id. """
        with DBManager.lock:
            cur = conn.cursor()

            # Check if domain already stored
            site = DBManager.get_site(conn, site_json['domain'])

            if site is None:
                cur.execute("""
                -- Insert a new site into the database
                INSERT INTO crawldb.site ("domain", robots_content, sitemap_content)
                VALUES (%s, %s, %s)
                RETURNING id;
                """, (site_json['domain'], site_json['robots'], site_json['sitemap']))
                site_id = cur.fetchone()
                return site_id[0]
            else:
                return site[0]

    @staticmethod
    def insert_page(conn, page_json):
        """ Inserts Page into DB and returns page_id. """
        with DBManager.lock:
            DBManager.insert_page_without_lock(conn, page_json)

    @staticmethod
    def insert_page_without_lock(conn, page_json):
        page = DBManager.get_page(conn, page_json['url'])
        cur = conn.cursor()

        if page is None:
            cur.execute("""
            INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, hashcode, http_status_code, accessed_time)
            VALUES (
                (SELECT id FROM crawldb.site WHERE "domain" = %s), %s, %s, %s, %s, %s, to_timestamp(%s));
            """, (page_json['domain'], page_json['page_type_code'], page_json['url'][:3000], page_json['html_content'],
                  page_json['hashcode'], page_json['http_status_code'], page_json['accessed_time']))
        elif page[4] is None:
            cur.execute("""
            UPDATE crawldb.page
            SET 
                site_id = (SELECT id FROM crawldb.site WHERE "domain" = %s),
                page_type_code = %s,
                html_content = %s,
                hashcode = %s,
                http_status_code = %s,
                accessed_time = to_timestamp(%s)
            WHERE url = %s
            """, (page_json['domain'], page_json['page_type_code'], page_json['html_content'], page_json['hashcode'],
                  page_json['http_status_code'], page_json['accessed_time'], page_json['url'][:3000]))
            #print(f"{datetime.datetime.now()} Finished Page insert for {page_json['url']}")
        #else:
            #print(f"{datetime.datetime.now()} Page already exists and filled.")


    @staticmethod
    def insert_image(conn, image_json, url):
        """ Inserts Img into DB and returns img_id. """
        with DBManager.lock:
            cur = conn.cursor()
            cur.execute("""
            -- Insert a new image for a given page
            INSERT INTO crawldb.image (page_id, filename, content_type, "data", accessed_time)
            VALUES (
                (SELECT id from crawldb.page WHERE url = %s), 
                %s, %s, %s, to_timestamp(%s))
            ON CONFLICT DO NOTHING;
            """, (url, image_json['filename'][:255], image_json['content_type'][:50], image_json['data'],
                  image_json['accessed_time']))
            # print(f"{datetime.datetime.now()} Finished Image insert for {url}")

    @staticmethod
    def insert_page_data(conn, page_data_json, url):
        """ Inserts PageData into DB and returns page_data_id. """
        with DBManager.lock:
            # First insert the data type if it doesn't exist
            cur = conn.cursor()
            cur.execute("""
            INSERT INTO crawldb.data_type (code)
            VALUES (%s)
            ON CONFLICT DO NOTHING;
            """, (page_data_json['data_type_code'],))

            cur = conn.cursor()
            cur.execute("""
            -- Insert a new page data object for a given page
            INSERT INTO crawldb.page_data (page_id, data_type_code, "data")
            VALUES (
                (SELECT id from crawldb.page WHERE url = %s), 
                %s, %s)
            ON CONFLICT DO NOTHING;
            """, (url, page_data_json['data_type_code'], page_data_json['data']))
            # print(f"{datetime.datetime.now()} Finished PageData insert for {url}")

    @staticmethod
    def insert_link(conn, link_json, logging=None):
        """ Inserts Link into DB. """
        with DBManager.lock:
            # Extra error handling due to some links being None
            if not link_json['to_page']:
                if logging:
                    logging.warning(f"Link to_page is None: {link_json}")
                return

            # First we must check that both pages exist
            page_to = DBManager.get_page(conn, link_json['to_page'])

            if page_to is None:
                page_raw = {
                    "html_content": None,
                    "hashcode": None,
                    "page_type_code": None,
                    "domain": None,
                    "url": link_json['to_page'],
                    "http_status_code": None,
                    "accessed_time": None
                }
                DBManager.insert_page_without_lock(conn, page_raw)

            # If page from and to point to same page
            cur = conn.cursor()
            cur.execute("""
            -- Insert a new link
            INSERT INTO crawldb.link (from_page, to_page)
            VALUES (
                (SELECT id FROM crawldb.page WHERE url = %s),
                (SELECT id FROM crawldb.page WHERE url = %s)
            )
            ON CONFLICT DO NOTHING;
            """, (link_json['from_page'], link_json['to_page']))

    @staticmethod
    def insert_all(conn, page_info, urls, imgs, logging=None):
        # First we must insert the page
        DBManager.insert_page(conn, page_info)

        # We must insert link to duplicate page if DUPLICATE found:
        if page_info['page_type_code'] == 'DUPLICATE':
            link = {
                'from_page': page_info['url'],
                'to_page': page_info['duplicate_url']
            }
            DBManager.insert_link(conn, link, logging=logging)
            return

        # We should insert page data if page is binary
        if page_info['page_type_code'] == 'BINARY':
            DBManager.insert_page_data(conn, page_info['page_data'], page_info['url'])

        # Next lets insert all urls between pages
        for link in urls:
            DBManager.insert_link(conn, link)

        # Next lets insert all images
        for img in imgs:
            DBManager.insert_image(conn, img, page_info['url'])


if __name__ == "__main__":
    # This is example to check if connection sets up and try to get rows
    handler = DBManager()
    conn = handler.get_connection()
    print(DBManager.get_all_data_types(conn))
