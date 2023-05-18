import os
import sys

import nltk
nltk.download('punkt')
nltk.download('stopwords')

from bs4 import BeautifulSoup

from stopwords import stop_words_slovene

def preprocess_text(raw_text):

    text = BeautifulSoup(raw_text, "lxml").text

    tokens = nltk.tokenize.word_tokenize(raw_text, 
                    language="slovene", preserve_line=False)
    
    tokens = [t.lower() for t in tokens]
    tokens = [t for t in tokens if t not in stop_words_slovene]
