"""
Alex Eidt

analyze.py takes in user data to customize the word separator algorithm
and has the user enter the strings they'd like to be separated.
"""

import os
import re
import json
import pandas as pd
from parse import parse
from process import create_dfs


def get_dfs(data=None):
    """
    Parses 'word_length.csv', 'letters.csv' and 'letterMap.json' as a Data
    Structures and returns them.

    Parameters:

    data: Optional. If the user wishes to 'train' the algorithm based on their
          own word set, they can pass that in as a string.
    """
    data_dir = set(os.listdir(os.path.join(os.getcwd(), 'Data')))
    if 'words.csv' not in data_dir or data is not None:
        words_df = parse(data)
    else:
        words_df = pd.read_csv('Data/words.csv', index_col=0, keep_default_na=False)

    if 'word_length.csv' not in data_dir or \
        'letters.csv' not in data_dir or \
        'letterMap.json' not in data_dir or \
        data is not None:
        create_dfs(words_df)

    word_length_df = pd.read_csv('Data/word_length.csv', index_col=0, keep_default_na=False)
    letter_df = pd.read_csv('Data/letters.csv', index_col=0, keep_default_na=False)
    
    with open('Data/letterMap.json', mode='r') as f:
        letter_map = json.load(f)

    return word_length_df, letter_df, letter_map


def find_words(user_input, word_length_df, letter_df, letter_map):
    """
    The word separator algorithm is implemented here.

    Parameters:

    user_input: The input text from the user
    word_length_df: The DataFrame mapping word lengths to counts
    letter_df: The DataFrame containing statistics about the occurence of letters
               in the given dataset.
    letter_map: Dictionary representing graph of letters for each word in the dataset.
    """
    word_graph = {}
    # Keep track of word scores so they don't need to be recalculated
    word_scores = {}

    # Find all possible words 'text' could start based on `letter_map`
    # and return this as a list
    def get_layer(text):
        temp = letter_map
        word = []
        layer = []
        for letter in text:
            if letter in temp:
                word.append(letter)
                if '|' in temp[letter]:
                    layer.append(''.join(word))
                temp = temp[letter]
            else:
                break
        return layer

    # Returns the score for a word
    def score(word):
        score = 1
        for i in range(len(word) - 1):
            score *= letter_df.loc[word[i + 1], word[i]].squeeze()
        begin = letter_df.loc[word[0], 'letter_begin'].squeeze()
        end = letter_df.loc[word[-1], 'letter_end'].squeeze()
        score += begin + end + word_length_df.loc[len(word)].squeeze()
        return int(round(score))

    # Traverse the word graph with all possiblities of words
    def traverse(text, graph):
        layer = get_layer(text)
        if layer:
            for choice in layer:
                if choice not in word_scores:
                    word_scores[choice] = score(choice)
                key = f'{choice}-{word_scores[choice]}'
                graph[key] = {}
                traverse(text.replace(choice, '', 1), graph[key])

    # Traverse through the user input and fill up the word graph of possibilities
    traverse(user_input, word_graph)

    output = []
    # Find the best path through the graph to create the sentence
    def best_path(graph):
        if ''.join(output) == user_input:
            return ' '.join(output)
        if graph:
            key_map = {}
            for key in graph:
                word, priority = key.split('-', 1)
                priority = int(priority)
                # If two words have same priority, add 1 until priorities are unique
                while priority in key_map:
                    priority += 1
                key_map[priority] = word
            # Go to word with largest score first
            for key in sorted(key_map, reverse=True):
                output.append(key_map[key])
                so_far = best_path(graph[f'{key_map[key]}-{key}'])
                if so_far:
                    return so_far
        if output:
            output.pop()
        return None

    return best_path(word_graph)


if __name__ == '__main__':
    print('Welcome to the Word Separator!\n')
    print('Enter a string of words below.\n')
    print('Example:')
    print('\thellotherehowareyou -> hello there how are you\n')
    print("If you'd like to train the algorithm based on your own data set, place a file")
    print('containing lots of words separated by spaces in this directory and enter the file name below.')
    print('The more words there are, the better the algorithm will be.\n')

    file_name = input('Enter File Name (Press Enter/Return to skip): ')
    while file_name and file_name not in os.listdir():
        file_name = input('File not found in this directory.\nPlease enter another file name (Press Enter/Return to skip): ')

    text = None
    if file_name:
        with open(file_name, mode='r') as f:
            text = f.read()

    # Get all Data Structures required for the algorithm.
    word_length_df, letter_df, letter_map = get_dfs(text)
    del text

    word = input('Enter a series of words with no punctuation or spaces (Press Enter/Return to quit): ')
    while word:
        # Remove all spaces and non-letter characters. Make 'word' lowercase.
        word = re.sub(r'[^a-z]+', '', word.replace(' ', '').lower())
        output = find_words(word, word_length_df, letter_df, letter_map)
        if output is None:
            print('Input contains words not present in words.csv. Could not break apart string.')
        else:
            print(output)
        word = input('Enter a series of words with no punctuation or spaces (Press Enter/Return to quit): ')
