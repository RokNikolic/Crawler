import os
import sys

import nltk
nltk.download('punkt')
nltk.download('stopwords')

from bs4 import BeautifulSoup


def preprocess_text(raw_text):
    """
    The function preprocesses the text.
    :param raw_text: input is html file
    :return: processed_tokens, tokens
    """

    text = BeautifulSoup(raw_text, "html.parser").get_text()

    tokens = nltk.tokenize.word_tokenize(text,
                    language="slovene", preserve_line=False)
    
    processed_tokens = [t.lower() for t in tokens]

    return processed_tokens


def print_output(query, results, search_time, output_file="output.txt"):
    """
    The function prints the output of the search.
    :param output_file: output file name
    :param query: list of words
    :param results: list of tuples (documentName, frequency, snippets)
    :param search_time: time of the search
    """
    sys.stdout = open(output_file, "w", encoding="utf-8")

    print(f"Results for query: \"{query}\"\n")
    print(f"\tResults found in {search_time*1000:.1f}ms.\n")

    if len(results) > 0:
        longest_document_name = max([len(result[0]) for result in results])
    else:
        longest_document_name = 8

    # Sort results by frequency
    results = sorted(results, key=lambda x: x[1], reverse=True)

    print(f"\tFrequencies {'Document': <{longest_document_name}} Snippet")
    print(f"\t{'-' * 11} {'-' * (longest_document_name+1)} {'-' * 59}")
    for doc_name, frequency, snippets in results:
        print(f"\t{frequency: <11} {doc_name: <{longest_document_name}} {'...'.join(snippets)}")

    sys.stdout.close()
    sys.stdout = sys.__stdout__
