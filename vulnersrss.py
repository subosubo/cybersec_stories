import datetime
import json
import logging
import pathlib
from os.path import join
from bs4 import BeautifulSoup
import requests
import html

import feedparser
import pytz

gmt = pytz.timezone('GMT')


class vulners:
    def __init__(self, valid, keywords, keywords_i, product, product_i):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i

        self.VULNERS_BLOG_URL = "https://vulners.com/rss.xml?query=bulletinFamily:blog%20order:published"
        self.PUBLISH_VULNERS_JSON_PATH = join(
            pathlib.Path(__file__).parent.absolute(
            ), "output/vulners_record.json"
        )
        self.VULNERS_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %Z"
        self.LAST_PUBLISHED = datetime.datetime.now(
            gmt) - datetime.timedelta(days=1)
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.INFO)
        self.new_vulners_blog = []
        self.vulners_blog_title = []

    ################## LOAD CONFIGURATIONS ####################

    def load_lasttimes(self):
        # Load lasttimes from json file

        try:
            with open(self.PUBLISH_VULNERS_JSON_PATH, "r") as json_file:
                published_time = json.load(json_file)
                self.LAST_PUBLISHED = datetime.datetime.strptime(
                    published_time["LAST_PUBLISHED"], self.VULNERS_TIME_FORMAT
                )

        # If error, just keep the fault date (today - 1 day)
        except Exception as e:
            self.logger.error(f"VULNERS-ERROR-1: {e}")

    def update_lasttimes(self):

        # Save lasttimes in json file
        try:
            with open(self.PUBLISH_VULNERS_JSON_PATH, "w") as json_file:
                json.dump(
                    {
                        "LAST_PUBLISHED": self.LAST_PUBLISHED.replace(
                            tzinfo=gmt).strftime(self.VULNERS_TIME_FORMAT)
                    },
                    json_file,
                )
        except Exception as e:
            self.logger.error(f"VULNERS-ERROR-2: {e}")

    ################## SEARCH BLOG FROM VULNERS ####################

    def get_vulners_list(self, link):
        newsfeed = feedparser.parse(link)
        return newsfeed

    def filter_vulners_list(self, vulners_list, last_published: datetime.datetime):
        filtered_vulners = []
        new_last_time = last_published
        for vulner_obj in vulners_list:
            vulner_obj_time = datetime.datetime.strptime(
                vulner_obj["published"], self.VULNERS_TIME_FORMAT
            )
            if vulner_obj_time > last_published:
                if self.valid or self.is_summ_keyword_present(vulner_obj["description"]):

                    filtered_vulners.append(vulner_obj)

            if vulner_obj_time > new_last_time:
                new_last_time = vulner_obj_time

        return filtered_vulners, new_last_time

    def is_summ_keyword_present(self, summary: str):
        # Given the summary check if any keyword is present
        return any(w in summary for w in self.keywords) or any(
            w.lower() in summary.lower() for w in self.keywords_i
        )  # for each of the word in description keyword config, check if it exists in summary.

    def get_new_vulners(self):
        vulner_obj = self.get_vulners_list(self.VULNERS_BLOG_URL)
        self.new_vulners_blog, self.LAST_PUBLISHED = self.filter_vulners_list(
            vulner_obj["entries"], self.LAST_PUBLISHED
        )
        # removes html tags from description
        self.remove_html_from_vulners()
        # replaces vulners url from references with actual reference url
        self.replace_links()

        self.vulners_blog_title = [new_blog["title"]
                                   for new_blog in self.new_vulners_blog]
        self.logger.info(f"Vulners Blog: {self.vulners_blog_title}")

    def remove_html_from_vulners(self):
        for blog in self.new_vulners_blog:
            # html.unescape - decode HTML entiries to text
            # beautifulsoup get_text removes html tags
            blog['description'] = html.unescape(BeautifulSoup(
                blog['description'], 'lxml').get_text())

    def replace_links(self):
        for blog in self.new_vulners_blog:
            response = requests.get(blog['link'])
            soup = BeautifulSoup(response.text, 'lxml')
            element = soup.find('div', id='jsonbody').get_text()
            json_dict = json.loads(element)
            blog['link'] = json_dict['href']
