import logging
import pytz
from os.path import join

from parse_rss import rss_parse


utc = pytz.UTC


class bleepingcom:
    def __init__(self, valid, keywords, keywords_i, product, product_i, last_published, time_format):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i
        self.last_published = last_published
        self.time_format = time_format
        self.BLEEPING_COM_UR = "https://www.bleepingcomputer.com/feed/"
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_stories = []
        self.bc_title = []

    ################## GET ARTICLES ####################

    def get_articles_rss(self):
        rss = rss_parse(url=self.BLEEPING_COM_UR, title="BleepingCom", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, last_published=self.last_published, time_format=self.time_format)
        rss.get_new_rss()
        self.new_stories = rss.filtered_list
        self.last_published = rss.last_published
        self.bc_title = rss.filted_obj_title
