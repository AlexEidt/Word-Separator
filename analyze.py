"""
Alex Eidt

analyze.py takes in user data to customize the word separator algorithm
and has the user enter the strings they'd like to be separated.
"""

import os
import json
import pandas as pd
from parse import parse
from process import create_dfs


def process(text, data=None):
    """
    Processes the given 'text' which is a string with no punctuation
    or spaces.

    Parameters:

    text: Text from user input.

    data: Optional. If the user wishes to 'train' the algorithm based on their
          own word set, they can pass that in as a string.
    """
    current_dir = set(os.listdir())
    if 'words.csv' not in current_dir:
        words_df = parse(data)
    else:
        words_df = pd.read_csv('words.csv', index_col=0, keep_default_na=False)

    if 'word_length.csv' not in current_dir or \
        'letters.csv' not in current_dir or \
        'letterMap.json' not in current_dir:
        create_dfs(words_df)

    word_length_df = pd.read_csv('word_length.csv', index_col=0, keep_default_na=False)
    letter_df = pd.read_csv('letters.csv', index_col=0, keep_default_na=False)
    
    with open('letterMap.json', mode='r') as f:
        letter_map = json.load(f)

    return find_words(text, word_length_df, letter_df, letter_map)


def find_words(sample, word_length_df, letter_df, letter_map):
    """
    The word separator algorithm is implemented here.

    Parameters:

    sample: The input text from the user
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

    traverse(sample, word_graph)

    output = []
    # Find the best path through the graph to create the sentence
    def best_path(graph):
        if graph:
            key_map = {}
            for key in graph:
                word, priority = key.split('-', 1)
                priority = int(priority)
                while priority in key_map:
                    priority += 1
                key_map[priority] = word
            # Go to word with largest score first
            for key in sorted(key_map, reverse=True):
                output.append(key_map[key])
                if ''.join(output) == sample:
                    print(' '.join(output))
                    break
                best_path(graph[f'{key_map[key]}-{key}'])
        output.pop()

    best_path(word_graph)


if __name__ == '__main__':
    print('Welcome to the Word Separator!\n')
    print("Enter a string of words below. If you enter a word that isn't in words.csv, then the program will crash!\n")
    print('Example:')
    print('\thellotherehowareyou -> hello there how are you\n')
    print("If you'd like to train the algorithm based on your own data set, delete words.csv from")
    print('this directory and enter the file name containing lots of words separated by spaces.')
    print('The more words there are, the better the algorithm will be.')
    file_name = input('Enter File Name (Press Enter/Return to skip): ')

    text = None
    if file_name:
        with open(file_name, mode='r') as f:
            f.read()

    cont = 'y'
    while cont:
        word = input('Enter a series of words with no punctuation or spaces: ')
        word = word.replace(' ', '').lower()
        process(word, data=text)
        cont = input('Continue? (Press enter to quit, any other key to continue): ')
