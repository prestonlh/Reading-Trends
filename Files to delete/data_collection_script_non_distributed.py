#THIS SCRIPT IS USED FOR SCRAPING DATA ON MY OWN COMPUTER. IT WORKS AND HAS GENERATED THE DATA COLLECTED THUS FAR.
#THIS SCRIPT SHOULD BE REPLACED WITH A DISTRIBUTED VERSION SINCE THIS IS TOO SLOW!

#import libraries
from bs4 import BeautifulSoup
from datetime import datetime
import re
import requests
import random
import pandas as pd
import sys

#import classes

from parser_script import Parser
from parser_script import Review_Parser
from parser_script import Book_Parser

from scraper_script import Scraper

#import data
from database_script import book_list

#Data Generation Classes

class Data_Collector():

    def __init__(self, max_sleep_time, file_name):

        self.max_sleep_time = max_sleep_time

        self.data_points_counter = 0
        self.log_file_name = "databases/"+ file_name + ".csv"
        self.scraper = Scraper()

    def is_csv(self):

        try:
            df = pd.read_csv(self.log_file_name, low_memory=False)
            is_csv = True

        except (FileNotFoundError, pd.errors.EmptyDataError):
            is_csv = False

        return is_csv

    def prepare_scope(self):

        pass

    def open_log_file(self):

        self.datafile = open(self.log_file_name, "a")

    def add_headers_to_log_file(self):

        print("This method should be overwritten in each inherited class. If this is printed, something is not working correctly.")

    def prepare_log_file(self):

        if self.is_csv():
            self.open_log_file()

        else:

            self.open_log_file()
            self.add_headers_to_log_file()

        print("Log File Ready")

    def generate_current_url(self):

        print("This method should be overwritten in each inherited class. If this is printed, something is not working correctly.")

    def scrape_url(self):

        self.current_webpage_as_string = self.scraper.url_to_string_content(self.current_url)

    def generate_soup(self):

        self.current_soup = self.parser.html_to_soup(self.current_webpage_as_string)

        invalid_count = 0

        while self.parser.is_soup_populated(self.current_soup) == False:

            if invalid_count < 10:
                self.generate_datetime()
                print("Recieved Invalid Response from Website. Pausing Data Collection at {}...".format(self.self.now_string))

                pause_time = max(self.max_sleep_time, invalid_count*60) #IF IT'S THE FIRST ERROR, REGULAR SLEEPTIME. FOR SUBSEQUENT ERRORS, INCREASINGLY LARGE WAIT TIMES.
                self.sleep(pause_time)

                self.generate_datetime()
                print("Restarting Data Collection at {}...".format(self.now_string))
                self.current_soup = self.parser.html_to_soup(self.current_webpage_as_string)

                invalid_count += 1

            else:

                print("Too Many Invalid Requests Recieved. Terminating Data Collection.")
                self.datafile.close()
                sys.exit()

    def parse(self):

        print("This method should be overwritten in each inherited class. If this is printed, something is not working correctly.")

    def log_data(self):

        print("This method should be overwritten in each inherited class. If this is printed, something is not working correctly.")

    def print_progress(self):
        if self.data_points_counter % 5 == 0:
            self.calculate_progress()
            percent_complete_string = str(self.percent_complete)

            print("{} / {} {} Collected ({}% Complete) at {}". format(str(self.data_points_counter), str(self.max_data_points), self.data_point_type, percent_complete_string, self.now_string))

    def calculate_progress(self):

        self.percent_complete = round(100 * self.data_points_counter / self.max_data_points, 2)

    def sleep(self, max_sleep_time = None):

        if max_sleep_time:
            sleeptime = max_sleep_time
        else:
            sleeptime = self.max_sleep_time

        self.scraper.sleep(sleeptime)

    def generate_datetime(self):

        now = datetime.now()
        self.now_string = now.strftime("%m/%d/%Y %H:%M:%S")

    def timestamp(self):

        self.datafile.write(","+self.now_string)

    def is_collection_complete(self):

        is_complete = self.data_points_counter >= self.max_data_points
        return is_complete

    def data_collection_loop(self):

        self.prepare_log_file()
        self.prepare_scope()

        print("Beginning Data Collection...")
        while not self.is_collection_complete():

            try:
                self.generate_current_url()
                self.scrape_url()
                self.generate_soup()
                self.parse()
                self.log_data()
                self.generate_datetime()
                self.timestamp()
                self.print_progress()
                self.sleep()

            except requests.exceptions.ConnectionError: #I THINK THIS IS WHEN THE INTERNET DISCONNECTS
                print("Connection Error! \n Restarting Data Collection...")

                continue

        print("Data Collection Complete")
        self.datafile.close()

class Review_Data_Collector(Data_Collector):

    def __init__(self, min_id, max_id, max_data_points, max_sleep_time, file_name):

        super().__init__(max_sleep_time, file_name)

        #Specifics for Review Data Collection
        self.id_list = range(min_id, max_id)
        self.base_url = "https://www.goodreads.com/review/show/"
        self.data_point_type = "Reviews"

        #counter
        self.max_data_points = max_data_points

        #Review Parser
        self.parser = Review_Parser()

    def generate_current_url(self):
        self.current_id = random.choice(self.id_list)
        self.current_url = self.base_url + str(self.current_id)

    def add_headers_to_log_file(self):

        self.datafile.write("ID,is_URL_valid,review_publication_date,book_title,book_id,rating,reviewer_href,started_reading_date,finished_reading_date,shelved_date,log_time")

    def parse(self):

        self.is_current_valid = self.parser.review_soup_is_valid(self.current_soup)

        if self.is_current_valid:
            self.current_date = self.parser.review_soup_to_date(self.current_soup)
            self.current_book_title = self.parser.review_soup_to_book_title(self.current_soup)
            self.current_book_id = self.parser.review_soup_to_book_id(self.current_soup)
            self.current_rating = self.parser.review_soup_to_rating(self.current_soup)
            self.current_reviewer_href = self.parser.review_soup_to_reviewer_href(self.current_soup)

            self.current_progress_dict = self.parser.review_soup_to_progress_dict(self.current_soup)
            self.current_start_date = self.parser.progress_dict_to_start_date(self.current_progress_dict)
            self.current_finished_date = self.parser.progress_dict_to_finish_date(self.current_progress_dict)
            self.current_shelved_date = self.parser.progress_dict_to_shelved_date(self.current_progress_dict)

        else:
            self.current_date = None
            self.current_book_title = None
            self.current_book_id = None
            self.current_rating = None
            self.current_reviewer_href = None
            self.current_start_date = None
            self.current_finished_date = None
            self.current_shelved_date = None

    def log_data(self):

        self.datafile.write("\n{},{},{},{},{},{},{},{},{},{}".format(str(self.current_id), self.is_current_valid, self.current_date, self.current_book_title, self.current_book_id, self.current_rating, self.current_reviewer_href, self.current_start_date, self.current_finished_date, self.current_shelved_date))

        self.data_points_counter += 1

class Book_Data_Collector(Data_Collector):

    def __init__(self, requested_book_id_list, max_sleep_time, file_name):

        super().__init__(max_sleep_time, file_name)
        self.requested_book_id_list = requested_book_id_list

        self.base_url = "https://www.goodreads.com/book/show/"
        self.data_point_type = "Books"

        self.parser = Book_Parser()

    def prepare_scope(self):

        if self.is_csv():

            self.data_logged_at_start = pd.read_csv(self.log_file_name)
            self.book_ids_already_scraped_list = self.data_logged_at_start.book_id.unique()
            self.book_ids_already_scraped_list = [str(id) for id in self.book_ids_already_scraped_list]
            self.book_ids_to_be_scraped = []

            for item in self.requested_book_id_list:

                if item not in self.book_ids_already_scraped_list:
                    self.book_ids_to_be_scraped.append(item)
        else:

            self.book_ids_to_be_scraped = self.requested_book_id_list

        self.max_data_points = len(self.book_ids_to_be_scraped)

    def add_headers_to_log_file(self):

        self.datafile.write("book_id,author,language,num_reviews,num_ratings,avg_rating,isbn13,editions_url,publication_date,first_publication_date,series,log_time")

    def generate_current_url(self):

        self.current_id = self.book_ids_to_be_scraped[self.data_points_counter]
        self.current_url = self.base_url + self.current_id

    def parse(self):

        self.author = self.parser.book_soup_to_author(self.current_soup)
        self.language = self.parser.book_soup_to_language(self.current_soup)
        self.num_reviews = self.parser.book_soup_to_num_reviews(self.current_soup)
        self.num_ratings = self.parser.book_soup_to_num_ratings(self.current_soup)
        self.avg_rating = self.parser.book_soup_to_avg_rating(self.current_soup)
        self.isbn13 = self.parser.book_soup_to_isbn13(self.current_soup)
        self.editions_href = self.parser.book_soup_to_editions_href(self.current_soup)
        self.publication_date = self.parser.book_soup_to_publication_date(self.current_soup)
        self.first_publication_date = self.parser.book_soup_to_first_publication_date(self.current_soup)
        self.series = self.parser.book_soup_to_series(self.current_soup)

    def log_data(self):

        self.datafile.write("\n{},{},{},{},{},{},{},{},{},{},{}".format(self.current_id, self.author, self.language, self.num_reviews, self.num_ratings, self.avg_rating, self.isbn13, self.editions_href, self.publication_date, self.first_publication_date, self.series))

        self.data_points_counter += 1

## REVIEW DATA COLLECTION

#keeping this low until I am fully confident that this is working as expected.
num_reviews_to_collect = 5 * 10 **6
estimated_num_reviews = int(3.5 * 10 **9)
num_wait_seconds = 1

min_2017_ID = 1484362322 #I want to actually analyze data from 2018-2020, but I'm pulling 2017 data too just because the ID generation isn't quite linear.
max_2020_ID = 3455207761 #I'm not sure if i should use this, since reviews are going to continue to roll in...

#Uncomment to run the Review Detail collector
review_collector = Review_Data_Collector(min_2017_ID, max_2020_ID, num_reviews_to_collect, num_wait_seconds, "review_data")
review_collector.data_collection_loop()

## BOOK DATA COLLECTION

#book_list = book_list[:10]
num_wait_seconds = 5 ##BOOK PAGES HAVE ISSUES WHEN SCRAPED TOO QUICKLY, SO KEEP THIS LONG IF POSSIBLE

#uncomment to run Book Collector
#book_collector = Book_Data_Collector(book_list, num_wait_seconds, "book_data")
#book_collector.data_collection_loop()
