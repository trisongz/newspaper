""" Initializes nltk with required corpus """

import nltk
from typing import List, Dict, Any

CORPUSES = {
    'corpora/brown': 'brown', # Required for FastNPExtractor
    'tokenizers/punkt': 'punkt', # Required for WordTokenizer
    'taggers/maxent_treebank_pos_tagger': 'maxent_treebank_pos_tagger', # Required for NLTKTagger
    'corpora/movie_reviews': 'movie_reviews', # Required for NaiveBayesAnalyzer
    'corpora/wordnet': 'wordnet', # Required for lemmatization and Wordnet
    'corpora/stopwords': 'stopwords'
}

"""
Prevent multiple reinitialization of the tokenizer if not needed.
"""

class Tokenizer:
    tokenizers: Dict[str, Any] = {}

    @classmethod
    def load(cls):
        for data_loc, src in CORPUSES.items():
            try:
                nltk.data.find(data_loc)
            except LookupError:
                nltk.download(src)


    @classmethod
    def get(cls, name: str, path: str):
        """ Get a Tokenizer """
        if not cls.tokenizers.get(name):
            cls.load()
            cls.tokenizers[name] = nltk.data.load(path) #nltk.data.load('tokenizers/punkt/english.pickle')
        return cls.tokenizers[name]
