# -*- coding: UTF-8 -*-
# This is for shell

import argparse
import os

from time import perf_counter

from utils import preprocess_text, print_output
from stopwords import stop_words_slovene


def basic_search(query):
    """
    The function searches for the query in data html files.
    :param query: list of words
    :return: list of tuples (documentName, frequency, indexes)
    """
    start = perf_counter()
    raw_results = []
    processed_query = preprocess_text(query)

    # We should remove stop words only from the query
    processed_query = [word for word in processed_query if word not in stop_words_slovene]

    # Get all the files in data
    for root, dirs, files in os.walk('..\\data'):
        for file in files:
            f = open(os.path.join(root, file), 'r', encoding="utf8")
            raw_text = f.read()
            tokens = preprocess_text(raw_text)

            # Check if all words in query are in the file
            contains_all_words = all(word in tokens for word in processed_query)
            if contains_all_words:
                # Get the frequency for all words
                frequency = sum(tokens.count(word) for word in processed_query)
                word_indexes = [i for i, x in enumerate(tokens) if x.lower() in processed_query]

                # Add the result
                raw_results.append((os.path.join(root, file), frequency, word_indexes))

    stop = perf_counter()

    # At the end create snippets for all results
    out_results = []
    for docname, frequencies, indexes in raw_results:
        f = open(docname, 'r', encoding='utf-8')
        tokens = preprocess_text(f.read())

        # Get Snippets for all indexes
        snippets = []
        for index in indexes:
            snippets.append(" ".join(tokens[max(index - 3, 0):min(index + 3, len(tokens))]))

        out_results.append((docname, frequencies, snippets))

    return out_results, stop - start


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search for a query in the index.')
    parser.add_argument('query', metavar='query', type=str, nargs='+', help='query to search for')
    args = parser.parse_args()
    query = " ".join(args.query)
    results, search_time = basic_search(query)
    print_output(query, results, search_time, output_file="results_basic.txt")

