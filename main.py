import asyncio
import datetime
import json
import logging
import os
import pathlib
import sys
from enum import Enum
from os.path import join
from tkinter import LAST

import aiohttp
import feedparser
import pytz
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Color, Embed, Webhook

utc = pytz.UTC

BLEEPING_COM_UR = "https://www.bleepingcomputer.com/feed/"
PUBLISH_JSON_PATH = join(pathlib.Path(__file__).parent.absolute(), "output/record.json")
TIME_FORMAT = "%a, %d %b %Y %H:%M:%S %z"
LAST_PUBLISHED = datetime.datetime.now(utc) - datetime.timedelta(days=7)


KEYWORDS_CONFIG_PATH = join(
    pathlib.Path(__file__).parent.absolute(), "config/config.yaml"
)
ALL_VALID = False
DESCRIPTION_KEYWORDS_I = []
DESCRIPTION_KEYWORDS = []
PRODUCT_KEYWORDS_I = []
PRODUCT_KEYWORDS = []

logger = logging.getLogger('cybersecstories')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='cybersec_stories.log',
                              encoding='utf-8',
                              mode='w')
handler.setFormatter(
    logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

def load_keywords():
    ''' Load keywords from config file '''

    global ALL_VALID
    global DESCRIPTION_KEYWORDS_I, DESCRIPTION_KEYWORDS
    global PRODUCT_KEYWORDS_I, PRODUCT_KEYWORDS
    try:

        with open(KEYWORDS_CONFIG_PATH, 'r') as yaml_file:
            keywords_config = yaml.safe_load(yaml_file)
            print(f"Loaded keywords: {keywords_config}")
            ALL_VALID = keywords_config["ALL_VALID"]
            DESCRIPTION_KEYWORDS_I = keywords_config["DESCRIPTION_KEYWORDS_I"]
            DESCRIPTION_KEYWORDS = keywords_config["DESCRIPTION_KEYWORDS"]
            PRODUCT_KEYWORDS_I = keywords_config["PRODUCT_KEYWORDS_I"]
            PRODUCT_KEYWORDS = keywords_config["PRODUCT_KEYWORDS"]

    except Exception as e:
        logger.error(e)
        sys.exit(1)

################## LOAD CONFIGURATIONS ####################

def load_lasttimes():
    ''' Load lasttimes from json file '''

    global LAST_PUBLISHED

    try:
        with open(PUBLISH_JSON_PATH, 'r') as json_file:
            published_time = json.load(json_file)
            LAST_PUBLISHED = datetime.datetime.strptime(
                published_time["LAST_PUBLISHED"], TIME_FORMAT)

    except Exception as e:  #If error, just keep the fault date (today - 1 day)
        print(f"ERROR, using default last times.\n{e}")
        logger.error(e)
        pass

    print(f"Last_Published: {LAST_PUBLISHED}")


def update_lasttimes():
    ''' Save lasttimes in json file '''

    with open(PUBLISH_JSON_PATH, 'w') as json_file:
        json.dump(
            {
                "LAST_PUBLISHED": LAST_PUBLISHED.strftime(TIME_FORMAT),
            }, json_file)

################## SEARCH STORIES FROM BLEEPING COMPUTER ####################

def get_stories(link):
    newsfeed = feedparser.parse(link)
    print(newsfeed)
    return newsfeed

def get_new_stories():

    global LAST_PUBLISHED

    stories = get_stories(BLEEPING_COM_UR)
    filtered_stories, new_published_time = filter_stories(stories["entries"], LAST_PUBLISHED)

    LAST_PUBLISHED = new_published_time

    return filtered_stories


def filter_stories(stories, last_published:datetime.datetime):

    filtered_stories = []
    new_last_time = last_published

    for story in stories:
        story_time = datetime.datetime.strptime(story["published"], TIME_FORMAT)
        if story_time > last_published:
            if ALL_VALID or is_summ_keyword_present(story["summary"]):

                filtered_stories.append(story)

        if story_time > new_last_time:
            new_last_time = story_time

    return filtered_stories, new_last_time

def is_summ_keyword_present(summary: str):
    ''' Given the summary check if any keyword is present '''

    return any(w in summary for w in DESCRIPTION_KEYWORDS) or \
            any(w.lower() in summary.lower() for w in DESCRIPTION_KEYWORDS_I) #for each of the word in description keyword config, check if it exists in summary.

#################### SEND MESSAGES #########################

def generate_new_story_message(new_stories) -> Embed:
    ''' Generate new CVE message for sending to slack '''

    nl = '\n'
    embed = Embed(
        title=f"🔈 *{new_stories['title']}* 🔈",
        description=new_stories["summary"] if len(new_stories["summary"]) < 500 else
        new_stories["summary"][:500] + "...",
        timestamp=datetime.datetime.utcnow(),
        color=Color.blue())
    embed.add_field(name=f"📅  *Published*",
                    value=f"{new_stories['Published']}",
                    inline=True)
    embed.add_field(name=f"More Information (_limit to 5_)",
                    value=f"{nl.join(new_stories['link'][:5])}",
                    inline=False)

    return embed

async def send_discord_message(message: Embed):
    ''' Send a message to the discord channel webhook '''

    discord_webhok_url = os.getenv('DISCORD_WEBHOOK_URL')

    if not discord_webhok_url:
        print("DISCORD_WEBHOOK_URL wasn't configured in the secrets!")
        return

    await sendtowebhook(webhookurl=discord_webhok_url, content=message)

async def sendtowebhook(webhookurl: str, content: Embed):
    async with aiohttp.ClientSession() as session:
        webhook = Webhook.from_url(webhookurl, session=session)
        await webhook.send(embed=content)


async def itscheckintime():

    load_keywords()
    load_lasttimes()

    new_stories = get_new_stories()

    new_title = [new_story['title'] for new_story in new_stories]
    print(f"New Stories: {new_title}")

    for story in new_stories:
       story_msg = generate_new_story_message(story)
       await send_discord_message(story_msg)

    update_lasttimes()

if __name__ == "__main__":
    scheduler = AsyncIOScheduler()
    scheduler.add_job(itscheckintime, 'interval', minutes=5)
    scheduler.start()
    print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit):
        pass
