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
        # self.BC_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        self.LAST_PUBLISHED = datetime.datetime.now(
            utc) - datetime.timedelta(days=1)
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_stories = []
        self.bc_title = []

    ################## LOAD CONFIGURATIONS ####################

    # def load_lasttimes(self):
    #     # Load lasttimes from json file

    #     try:
    #         with open(self.PUBLISH_BC_JSON_PATH, "r") as json_file:
    #             published_time = json.load(json_file)
    #             self.LAST_PUBLISHED = datetime.datetime.strptime(
    #                 published_time["LAST_PUBLISHED"], self.BC_TIME_FORMAT
    #             )

    #     # If error, just keep the fault date (today - 1 day)
    #     except Exception as e:
    #         self.logger.error(f"BC-ERROR-1: {e}")

    # def update_lasttimes(self):
    #     # Save lasttimes in json file
    #     try:
    #         with open(self.PUBLISH_BC_JSON_PATH, "w") as json_file:
    #             json.dump(
    #                 {
    #                     "LAST_PUBLISHED": self.LAST_PUBLISHED.strftime(
    #                         self.BC_TIME_FORMAT
    #                     ),
    #                 },
    #                 json_file,
    #             )
    #     except Exception as e:
    #         self.logger.error(f"BC-ERROR-2: {e}")

    ################## SEARCH STORIES FROM BLEEPING COMPUTER ####################

    # def get_stories(self, link):
    #     newsfeed = feedparser.parse(link)
    #     return newsfeed

    # def filter_stories(self, stories, last_published: datetime.datetime):
    #     filtered_stories = []
    #     new_last_time = last_published
    #     for story in stories:
    #         story_time = datetime.datetime.strptime(
    #             story["published"], self.BC_TIME_FORMAT
    #         )
    #         if story_time > last_published:
    #             if self.valid or self.is_summ_keyword_present(story["description"]):

    #                 filtered_stories.append(story)

    #         if story_time > new_last_time:
    #             new_last_time = story_time

    #     return filtered_stories, new_last_time

    # def is_summ_keyword_present(self, summary: str):
    #     # Given the summary check if any keyword is present
    #     return any(w in summary for w in self.keywords) or any(
    #         w.lower() in summary.lower() for w in self.keywords_i
    #     )  # for each of the word in description keyword config, check if it exists in summary.

    # def get_new_stories(self):
    #     stories = self.get_stories(self.BLEEPING_COM_UR)
    #     self.new_stories, self.LAST_PUBLISHED = self.filter_stories(
    #         stories["entries"], self.LAST_PUBLISHED
    #     )

    #     self.bc_title = [new_story["title"] for new_story in self.new_stories]
    #     self.logger.info(f"Bleeping Computer Stories: {self.bc_title}")

    ################## GET ARTICLES ####################

    def get_articles_rss(self, time_format):
        rss = rss_parse(url=self.BLEEPING_COM_UR, title="BleepingCom", valid=self.valid, keywords=self.keywords,
                        keywords_i=self.keywords_i, product=self.product, product_i=self.product_i, LAST_PUBLISHED=self.LAST_PUBLISHED, TIME_FORMAT=time_format)
        rss.get_new_rss()
        self.new_stories = rss.filtered_list
        self.LAST_PUBLISHED = rss.LAST_PUBLISHED
        self.bc_title = rss.filted_obj_title
