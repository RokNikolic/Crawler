import threading

import psycopg2
from psycopg2.pool import PoolError, ThreadedConnectionPool


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
        except PoolError | ConnectionError:
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
            INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time)
            VALUES (
                (SELECT id FROM crawldb.site WHERE "domain" = %s), %s, %s, %s, %s, to_timestamp(%s));
            """, (page_json['domain'], page_json['page_type_code'], page_json['url'], page_json['html_content'],
                  page_json['http_status_code'], page_json['accessed_time']))
        else:
            cur.execute("""
            UPDATE crawldb.page
            SET 
                site_id = (SELECT id FROM crawldb.site WHERE "domain" = %s),
                page_type_code = %s,
                html_content = %s,
                http_status_code = %s,
                accessed_time = to_timestamp(%s)
            WHERE url = %s
            """, (page_json['domain'], page_json['page_type_code'], page_json['html_content'],
                  page_json['http_status_code'], page_json['accessed_time'], page_json['url']))
        print(f"Finished Page insert for {page_json['url']}")

    @staticmethod
    def insert_image(conn, image_json):
        """ Inserts Img into DB and returns img_id. """
        with DBManager.lock:
            cur = conn.cursor()
            cur.execute("""
            -- Insert a new image for a given page
            INSERT INTO crawldb.image (page_id, filename, content_type, "data", accessed_time)
            VALUES (
                (SELECT id from crawldb.page WHERE url = %s), 
                %s, %s, %s, %s);
            """, (image_json['page_url'], image_json['filename'], image_json['content_type'], image_json['data'],
                  image_json['accessed_time']))

    @staticmethod
    def insert_page_data(conn, page_data_json):
        """ Inserts PageData into DB and returns page_data_id. """
        with DBManager.lock:
            cur = conn.cursor()
            cur.execute("""
            -- Insert a new page data object for a given page
            INSERT INTO crawldb.page_data (page_id, data_type_code, "data")
            VALUES (%d, %s, %s);
            """, (page_data_json['page_id'], page_data_json['data_type_code'], page_data_json['data']))

    @staticmethod
    def insert_link(conn, link_json):
        """ Inserts Link into DB. """
        with DBManager.lock:

            # First we must check that both pages exist
            page_from = DBManager.get_page(conn, link_json['from_page'])
            page_to = DBManager.get_page(conn, link_json['to_page'])

            if page_to is None:
                page_raw = {
                    "html_content": None,
                    "page_type_code": None,
                    "domain": None,
                    "url": link_json['to_page'],
                    "http_status_code": None,
                    "accessed_time": None
                }
                DBManager.insert_page_without_lock(conn, page_raw)
            page_to = DBManager.get_page(conn, link_json['to_page'])
            print(f"From {page_from[3]} To {page_to[3]}")

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
    def insert_all(conn, page_info, urls, imgs):
        # First we must insert the page
        DBManager.insert_page(conn, page_info)

        # Next lets insert all urls between pages
        for link in urls:
            DBManager.insert_link(conn, link)

        # Next lets insert all images
        for img in imgs:
            DBManager.insert_image(conn, img)


if __name__ == "__main__":
    # This is example to check if connection sets up and try to get rows
    handler = DBManager()
    conn = handler.get_connection()
    print(DBManager.get_all_data_types(conn))
