import asyncio
import logging
import os
import pathlib
import sys
from os.path import join, dirname
from dotenv import load_dotenv
from discord import Color
import datetime
from time import sleep

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
PULSE_JSON_PATH = join(pathlib.Path(__file__).parent.absolute(), "output/pulse.json")
MOD_PULSE_JSON_PATH = join(
    pathlib.Path(__file__).parent.absolute(), "output/modpulse.json"
)


def load_stories_to_publish():
    try:
        with open(STORY_JSON_PATH) as fp:
            liststories = json.load(fp)
        with open(MOD_PULSE_JSON_PATH) as fp:
            listmodpulse = json.load(fp)
        with open(PULSE_JSON_PATH) as fp:
            listpulse = json.load(fp)
        fp.close()
        return liststories, listmodpulse, listpulse
    except Exception as e:
        logger.error(f"ERROR_LOAD:{e}")


def store_stories_for_later(liststories, listmodpulse, listpulse):
    try:
        with open(STORY_JSON_PATH, "w") as json_file:
            json.dump(liststories, json_file, indent=4, separators=(",", ": "))
        with open(MOD_PULSE_JSON_PATH, "w") as json_file:
            json.dump(listmodpulse, json_file, indent=4, separators=(",", ": "))
        with open(PULSE_JSON_PATH, "w") as json_file:
            json.dump(listpulse, json_file, indent=4, separators=(",", ": "))
        json_file.close()
    except Exception as e:
        logger.error(f"ERROR_STORE:{e}")


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
        logger.error(f"ERROR_KW:{e}")
        sys.exit(1)


#################### SEND MESSAGES #########################


def generate_new_story_message(new_story) -> Embed:
    # Generate new CVE message for sending to discord
    embed = Embed(
        title=f"🔈 *{new_story['title']}*",
        description=new_story["summary"]
        if len(new_story["summary"]) < 500
        else new_story["summary"][:500] + "...",
        timestamp=datetime.datetime.now(),
        color=Color.light_gray(),
    )
    embed.add_field(
        name=f"📅  *Published*", value=f"{new_story['published']}", inline=True
    )
    embed.add_field(
        name=f"More Information", value=f"{new_story['link']}", inline=False
    )
    return embed


def generate_new_pulse_message(new_pulse) -> Embed:

    nl = "\n"
    if new_pulse["description"]:
        embed = Embed(
            title=f"🔈 *{new_pulse['name']}*",
            description=new_pulse["description"]
            if len(new_pulse["description"]) < 500
            else new_pulse["description"][:500] + "...",
            timestamp=datetime.datetime.now(),
            color=Color.light_gray(),
        )
        embed.add_field(
            name=f"📅  *Published*", value=f"{new_pulse['created']}", inline=True
        )
        embed.add_field(
            name=f"📅  *Last Modified*",
            value=f"{new_pulse['modified']}",
            inline=True,
        )
        try:
            embed.add_field(
                name=f"More Information (_limit to 5_)",
                value=f"{nl.join(new_pulse['references'][:5])}",
                inline=False,
            )
        except KeyError:
            embed.add_field(
                name=f"More Information:",
                value=f"https://otx.alienvault.com/pulse/{new_pulse['id']}",
                inline=False,
            )
    return embed


def generate_mod_pulse_message(mod_pulse) -> Embed:
    # Generate new CVE message for sending to discord
    nl = "\n"
    embed = Embed(
        title=f"🔈 *Updated: {mod_pulse['name']}*",
        description=mod_pulse["description"]
        if len(mod_pulse["description"]) < 500
        else mod_pulse["description"][:500] + "...",
        timestamp=datetime.datetime.now(),
        color=Color.light_gray(),
    )
    embed.add_field(
        name=f"📅  *Published*", value=f"{mod_pulse['created']}", inline=True
    )
    embed.add_field(
        name=f"📅  *Last Modified*", value=f"{mod_pulse['modified']}", inline=True
    )
    try:
        embed.add_field(
            name=f"More Information (_limit to 5_)",
            value=f"{nl.join(mod_pulse['references'][:5])}",
            inline=False,
        )
    except KeyError:
        embed.add_field(
            name=f"More Information (_limit to 5_)",
            value=f"N/A",
            inline=False,
        )
    return embed


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
            logger.error(f"ERROR_SEND_HTTP: {e}")
            sleep(180)
            await webhook.send(embed=content)
        except Exception as e:
            logger.debug(f"ERROR_SEND:{e}")
            os.system("kill 1")


#################### MAIN BODY #########################
async def itscheckintime():

    try:

        stories_to_pub = []
        pulse_to_pub = []
        mod_pulse_to_pub = []

        stories_to_pub, mod_pulse_to_pub, pulse_to_pub = load_stories_to_publish()

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
                stories_to_pub.append(story)

        if hn.new_news:
            for hnews in hn.new_news:
                stories_to_pub.append(hnews)

        if alien.new_pulses:
            for pulse in alien.new_pulses:
                if pulse["description"]:  # only publish if there is a description
                    pulse_to_pub.append(pulse)

        if alien.mod_pulses:
            for mod_pulse in alien.mod_pulses:
                if pulse["description"]:
                    mod_pulse_to_pub.append(mod_pulse)

        if stories_to_pub:
            for story in stories_to_pub[:max_publish]:
                story_msg = generate_new_story_message(story)
                await send_discord_message(story_msg)

        if pulse_to_pub:
            for pulse in pulse_to_pub[:max_publish]:
                pulse_msg = generate_new_pulse_message(pulse)
                await send_discord_message(pulse_msg)

        if mod_pulse_to_pub:
            for modpulse in mod_pulse_to_pub[:max_publish]:
                pulse_msg = generate_mod_pulse_message(modpulse)
                await send_discord_message(pulse_msg)

        store_stories_for_later(
            stories_to_pub[max_publish:],
            mod_pulse_to_pub[max_publish:],
            pulse_to_pub[max_publish:],
        )

    except Exception as e:
        logger.error(f"ERROR-1:{e}")
        sys.exit(1)


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
