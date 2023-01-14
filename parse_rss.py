import datetime
import json
import logging
from os.path import join
from bs4 import BeautifulSoup
import requests
import html
import feedparser


class rss_parse:

    def __init__(self, url, title, valid, keywords, keywords_i, product, product_i, last_published, time_format):
        self.time_format = time_format
        self.url = url
        self.title_label = title
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.last_published = last_published

        self.filtered_list = []

    ################## SEARCH  ####################

    def request_rss(self, link):
        newsfeed = feedparser.parse(link)
        return newsfeed

    def filter_list(self, list, last_published: datetime.datetime):
        filtered_list = []
        new_last_time = last_published

        for list_obj in list:
            list_obj_time = datetime.datetime.strptime(
                list_obj["published"], self.time_format
            )
            if list_obj_time > last_published:
                if self.valid or self.is_summ_keyword_present(list_obj["description"]):

                    filtered_list.append(list_obj)

            if list_obj_time > new_last_time:
                new_last_time = list_obj_time

        return filtered_list, new_last_time

    def is_summ_keyword_present(self, summary: str):
        # Given the summary check if any keyword is present
        return any(w in summary for w in self.keywords) or any(
            w.lower() in summary.lower() for w in self.keywords_i
        )  # for each of the word in description keyword config, check if it exists in summary.

    def get_new_rss(self):
        new_list = self.request_rss(self.url)
        self.filtered_list, self.last_published = self.filter_list(
            new_list["entries"], self.last_published
        )
        # removes html tags from description
        self.remove_html()
        # replaces vulners url from references with actual reference url
        if self.title_label == "Vulners":
            self.replace_links()

        self.filted_obj_title = [filted_obj["title"]
                                 for filted_obj in self.filtered_list]
        self.logger.info(f"{self.title_label}: {self.filted_obj_title}")

    def remove_html(self):
        for filted_obj in self.filtered_list:
            # html.unescape - decode HTML entiries to text
            # beautifulsoup get_text removes html tags
            filted_obj['description'] = html.unescape(BeautifulSoup(
                filted_obj['description'], 'lxml').get_text())

    def replace_links(self):
        for filted_obj in self.filtered_list:
            response = requests.get(filted_obj['link'])
            soup = BeautifulSoup(response.text, 'lxml')
            element = soup.find('div', id='jsonbody').get_text()
            json_dict = json.loads(element)
            filted_obj['link'] = json_dict['href']
