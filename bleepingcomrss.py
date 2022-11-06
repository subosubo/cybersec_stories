import datetime
import json
import logging
import pathlib
from os.path import join

import feedparser
import pytz
from discord import Color, Embed

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
            pathlib.Path(__file__).parent.absolute(), "output/record.json"
        )
        self.BC_TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
        self.LAST_PUBLISHED = datetime.datetime.now(utc) - datetime.timedelta(days=1)
        self.logger = logging.getLogger("cybersecstories")

    ################## LOAD CONFIGURATIONS ####################

    def load_lasttimes(self):
        # Load lasttimes from json file

        try:
            with open(self.PUBLISH_BC_JSON_PATH, "r") as json_file:
                published_time = json.load(json_file)
                self.LAST_PUBLISHED = datetime.datetime.strptime(
                    published_time["LAST_PUBLISHED"], self.BC_TIME_FORMAT
                )

        except Exception as e:  # If error, just keep the fault date (today - 1 day)
            self.logger.error(f"ERROR: {e}")

    def update_lasttimes(self):
        # Save lasttimes in json file
        try:
            with open(self.PUBLISH_BC_JSON_PATH, "w") as json_file:
                json.dump(
                    {
                        "LAST_PUBLISHED": self.LAST_PUBLISHED.strftime(
                            self.BC_TIME_FORMAT
                        ),
                    },
                    json_file,
                )
        except Exception as e:
            self.logger.error(f"ERROR: {e}")

    ################## SEARCH STORIES FROM BLEEPING COMPUTER ####################

    def get_stories(self, link):
        newsfeed = feedparser.parse(link)
        return newsfeed

    def filter_stories(self, stories, last_published: datetime.datetime):
        filtered_stories = []
        new_last_time = last_published
        for story in stories:
            story_time = datetime.datetime.strptime(
                story["published"], self.BC_TIME_FORMAT
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
        stories = self.get_stories(self.BLEEPING_COM_UR)
        filtered_stories, new_published_time = self.filter_stories(
            stories["entries"], self.LAST_PUBLISHED
        )
        self.LAST_PUBLISHED = new_published_time
        return filtered_stories

    def generate_new_story_message(self, new_story) -> Embed:
        # Generate new CVE message for sending to slack
        embed = Embed(
            title=f"🔈 *{new_story['title']}*",
            description=new_story["summary"]
            if len(new_story["summary"]) < 500
            else new_story["summary"][:500] + "...",
            timestamp=datetime.datetime.utcnow(),
            color=Color.light_gray(),
        )
        embed.add_field(
            name=f"📅  *Published*", value=f"{new_story['published']}", inline=True
        )
        embed.add_field(
            name=f"More Information", value=f"{new_story['link']}", inline=False
        )

        return embed
