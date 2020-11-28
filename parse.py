"""
Alex Eidt

parse.py extracts all the text from every text file found on
http://textfiles.com/stories/. Multi-threading is used to speed
up the data collection process.
"""

import re
import requests
import concurrent.futures as cf
from pandas import DataFrame
from collections import Counter
from bs4 import BeautifulSoup

URL = 'http://textfiles.com/stories/'

def parse(text_data=None):
    """
    Parses all text files on URL and removes non-alphabetic characters
    for later processing.

    Parameters:

    text_data: Optional parameter. If you which to train the algorithm based on
               a certain text, pass this text as a string into parse.

    Currently only supports English characters.

    Returns a pandas DataFrame with a list of all words found in the
    text files along with the number of times these words appeared.
    """
    # data stores all stories.
    data = []
    if text_data is None:
        text = BeautifulSoup(requests.get(URL).text, features='lxml')
        

        # Use threading to extract each story.
        with cf.ThreadPoolExecutor() as executor:
            results = [
                executor.submit(
                    lambda url: requests.get(url).text, 
                    f"{URL}{link['href']}"
                )
                for link in text.find_all('a') if '.' in link['href']
            ]
            for result in cf.as_completed(results):
                data.append(result.result())
    else:
        data.append(text_data)

    # Remove ,.'";:?!()-\n from the text.
    text = re.sub(r'[\,\'\"\;\:\?\!\(\)\<\>\_\d]+', '', ' '.join(data).replace('\n', ' '))
    del data
    text = re.sub(r'[\-\.]+', ' ', text)
    text = text.lower()
    text = text.split(' ')
    text = list(
        filter(
            # Filter out entries that contain any characters other than lowercase letters.
            lambda x: not re.search(r'[^a-z]', x), 
            # Filter out empty entries
            filter(None, text)
        )
    )

    # DataFrame mapping words to their count.
    words_df = DataFrame.from_dict(
        dict(Counter(text)), orient='index', columns=['Count']
    )
    # Remove all words that only appear once
    words_df = words_df[words_df['Count'] > 1]
    # For English, filter out all one letter words that aren't A or I
    words_df = words_df[
        (words_df.index.str.len() > 1) | (words_df.index == 'i') | (words_df.index == 'a')
    ]

    words_df.to_csv('words.csv')

    return words_df


if __name__ == '__main__':
    words_df = parse()