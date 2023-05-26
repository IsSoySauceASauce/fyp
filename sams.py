import pandas as pd
import matplotlib.pyplot as plt
import string
import pickle
from datetime import datetime, timedelta
import numpy as np
import malaya
import re
from statistics import mean
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

mly = malaya.sentiment.multinomial()
sia = SentimentIntensityAnalyzer()

malay_stopwords = np.load('data/malay_stopwords.npy')
positive_malay_words = np.load('data/positive_malay_words.npy')
negative_malay_words = np.load('data/negative_malay_words.npy')
positive_word_top_100 = np.load('data/positive_word_top_100.npy')
negative_word_top_100 = np.load('data/negative_word_top_100.npy')
learned_positive_words = np.load('data/learned_positive_words.npy')
learned_negative_words = np.load('data/learned_negative_words.npy')

def get_features(tweet):
    features = dict()
    top_positive_words_frequency = 0
    top_negative_words_frequency = 0
    positive_malay_words_frequency = 0
    negative_malay_words_frequency = 0
    learned_positive_words_frequency = 0
    learned_negative_words_frequency = 0
    english_compound_scores = list()
    english_positive_scores = list()
    english_negative_scores = list()
    malaya_positive_scores = list()
    malaya_negative_scores = list()

    for sentence in nltk.sent_tokenize(tweet):
        sentence = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+','', sentence)
        sentence = re.sub('(@[A-Za-z0-9_]+)','', sentence)

        for word in nltk.word_tokenize(sentence):
            if word.lower() in positive_word_top_100:
                top_positive_words_frequency += 1
            if word.lower() in negative_word_top_100:
                top_negative_words_frequency += 1

            if word.lower() in positive_malay_words:
                positive_malay_words_frequency += 1
            if word.lower() in negative_malay_words:
                negative_malay_words_frequency += 1

            if word.lower() in learned_positive_words:
                learned_positive_words_frequency += 1
            if word.lower() in learned_negative_words:
                learned_negative_words_frequency += 1

        malaya_positive_scores.append(mly.predict_proba([sentence])[0]["positive"])
        malaya_negative_scores.append(mly.predict_proba([sentence])[0]["negative"])

        english_compound_scores.append(sia.polarity_scores(sentence)["compound"])
        english_positive_scores.append(sia.polarity_scores(sentence)["pos"])
        english_negative_scores.append(sia.polarity_scores(sentence)["neg"])

    features["malaya_mean_positive"] = mean(malaya_positive_scores)
    features["malaya_mean_negative"] = mean(malaya_negative_scores)
    
    features["english_mean_compound"] = mean(english_compound_scores) + 1
    features["english_mean_positive"] = mean(english_positive_scores)
    features["english_mean_negative"] = mean(english_negative_scores)
    
    features["top_positive_words_frequency"] = top_positive_words_frequency
    features["top_negative_words_frequency"] = top_negative_words_frequency

    features["positive_malay_words_frequency"] = positive_malay_words_frequency
    features["negative_malay_words_frequency"] = negative_malay_words_frequency

    features["learned_positive_words_frequency"] = learned_positive_words_frequency
    features["learned_negative_words_frequency"] = learned_negative_words_frequency

    return features

def predict(model_path, text):
    classifier = pickle.load(open(model_path, 'rb'))
    sentiment = classifier.classify(get_features(text))

    return sentiment