import datetime
import json
import logging
import pathlib
from os.path import join

import feedparser
import pytz
from discord import Color, Embed

utc = pytz.UTC


class hackernews:
    def __init__(self, valid, keywords, keywords_i, product, product_i):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i

        self.HACKER_NEWS_UR = "https://feeds.feedburner.com/TheHackersNews"
        self.PUBLISH_HN_JSON_PATH = join(
            pathlib.Path(__file__).parent.absolute(), "output/hacker_news_record.json"
        )
        self.HN_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        self.LAST_PUBLISHED = datetime.datetime.now(utc) - datetime.timedelta(days=1)
        self.logger = logging.getLogger(__name__)

        self.new_news = []
        self.hn_title = []

    ################## LOAD CONFIGURATIONS ####################

    def load_lasttimes(self):
        # Load lasttimes from json file

        try:
            with open(self.PUBLISH_HN_JSON_PATH, "r") as json_file:
                published_time = json.load(json_file)
                self.LAST_PUBLISHED = datetime.datetime.strptime(
                    published_time["LAST_PUBLISHED"], self.HN_TIME_FORMAT
                )

        except Exception as e:  # If error, just keep the fault date (today - 1 day)
            self.logger.error(f"HN-ERROR-1: {e}")

    def update_lasttimes(self):
        # Save lasttimes in json file
        try:
            with open(self.PUBLISH_HN_JSON_PATH, "w") as json_file:
                json.dump(
                    {
                        "LAST_PUBLISHED": self.LAST_PUBLISHED.strftime(
                            self.HN_TIME_FORMAT
                        ),
                    },
                    json_file,
                )
        except Exception as e:
            self.logger.error(f"HN-ERROR-2: {e}")

    ################## SEARCH STORIES FROM THE HACKING NEW ####################

    def get_stories(self, link):
        newsfeed = feedparser.parse(link)
        return newsfeed

    def filter_stories(self, stories, last_published: datetime.datetime):
        filtered_stories = []
        new_last_time = last_published
        for story in stories:
            story_time = datetime.datetime.strptime(
                story["published"], self.HN_TIME_FORMAT
            )
            if story_time > last_published:
                if self.valid or self.is_summ_keyword_present(story["description"]):

                    filtered_stories.append(story)

            if story_time > new_last_time:
                new_last_time = story_time

        return filtered_stories, new_last_time

    def is_summ_keyword_present(self, summary: str):
        # Given the summary check if any keyword is present
        return any(w in summary for w in self.keywords) or any(
            w.lower() in summary.lower() for w in self.keywords_i
        )  # for each of the word in description keyword config, check if it exists in summary.

    def get_new_stories(self):
        stories = self.get_stories(self.HACKER_NEWS_UR)
        self.new_news, self.LAST_PUBLISHED = self.filter_stories(
            stories["entries"], self.LAST_PUBLISHED
        )

        self.hn_title = [news["title"] for news in self.new_news]
        print(f"The Hacking News: {self.hn_title}")
        self.logger.info(f"The Hacking News: {self.hn_title}")
