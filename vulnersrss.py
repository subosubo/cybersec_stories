import datetime
import logging
import pathlib
import pytz
from os.path import join
from parse_rss import rss_parse

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
            ), "output/record.json"
        )
        self.last_published = datetime.datetime.now(
            gmt) - datetime.timedelta(days=1)
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_vulners_blog = []
        self.vulners_blog_title = []

    ################## GET ARTICLES ####################

    def get_articles_rss(self, time_format):
        rss = rss_parse(url=self.VULNERS_BLOG_URL, title="Vulners", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, last_published=self.last_published, time_format=time_format)
        rss.get_new_rss()
        self.new_vulners_blog = rss.filtered_list
        self.last_published = rss.last_published
        self.vulners_blog_title = rss.filted_obj_title
