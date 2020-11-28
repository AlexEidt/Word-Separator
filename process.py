"""
Alex Eidt

process.py creates several Data Structures storing statistics about how
letters appear in the given text.
"""

import os
import json
import pandas as pd
from collections import Counter
from parse import parse


def create_dfs(words_df):
    """
    Based on the words in words_df, this function creates two pandas DataFrames
    and one dictionary storing information for the word list.

    A DataFrame called word_length_df is created and stored as a .csv file
    called "word_length.csv". The rows of this DataFrame contain the lengths of
    words, the column contains the number of times words of this length occur.

    A DataFrame called letter_df is created and stored as a .csv file called
    "letters.csv". The rows of this DataFrame contain all letters that occur in the
    words in words_df. There are many columns. The first column is called
    "letter_count" and contains the number of times each letter occurs in the given training
    text. The second column "letter_begin" contains the number of times each letter was the
    first letter in a word. The third column "letter_end" contains the number of times
    each letter was the last letter of a word. 
    
    The next columns after these three are all the letters found in the words in words_df.
    Along with the rows, this forms a matrix where the value at matrix[A][B]
    represents the number of times letter A was directly followed by letter B.

    The data in letter_df is used to calculated a "score" for each potential word, words
    with a higher score are used to guess the original sentence.

    A Dictionary called letter_map indirectly contains information for all words in words_df.
    It is a series of nested dictionaries representing a graph. The letter of each word is a key
    in a dictionary, and its value is another dictionary containing the next letter as a key whose
    value is the next letter in the word and so on. This graph is built up for every word in
    words_df as a way to parse each letter in the input text from the user.
    """
    # For English, filter out all words that have length 2 and occur less than 100 times
    words_df = words_df[
        (words_df.index.str.len() != 2) | (words_df['Count'] > 100)
    ]

    # All words that appear less than 15 times in total or whose length is less than 
    # 5 are filtered out.
    words_df = words_df[(words_df['Count'] > 15) | (words_df.index.str.len() >= 5)]

    text = []
    for word in words_df.index:
        for _ in range(words_df.loc[word].squeeze()):
            text.append(word)


    # Maps lengths of words to their count.
    # I.e 4 letter long words may appear 1000 times, this will be represented
    # in word_length_df as 4 -> 1000.
    word_length_df = pd.DataFrame.from_dict(
        dict(Counter(map(len, text))), orient='index', columns=['Count']
    )
    
    # Convert counts to percentages and normalizes between 0-1000.
    word_length_df['Count'] /= word_length_df['Count'].sum()
    word_length_df['Count'] *= 1000

    word_length_df.to_csv('Data/word_length.csv')
    print('word_length.csv has been created')
    del word_length_df

    letter_df = pd.DataFrame.from_dict({
        # Maps letters to number of times they appeared.
        'letter_count': dict(Counter(''.join(text))),
        # Maps each letter to the number of times it appears at the beginning of a word.
        'letter_begin': dict(Counter(map(lambda x: x[0], text))),
        # Maps each letter to the number of times it appears at the end of a word.
        'letter_end': dict(Counter(map(lambda x: x[-1], text)))
    })

    # Tracks the number of times any letter follows any other letter in a matrix.
    letter_order = {
        letter: {l: 0 for l in letter_df.index} for letter in letter_df.index
    }

    for word in text:
        for i in range(len(word) - 1):
            letter_order[word[i]][word[i + 1]] += 1

    del text

    letter_df = pd.concat(
        [letter_df, pd.DataFrame.from_dict(letter_order, orient='index').sort_index(axis=1)],
        axis=1
    )
    letter_df.fillna(0.0, inplace=True)
    del letter_order

    # Convert counts to percentages and normalizes between 0-1000
    for column in letter_df:
        letter_df[column] /= letter_df[column].sum()
        letter_df[column] *= 1000

    letter_df.sort_index(inplace=True)

    letter_df.to_csv('Data/letters.csv')
    print('letters.csv has been created')

    # Dictionary representing a directed graph that maps each letter of each word
    # to the next letter in that word and so on.
    letter_map = {}
    for word in words_df.index:
        temp = letter_map
        word_len = len(word)
        for i, letter in enumerate(word, start=1):
            if letter not in temp:
                temp[letter] = {}
            if i == word_len:
                temp[letter]['|'] = None
            temp = temp[letter]

    with open('Data/letterMap.json', mode='w') as f:
        json.dump(letter_map, f, sort_keys=True)
    
    print('letterMap.json has been created')