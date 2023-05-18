import sqlite3
import os

from preprocess_text import preprocess_text

if __name__ == "__main__":
    # Check if sqlite3 database exists
    if os.path.exists('index.db'):
        print('Database already exists.')
        conn = sqlite3.connect('inverted-index.db')
    else:
        print('Creating database.')
        conn = sqlite3.connect('inverted-index.db')
        c = conn.cursor()
        c.execute('''
        CREATE TABLE IndexWord (
          word TEXT PRIMARY KEY
        );
        
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
            with open(os.path.join(root, file), 'r') as f:
                # Read the file
                raw_text = f.read()
                # Split the file into words
                words = preprocess_text(raw_text)
                # Get the unique words
                unique_words = set(words)
                # For each unique word, get the frequency and indexes
                for word in unique_words:
                    # Get the frequency
                    frequency = words.count(word)
                    # Get the indexes
                    indexes = [i for i, x in enumerate(words) if x == word]
                    # Insert into the database
                    conn.execute('''
                    INSERT INTO IndexWord (word)
                    VALUES (?)
                    ''', (word,))
                    # Insert word, documentName, frequency, indexes
                    conn.execute('''
                    INSERT INTO Posting (word, documentName, frequency, indexes)
                    VALUES (?, ?, ?, ?)
                    ''', (word, file, frequency, str(indexes)))
                    conn.commit()
    conn.close()




