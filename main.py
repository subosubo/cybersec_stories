import asyncio
import logging
import os
import pathlib
import sys
import aiohttp
import yaml
import json
from os.path import join, dirname
from dotenv import load_dotenv
from discord import Color
from datetime import datetime
from time import sleep
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bleepingcomrss import bleepingcom
from vulnersrss import vulners
from discord import Embed, HTTPException, Webhook
from hackernews import hackernews
from otxalien import otxalien
from securityweekrss import securityweek


dotenv_path = join(dirname(__file__), ".env")
load_dotenv(dotenv_path)

max_publish = 2
dict_time_format = {"alien_tf": "%Y-%m-%dT%H:%M:%S.%f",
                    "bc_tf": "%a, %d %b %Y %H:%M:%S %z",
                    "hn_tf": "%a, %d %b %Y %H:%M:%S %z",
                    "vulner_tf": "%a, %d %b %Y %H:%M:%S %Z",
                    "sw_tf": "%a, %d %b %Y %H:%M:%S %z"}

#################### LOG CONFIG #########################

# create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


# create console handler and set level to debug
consolelog = logging.StreamHandler()
consolelog.setLevel(logging.INFO)

# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s')

# add formatter to ch
consolelog.setFormatter(formatter)

# create file handler and set level to debug
log_dir = Path(__file__).parent.absolute()
log_dir.mkdir(parents=True, exist_ok=True)
filelog = logging.FileHandler(
    log_dir / 'cybersec_stories_logfile.log', "a", "utf-8")
filelog.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to fh
filelog.setFormatter(formatter)

# add ch and fh to logger
logger.addHandler(consolelog)
logger.addHandler(filelog)

#################### LOAD STORIES FROM JSON #########################

STORY_JSON_PATH = join(pathlib.Path(
    __file__).parent.absolute(), "output/stories.json")
BLOG_JSON_PATH = join(pathlib.Path(
    __file__).parent.absolute(), "output/blog.json")
PULSE_JSON_PATH = join(pathlib.Path(
    __file__).parent.absolute(), "output/pulse.json")
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
        with open(BLOG_JSON_PATH) as fp:
            listblog = json.load(fp)
        fp.close()
        return liststories, listmodpulse, listpulse, listblog
    except Exception as e:
        logger.error(f"ERROR_LOAD:{e}")


def remove_duplicate(orig_list):
    new_list = [i for n, i in enumerate(
        orig_list) if i not in orig_list[n + 1:]]

    return new_list


def store_stories_for_later(liststories, listmodpulse, listpulse, listvulnersblog):
    try:
        with open(STORY_JSON_PATH, "w") as json_file:
            json.dump(liststories, json_file, indent=4, separators=(",", ": "))
        with open(MOD_PULSE_JSON_PATH, "w") as json_file:
            json.dump(listmodpulse, json_file,
                      indent=4, separators=(",", ": "))
        with open(PULSE_JSON_PATH, "w") as json_file:
            json.dump(listpulse, json_file, indent=4, separators=(",", ": "))
        with open(BLOG_JSON_PATH, "w") as json_file:
            json.dump(listvulnersblog, json_file,
                      indent=4, separators=(",", ": "))
        json_file.close()
    except Exception as e:
        logger.error(f"ERROR_STORE:{e}")


#################### LOAD CONFIG #########################


def load_keywords():
    # Load keywords from config file
    KEYWORDS_CONFIG_PATH = join(pathlib.Path(
        __file__).parent.absolute(), "config/config.yaml")
    try:

        with open(KEYWORDS_CONFIG_PATH, "r") as yaml_file:
            keywords_config = yaml.safe_load(yaml_file)
            logger.info(f"Loaded keywords: {keywords_config}")
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


def load_lasttimes() -> dict:
    RECORDS_JSON_PATH = join(pathlib.Path(
        __file__).parent.absolute(), "output/record.json")
    try:
        with open(RECORDS_JSON_PATH, 'r') as json_file:
            published_time = json.load(json_file)
            published_time['ALIEN_MODIFIED'] = datetime.strptime(
                published_time['ALIEN_MODIFIED'], dict_time_format['alien_tf'])
            published_time['ALIEN_CREATED'] = datetime.strptime(
                published_time['ALIEN_CREATED'], dict_time_format['alien_tf'])
            published_time['BC_LAST_PUBLISHED'] = datetime.strptime(
                published_time['BC_LAST_PUBLISHED'], dict_time_format['bc_tf'])
            published_time['HN_LAST_PUBLISHED'] = datetime.strptime(
                published_time['HN_LAST_PUBLISHED'], dict_time_format['hn_tf'])
            published_time['VULNER_LAST_PUBLISHED'] = datetime.strptime(
                published_time['VULNER_LAST_PUBLISHED'], dict_time_format['vulner_tf'])
            published_time['SW_LAST_PUBLISHED'] = datetime.strptime(
                published_time['SW_LAST_PUBLISHED'], dict_time_format['sw_tf'])

        json_file.close()
        return published_time

    except Exception as e:
        logger.error(f"ERROR-1: {e}")


def update_lasttimes(new_published_time: dict):
    RECORDS_JSON_PATH = join(pathlib.Path(
        __file__).parent.absolute(), "output/record.json")
    try:
        with open(RECORDS_JSON_PATH, 'w') as json_file:
            json.dump(new_published_time, json_file)
    except Exception as e:
        logger.error(f"ERROR-2: {e}")

#################### SEND MESSAGES #########################


def generate_new_story_message(new_story) -> Embed:
    embed = Embed(
        title=f"🔈 *{new_story['title']}*",
        description=new_story["summary"]
        if len(new_story["summary"]) < 500
        else new_story["summary"][:500] + "...",
        timestamp=datetime.now(),
        color=Color.light_gray(),
    )
    embed.add_field(
        name=f"📅  *Published*", value=f"{new_story['published']}", inline=True
    )
    embed.add_field(
        name=f"More Information", value=f"{new_story['link']}", inline=False
    )
    return embed


def generate_new_blog_message(new_blog) -> Embed:
    embed = Embed(
        title=f"🔈 *{new_blog['title']}*",
        description=new_blog["summary"]
        if len(new_blog["summary"]) < 500
        else new_blog["summary"][:500] + "...",
        timestamp=datetime.now(),
        color=Color.brand_green(),
    )
    embed.add_field(
        name=f"📅  *Published*", value=f"{new_blog['published']}", inline=True
    )
    embed.add_field(
        name=f"More Information", value=f"{new_blog['link']}", inline=False
    )
    return embed


def generate_new_pulse_message(new_pulse) -> Embed:
    nl = "\n"
    embed = Embed(
        title=f"🔈 *{new_pulse['name']}*",
        description=new_pulse["description"]
        if len(new_pulse["description"]) < 500
        else new_pulse["description"][:500] + "...",
        timestamp=datetime.now(),
        color=Color.dark_orange(),
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
    nl = "\n"
    embed = Embed(
        title=f"🔈 *Updated: {mod_pulse['name']}*",
        description=mod_pulse["description"]
        if len(mod_pulse["description"]) < 500
        else mod_pulse["description"][:500] + "...",
        timestamp=datetime.now(),
        color=Color.dark_orange(),
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
        logger.error(
            "DISCORD_WEBHOOK_URL wasn't configured in the secrets!")
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
            logger.error(f"ERROR_SEND:{e}")
            os.system("kill 1")


#################### MAIN BODY #########################
async def itscheckintime():

    try:

        stories_to_pub, mod_pulse_to_pub, pulse_to_pub, blog_to_pub = load_stories_to_publish()
        dict_pub_time = load_lasttimes()

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
        bc.LAST_PUBLISHED = dict_pub_time['BC_LAST_PUBLISHED']
        bc.get_articles_rss(dict_time_format['bc_tf'])
        dict_pub_time['BC_LAST_PUBLISHED'] = bc.LAST_PUBLISHED.strftime(
            dict_time_format['bc_tf'])

        thn = hackernews(
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
        thn.LAST_PUBLISHED = dict_pub_time['HN_LAST_PUBLISHED']
        thn.get_articles_rss(dict_time_format['hn_tf'])
        dict_pub_time['HN_LAST_PUBLISHED'] = thn.LAST_PUBLISHED.strftime(
            dict_time_format['hn_tf'])

        alien = otxalien(
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
        alien.ALIEN_CREATED = dict_pub_time['ALIEN_CREATED']
        alien.ALIEN_MODIFIED = dict_pub_time['ALIEN_MODIFIED']
        alien.get_new_pulse()
        alien.get_modified_pulse()
        dict_pub_time['ALIEN_CREATED'] = alien.ALIEN_CREATED.strftime(
            dict_time_format['alien_tf'])
        dict_pub_time['ALIEN_MODIFIED'] = alien.ALIEN_MODIFIED.strftime(
            dict_time_format['alien_tf'])

        # vulner blog
        vulner = vulners(
            ALL_VALID,
            DESCRIPTION_KEYWORDS,
            DESCRIPTION_KEYWORDS_I,
            PRODUCT_KEYWORDS,
            PRODUCT_KEYWORDS_I,
        )
        vulner.LAST_PUBLISHED = dict_pub_time['VULNER_LAST_PUBLISHED']
        vulner.get_articles_rss(dict_time_format['vulner_tf'])
        dict_pub_time['VULNER_LAST_PUBLISHED'] = vulner.LAST_PUBLISHED.strftime(
            dict_time_format['vulner_tf'])

        sw = securityweek(ALL_VALID,
                          DESCRIPTION_KEYWORDS,
                          DESCRIPTION_KEYWORDS_I,
                          PRODUCT_KEYWORDS,
                          PRODUCT_KEYWORDS_I,
                          )
        sw.LAST_PUBLISHED = dict_pub_time['SW_LAST_PUBLISHED']
        sw.get_articles_rss(dict_time_format['sw_tf'])
        dict_pub_time['SW_LAST_PUBLISHED'] = sw.LAST_PUBLISHED.strftime(
            dict_time_format['sw_tf'])

        stories_to_pub.extend(list(reversed(bc.new_stories)))
        stories_to_pub.extend(list(reversed(thn.new_news)))
        blog_to_pub.extend(list(reversed(vulner.new_vulners_blog)))
        blog_to_pub.extend(list(reversed(sw.new_SW_blog)))
        pulse_to_pub.extend(list(reversed(alien.new_pulses)))
        mod_pulse_to_pub.extend(list(reversed(alien.mod_pulses)))

        stories_to_pub = remove_duplicate(stories_to_pub)
        blog_to_pub = remove_duplicate(blog_to_pub)
        pulse_to_pub = remove_duplicate(pulse_to_pub)
        mod_pulse_to_pub = remove_duplicate(mod_pulse_to_pub)

        for story in stories_to_pub[:max_publish]:
            story_msg = generate_new_story_message(story)
            await send_discord_message(story_msg)

        for pulse in pulse_to_pub[:max_publish]:
            pulse_msg = generate_new_pulse_message(pulse)
            await send_discord_message(pulse_msg)

        for modpulse in mod_pulse_to_pub[:max_publish]:
            pulse_msg = generate_mod_pulse_message(modpulse)
            await send_discord_message(pulse_msg)

        for blog in blog_to_pub[:max_publish]:
            blog_msg = generate_new_blog_message(blog)
            await send_discord_message(blog_msg)

        update_lasttimes(dict_pub_time)

        store_stories_for_later(
            stories_to_pub[max_publish:],
            mod_pulse_to_pub[max_publish:],
            pulse_to_pub[max_publish:],
            blog_to_pub[max_publish:]
        )

    except Exception as e:
        logger.error(f"ERROR-1:{e}")
        sys.exit(1)


#################### MAIN #########################

if __name__ == "__main__":
    scheduler = AsyncIOScheduler(timezone="Asia/Singapore")
    scheduler.add_job(
        # , hour="8-18", minute="*/3"
        itscheckintime, "cron", day_of_week="mon-sun", hour="0-23", minute="*/3"
    )
    scheduler.start()

    logger.info(
        "Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C"))

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.warning(e)
        raise e
