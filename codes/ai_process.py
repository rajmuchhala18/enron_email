"""

This is the main AI Process which calls all the other dependent
functions and returns the AI result

"""
from multiprocessing import Process, Manager, Queue
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from email.parser import Parser
from gensim.test.utils import datapath
import gensim
import time

# prep NLTK Stop words
import nltk
from nltk.corpus import stopwords
nltk.download('stopwords')

from lda_topic_classification import *
from preprocess_email import get_email
import config

class ProcessClass(Process):


    def __init__(self, process_queue: Queue, resultproc: Manager, process_stat: Manager) -> None:
        """
        Init method to load all the models only once
        when an instance is created
        :params None
        :return None
        """
        Process.__init__(self)
        self.process_queue = process_queue
        self.resultproc = resultproc
        self.process_stat = process_stat


        ##Initialize all the models here
        self.classifier = SentimentIntensityAnalyzer()
        self.vader_thresh = config.vader_thresh
        self.lda_model = gensim.models.ldamodel.LdaModel.load(datapath(config.model_path))
        self.stop_words = stopwords.words('english')
        self.stop_words.extend(['from', 'subject', 're', 'edu', 'use'])
        self.nlp = spacy.load('en_core_web_sm', disable=['parser', 'ner'])

    def get_sentiment_analysis(self, email_body):
        sentiment_dict = self.classifier.polarity_scores(email_body)
        # decide sentiment as positive, negative and neutral
        if sentiment_dict['compound'] >= self.vader_thresh :
            return ("Positive")
        elif sentiment_dict['compound'] <= - self.vader_thresh :
            return ("Negative")
        else :
            return ("Neutral")

    def run(self) -> None:
        """
        The run method of the ProcessClass to process the incoming
        data and produce results by AI
        :params None
        :return None
        """

        """
        LOAD ALL THE WORKER SPECIFIC MODULES here
        """

        print ('WORKER Starting Now ...')

        while(self.process_stat["run_flag"]):
            try:
                result = {}
                result["sentiment"] = ""
                result["oil_and_gas_flag"] = False

                FLAG = True
                error_message = ''
                request_data = self.process_queue.get()
                request_data = request_data[0]

                req_id = request_data['req_id']
                input_data = request_data['Email']

                if input_data:
                    ##Parse the Email Input Data
                    try:
                        parsed_data = get_email(input_data)
                    except Exception as e:
                        FLAG = False
                        error_message = "Error analyzing parsing the Email: "+str(e)

                    ## Get Vader Sentiment Analysis
                    try:
                        start = start = time.time()
                        result["sentiment"] = self.get_sentiment_analysis(parsed_data[0])
                        duration = time.time() - start
                        print("Latency of Vader Sentiment Analysis: ", duration, flush=True)
                    except Exception as e:
                        FLAG = False
                        error_message = "Error analyzing the sentiment of the Email: "+str(e)

                    ##Get Enron Topic related to oil and gas
                    try:
                        start = start = time.time()
                        result["oil_and_gas_flag"] = get_topic_enron(parsed_data, self.lda_model, self.stop_words, self.nlp)
                        duration = time.time() - start
                        print("Latency of LDA Topic Classifier is : ", duration, flush=True)
                    except Exception as e:
                        FLAG = False
                        error_message = "Error analyzing the Topic of the Email: "+str(e)



                else:
                    FLAG = False
                    error_message = "Input data cannot be empty. Please provide valid email"

                result["req_id"] = req_id
                result["success"] = FLAG
                result["error_message"] = error_message
                response_data = result

            except Exception as e:
                FLAG = False
                error_message = "Error: "+str(e)
                response_data = {}
                response_data["sentiment"] = ""
                response_data["oil_and_gas_flag"] = False


            self.resultproc[req_id] = response_data

        print("AI_Process Done!!!!!!")
