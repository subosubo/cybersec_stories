import datetime
import logging
import pathlib
import pytz
from os.path import join

from parse_rss import rss_parse


utc = pytz.UTC


class bleepingcom:
    def __init__(self, valid, keywords, keywords_i, product, product_i):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i

        self.BLEEPING_COM_UR = "https://www.bleepingcomputer.com/feed/"
        self.PUBLISH_BC_JSON_PATH = join(
            pathlib.Path(__file__).parent.absolute(
            ), "output/bleeping_com_record.json"
        )
        self.last_published = datetime.datetime.now(
            utc) - datetime.timedelta(days=1)
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_stories = []
        self.bc_title = []

    ################## GET ARTICLES ####################

    def get_articles_rss(self, time_format):
        rss = rss_parse(url=self.BLEEPING_COM_UR, title="BleepingCom", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, last_published=self.last_published, TIME_FORMAT=time_format)
        rss.get_new_rss()
        self.new_stories = rss.filtered_list
        self.last_published = rss.last_published
        self.bc_title = rss.filted_obj_title
