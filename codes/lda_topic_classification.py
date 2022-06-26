import re
import numpy as np
import gensim
import gensim.corpora as corpora
from gensim.utils import simple_preprocess
from gensim.models import CoherenceModel
from gensim.models.phrases import Phrases, Phraser
from gensim.test.utils import datapath
from preprocess_email import get_email

# spacy for lemmatization
import spacy

# tokenize - break down each sentence into a list of words
def sent_to_words(sentences):
    for sentence in sentences:
        yield(gensim.utils.simple_preprocess(str(sentence), deacc=True))  # deacc=True removes punctuations

#remove stop_words, make bigrams and lemmatize
def remove_stopwords(texts, stop_words):
    return [[word for word in simple_preprocess(str(doc)) if word not in stop_words] for doc in texts]

def make_bigrams(texts, bigram_mod):
    return [bigram_mod[doc] for doc in texts]

def make_trigrams(texts,bigram_mod, trigram_mod):
    return [trigram_mod[bigram_mod[doc]] for doc in texts]

def lemmatization(texts, nlp, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV']):
    texts_out = []
    for sent in texts:
        doc = nlp(" ".join(sent))
        texts_out.append([token.lemma_ for token in doc if token.pos_ in allowed_postags])
    return texts_out

##Postprocess topics for trained LDA model
def get_topics(lda_model):
    topics = []
    for i in range(len(lda_model.show_topics(formatted=False))):
      topic_prop = lda_model.show_topic(i)
      topic_keywords = ", ".join([word for word, prop in topic_prop])
      topics.append(topic_keywords)
    return topics

##Main function to get topic enron emails
def get_topic_enron(data, lda_model, stop_words, nlp):

    ##Tokenize sentence to words
    data_words = list(sent_to_words(data))

    bigram = Phrases(data_words, min_count=5, threshold=100) # higher threshold fewer phrases.
    trigram = Phrases(bigram[data_words], threshold=100)
    bigram_mod = Phraser(bigram)
    trigram_mod = Phraser(trigram)

    # Remove Stop Words
    data_words_nostops = remove_stopwords(data_words, stop_words)

    # Form Bigrams and Trigrams
    data_words_bigrams = make_bigrams(data_words_nostops, bigram_mod)

    ##Lemmatize
    data_lemmatized = lemmatization(data_words_bigrams, nlp, allowed_postags=['NOUN', 'ADJ', 'VERB', 'ADV'])

    test_data = lda_model.id2word.doc2bow(data_lemmatized[0])
    output = lda_model[test_data]
    topics = get_topics(lda_model)

    if(topics[max(output[0],key=lambda item:item[1])[0]]==4):
      enron_oil_and_gas = True
    else:
      enron_oil_and_gas = False

    return enron_oil_and_gas
