import datetime
import logging
import pathlib
from os.path import join
from parse_rss import rss_parse


class securityweek:
    def __init__(self, valid, keywords, keywords_i, product, product_i):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i

        self.SW_BLOG_URL = "https://feeds.feedburner.com/securityweek"
        self.PUBLISH_SW_JSON_PATH = join(
            pathlib.Path(__file__).parent.absolute(
            ), "output/record.json"
        )
        self.last_published = datetime.datetime.now() - datetime.timedelta(days=1)
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_sw_blog = []
        self.sw_blog_title = []

    ################## GET ARTICLES ####################

    def get_articles_rss(self, time_format):
        rss = rss_parse(url=self.SW_BLOG_URL, title="Security Week", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, last_published=self.last_published, TIME_FORMAT=time_format)
        rss.get_new_rss()
        self.new_sw_blog = rss.filtered_list
        self.last_published = rss.last_published
        self.sw_blog_title = rss.filted_obj_title
