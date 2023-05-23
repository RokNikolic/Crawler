import sqlite3
import os

from utils import preprocess_text
from stopwords import stop_words_slovene

if __name__ == "__main__":
    # Check if sqlite3 database exists
    if os.path.exists('inverted-index.db'):
        print('Database already exists.')
        conn = sqlite3.connect('inverted-index.db')
        c = conn.cursor()
    else:
        print('Creating database.')
        conn = sqlite3.connect('inverted-index.db')
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IndexWord (
          word TEXT PRIMARY KEY
        );''')

        c.execute('''
        CREATE TABLE Posting (
          word TEXT NOT NULL,
          documentName TEXT NOT NULL,
          frequency INTEGER NOT NULL,
          indexes TEXT NOT NULL,
          PRIMARY KEY(word, documentName),
          FOREIGN KEY (word) REFERENCES IndexWord(word)
        );
                     ''')
        conn.commit()

    # Get all the files in data and build the index
    for root, dirs, files in os.walk('../data'):
        for file in files:
            print('Indexing file: ' + file)
            # Open the file
            with open(os.path.join(root, file), 'r', encoding='utf8') as f:
                # Read the file
                raw_text = f.read()
                words = preprocess_text(raw_text)

                # Only include words that are not stop words
                words_without_stop = [word for word in words if word not in stop_words_slovene]

                unique_words = set(words_without_stop)
                # For each unique word, get the frequency and indexes
                for word in unique_words:
                    frequency = words_without_stop.count(word)
                    indexes = [i for i, x in enumerate(words) if x == word]

                    # Check if word is already in the database
                    c.execute('''
                    SELECT word
                    FROM IndexWord
                    WHERE word = ?
                    ''', (word,))
                    if c.fetchone() is None:
                        # Insert into the database
                        c.execute('''
                        INSERT INTO IndexWord (word)
                        VALUES (?)
                        ''', (word,))
                    # Insert word, documentName, frequency, indexes
                    c.execute('''
                    INSERT INTO Posting (word, documentName, frequency, indexes)
                    VALUES (?, ?, ?, ?)
                    ''', (word, os.path.join(root, file), frequency, str(indexes)))

                    conn.commit()
    conn.close()




