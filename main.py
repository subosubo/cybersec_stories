import asyncio
import logging
import os
import pathlib
import sys
from os.path import join, dirname
from dotenv import load_dotenv

import aiohttp
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bleepingcomrss import bleepingcom
from discord import Embed, HTTPException, Webhook
from hackernews import hackernews
from otxalien import otxalien
import json

dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

max_publish = 5

#################### LOG CONFIG #########################

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler("cybersec_stories.log", "a", "utf-8")
c_handler.setLevel(logging.WARNING)
f_handler.setLevel(logging.ERROR)

# Create formatters and add it to handlers
c_format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
f_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

# Add handlers to the logger
logger.addHandler(c_handler)
logger.addHandler(f_handler)

#################### LOAD STORIES FROM JSON #########################

STORY_JSON_PATH = join(pathlib.Path(__file__).parent.absolute(), "output/stories.json")
MOD_STORY_JSON_PATH = join(
    pathlib.Path(__file__).parent.absolute(), "output/modstories.json"
)


def load_stories_to_publish():
    try:
        liststories = []
        listmodstories = []
        with open(STORY_JSON_PATH) as fp:
            liststories = json.load(fp)
        with open(MOD_STORY_JSON_PATH) as modfp:
            listmodstories = json.load(modfp)
        fp.close()
        modfp.close()
        return liststories, listmodstories
    except Exception as e:
        logger.error(f"ERROR - {e}")


def store_stories_for_later(liststories, listmodstories):
    try:
        with open(STORY_JSON_PATH, "w") as json_file:
            json.dump(liststories, json_file, indent=4, separators=(",", ": "))
        with open(MOD_STORY_JSON_PATH, "w") as mod_json_file:
            json.dump(listmodstories, mod_json_file, indent=4, separators=(",", ": "))
        json_file.close()
        mod_json_file.close()
    except Exception as e:
        logger.error(f"ERROR - {e}")


#################### LOADING #########################


def load_keywords():
    # Load keywords from config file
    KEYWORDS_CONFIG_PATH = join(
        pathlib.Path(__file__).parent.absolute(), "config/config.yaml"
    )
    try:

        with open(KEYWORDS_CONFIG_PATH, "r") as yaml_file:
            keywords_config = yaml.safe_load(yaml_file)
            print(f"Loaded keywords: {keywords_config}")
            ALL_VALID = keywords_config["ALL_VALID"]
            DESCRIPTION_KEYWORDS_I = keywords_config["DESCRIPTION_KEYWORDS_I"]
            DESCRIPTION_KEYWORDS = keywords_config["DESCRIPTION_KEYWORDS"]
            PRODUCT_KEYWORDS_I = keywords_config["PRODUCT_KEYWORDS_I"]
            PRODUCT_KEYWORDS = keywords_config["PRODUCT_KEYWORDS"]

        yaml_file.close()

        return (
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
    except Exception as e:
        logger.error(f"Loading keyword Error:{e}")
        sys.exit(1)


#################### SEND MESSAGES #########################


async def send_discord_message(message: Embed):
    """Send a message to the discord channel webhook"""

    discord_webhok_url = os.getenv("DISCORD_WEBHOOK_URL")

    if not discord_webhok_url:
        print("DISCORD_WEBHOOK_URL wasn't configured in the secrets!")
        return

    await sendtowebhook(webhookurl=discord_webhok_url, content=message)


async def sendtowebhook(webhookurl: str, content: Embed):
    async with aiohttp.ClientSession() as session:
        try:
            webhook = Webhook.from_url(webhookurl, session=session)
            await webhook.send(embed=content)

        except HTTPException as e:
            logger.error(f"HTTP Error: {e}")
            os.system("kill 1")
        except Exception as e:
            logger.debug(f"{e}")
            os.system("kill 1")


#################### MAIN BODY #########################
async def itscheckintime():

    try:

        list_to_pub = []
        mod_list_to_pub = []

        list_to_pub, mod_list_to_pub = load_stories_to_publish()

        (
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        ) = load_keywords()

        # bleeping
        bc = bleepingcom(
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
        bc.load_lasttimes()
        bc.get_new_stories()
        bc.update_lasttimes()

        alien = otxalien(
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
        alien.load_lasttimes()
        alien.get_new_pulse()
        alien.get_modified_pulse()

        alien.update_lasttimes()

        hn = hackernews(
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
        hn.load_lasttimes()
        hn.get_new_stories()
        hn.update_lasttimes()

        if bc.new_stories:
            for story in bc.new_stories:
                list_to_pub.append(story)

        if hn.new_news:
            for hnews in hn.new_news:
                list_to_pub.append(hnews)

        if alien.new_pulses:
            for pulse in alien.new_pulses:
                if pulse["description"]:  # only publish if there is a description
                    list_to_pub.append(pulse)

        if alien.mod_pulses:
            for mod_pulse in alien.mod_pulses:
                if pulse["description"]:
                    mod_list_to_pub.append(mod_pulse)

        # if bc.new_stories:  # if bc has entries
        #     for story in bc.new_stories:
        #         story_msg = bc.generate_new_story_message(story)
        #         await send_discord_message(story_msg)

        # otxalien

        # if alien.new_pulses:
        #     for pulse in alien.new_pulses:
        #         pulse_msg = alien.generate_new_pulse_message(
        #             pulse
        #         )  # return an embed pulse only if there is a description in subscribed pulse
        #         if pulse_msg:
        #             await send_discord_message(pulse_msg)

        # if alien.mod_pulses:
        #     for mod_pulse in alien.mod_pulses:
        #         mod_pulse_msg = alien.generate_mod_pulse_message(mod_pulse)
        #         await send_discord_message(mod_pulse_msg)

        # if hn.new_news:
        #     for hnews in hn.new_news:
        #         news_msg = hn.generate_new_story_message(hnews)
        #         await send_discord_message(news_msg)

    except Exception as e:
        logger.error(f"{e}")


#################### MAIN #########################

if __name__ == "__main__":
    scheduler = AsyncIOScheduler(timezone="Asia/Singapore")
    scheduler.add_job(
        itscheckintime, "cron", day_of_week="mon-fri", hour="7-18", minute="*/5"
    )
    scheduler.start()
    print("Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C"))

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.warning(e)
        raise e
