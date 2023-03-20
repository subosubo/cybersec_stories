import logging
import pytz
from os.path import join
from parse_rss import rss_parse

utc = pytz.UTC


class hackernews:
    def __init__(self, valid, keywords, keywords_i, product, product_i, last_published, time_format):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i
        self.last_published = last_published
        self.time_format = time_format
        self.HACKER_NEWS_UR = "https://feeds.feedburner.com/TheHackersNews"
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_news = []
        self.hn_title = []

    ################## GET ARTICLES ####################

    def get_articles_rss(self):
        rss = rss_parse(url=self.HACKER_NEWS_UR, title="TheHackersNews", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, last_published=self.last_published, time_format=self.time_format)
        rss.get_new_rss()
        self.new_news = rss.filtered_list
        self.last_published = rss.last_published
        self.hn_title = rss.filted_obj_title
