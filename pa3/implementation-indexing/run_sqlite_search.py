# -*- coding: UTF-8 -*-
# This is for shell

import argparse
import os
import sqlite3
import re

from time import perf_counter

from utils import preprocess_text, print_output
from stopwords import stop_words_slovene


def indexed_search(query):
    """
    The function searches for the query in data html files.
    :param query: list of words
    :return: list of tuples (documentName, frequency, indexes)
    """

    # We will measure only the search time not the preprocessing time for printing
    start = perf_counter()
    processed_query = preprocess_text(query)

    # We should remove stop words only from the query
    processed_query = [word for word in processed_query if word not in stop_words_slovene]

    if not os.path.exists('inverted-index.db'):
        print("Call generate_index.py first to generate the index.")
        exit(-1)

    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()
    c.execute(f'''
    SELECT documentName, SUM(frequency) AS freq , GROUP_CONCAT(indexes) AS idxs
    FROM Posting
    WHERE word IN ({",".join(["?"] * len(processed_query))})
    GROUP BY documentName
    ORDER BY frequency DESC
    ''', processed_query)
    raw_results = c.fetchall()
    conn.close()

    stop = perf_counter()

    # Get Snippets for all indexes
    format_results = []
    for docname, frequencies, indexes in raw_results:
        f = open(docname, 'r', encoding='utf-8')
        tokens = preprocess_text(f.read())

        # Remove brackets from indexes
        indexes = re.sub(r'[\[\]]', '', indexes)
        indexes = [int(ind) for ind in indexes.split(',')]

        # Get Snippets for all indexes
        snippets = []
        for index in indexes:
            snippets.append(" ".join(tokens[max(index - 3, 0):min(index + 3, len(tokens))]))

        format_results.append((docname, frequencies, snippets))

    return format_results, stop - start


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Search for a query in the index.')
    parser.add_argument('query', metavar='query', type=str, nargs='+', help='query to search for')
    args = parser.parse_args()
    query = " ".join(args.query)
    results, search_time = indexed_search(query)
    print_output(query, results, search_time, output_file="results_sqlite.txt")

