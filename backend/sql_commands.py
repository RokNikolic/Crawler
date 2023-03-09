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
            return self.pool.getconn()
        except psycopg2.Error:
            print(f"Trouble returning a connection to threaded pool.")
            return None

    @staticmethod
    def get_page(conn, url):
        cur = conn.cursor()
        cur.execute("SELECT * FROM crawldb.page WHERE url = %s;", (url,))
        rows = cur.fetchall()
        return rows

    @staticmethod
    def get_site(conn, domain):
        cur = conn.cursor()
        cur.execute("SELECT * FROM crawldb.site WHERE \"domain\"  = %s", (domain,))
        rows = cur.fetchall()
        return rows

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
        with DBManager.lock:
            cur = conn.cursor()
            cur.execute("""
            -- Insert a new site into the database
            INSERT INTO crawldb.site ("domain", robots_content, sitemap_content)
            VALUES (%s, %s, %s);
            """, (site_json['domain'], site_json['robots'], site_json['sitemap']))

    @staticmethod
    def insert_page(conn, page_json):
        with DBManager.lock:
            cur = conn.cursor()
            cur.execute("""
            -- Insert a new page for the given domain and page type code
            INSERT INTO crawldb.page (site_id, page_type_code, url, html_content, http_status_code, accessed_time) 
            VALUES (
                (SELECT id FROM crawldb.site WHERE "domain" = %s),
                %s,%s,%s,%d,%s);
            """, (page_json['domain'], page_json['page_type_code'], page_json['url'], page_json['html_content'],
                  page_json['accessed_time']))

    @staticmethod
    def insert_image(conn, image_json):
        with DBManager.lock:
            cur = conn.close()
            cur.execute("""
            -- Insert a new image for a given page
            INSERT INTO crawldb.image (page_id, filename, content_type, "data", accessed_time)
            VALUES (%d, %s, %s, %s, %s);
            """, (image_json['page_id'], image_json['filename'], image_json['content_type'], image_json['data'],
                  image_json['accessed_time']))

    @staticmethod
    def insert_page_data(conn, page_data_json):
        with DBManager.lock:
            cur = conn.close()
            cur.execute("""
            -- Insert a new page data object for a given page
            INSERT INTO crawldb.page_data (page_id, data_type_code, "data")
            VALUES (%d, %s, %s);
            """, (page_data_json['page_id'], page_data_json['data_type_code'], page_data_json['data']))

    @staticmethod
    def insert_link(conn, link_json):
        with DBManager.lock:
            cur = conn.close()
            cur.execute("""
            -- Insert a new link
            INSERT INTO crawldb.link (from_page, to_page)
            VALUES (%d, %d);
            """, (link_json['from_page'], link_json['to_page']))


if __name__ == "__main__":
    # This is example to check if connection sets up and try to get rows
    handler = DBManager()
    conn = handler.get_connection()
    print(DBManager.get_all_data_types(conn))
