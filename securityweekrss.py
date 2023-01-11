import datetime
import json
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
        # self.SW_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        self.LAST_PUBLISHED = datetime.datetime.now() - datetime.timedelta(days=1)
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_SW_blog = []
        self.SW_blog_title = []

    ################## LOAD CONFIGURATIONS ####################

    # def load_lasttimes(self):
    #     # Load lasttimes from json file

    #     try:
    #         with open(self.PUBLISH_SW_JSON_PATH, "r") as json_file:
    #             published_time = json.load(json_file)
    #             self.LAST_PUBLISHED = datetime.datetime.strptime(
    #                 published_time["SW_LAST_PUBLISHED"], self.SW_TIME_FORMAT
    #             )

    #     # If error, just keep the fault date (today - 1 day)
    #     except Exception as e:
    #         self.logger.error(f"SW-ERROR-1: {e}")

    # def update_lasttimes(self):

    #     try:

    #         # Save lasttimes in json file
    #         with open(self.PUBLISH_SW_JSON_PATH, 'r') as f:
    #             # Load the JSON data from the file
    #             data = json.load(f)

    #         # Modify the desired key in the JSON object
    #         data['SW_LAST_PUBLISHED'] = self.LAST_PUBLISHED.strftime(
    #             self.SW_TIME_FORMAT)

    #         # Open the file for writing
    #         with open(self.PUBLISH_SW_JSON_PATH, 'w') as f:
    #             # Write the modified JSON object to the file
    #             json.dump(data, f)

    #     except Exception as e:
    #         self.logger.error(f"SW-ERROR-2: {e}")

    ################## GET ARTICLES ####################

    def get_articles_rss(self, time_format):
        rss = rss_parse(url=self.SW_BLOG_URL, title="Security Week", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, LAST_PUBLISHED=self.LAST_PUBLISHED, TIME_FORMAT=time_format)
        rss.get_new_rss()
        self.new_SW_blog = rss.filtered_list
        self.LAST_PUBLISHED = rss.LAST_PUBLISHED
        self.SW_blog_title = rss.filted_obj_title
