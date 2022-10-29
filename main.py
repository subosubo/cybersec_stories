import asyncio
import logging
import os
import pathlib
import sys
from doctest import debug_script
from os.path import join

import aiohttp
import yaml
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Embed, Webhook

from bleepingcomrss import bleepingcom
from keep_alive import keep_alive
from otxalien import otxalien

logger = logging.getLogger("cybersecstories")
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename="cybersec_stories.log",
                              encoding="utf-8",
                              mode="w")
handler.setFormatter(
    logging.Formatter("%(asctime)s:%(levelname)s:%(name)s: %(message)s"))
logger.addHandler(handler)


def load_keywords():
    # Load keywords from config file
    KEYWORDS_CONFIG_PATH = join(
        pathlib.Path(__file__).parent.absolute(), "config/config.yaml")
    try:

        with open(KEYWORDS_CONFIG_PATH, "r") as yaml_file:
            keywords_config = yaml.safe_load(yaml_file)
            print(f"Loaded keywords: {keywords_config}")
            ALL_VALID = keywords_config["ALL_VALID"]
            DESCRIPTION_KEYWORDS_I = keywords_config["DESCRIPTION_KEYWORDS_I"]
            DESCRIPTION_KEYWORDS = keywords_config["DESCRIPTION_KEYWORDS"]
            PRODUCT_KEYWORDS_I = keywords_config["PRODUCT_KEYWORDS_I"]
            PRODUCT_KEYWORDS = keywords_config["PRODUCT_KEYWORDS"]

            return (
                ALL_VALID,
                DESCRIPTION_KEYWORDS,
                DESCRIPTION_KEYWORDS_I,
                PRODUCT_KEYWORDS,
                PRODUCT_KEYWORDS_I,
            )
    except Exception as e:
        logger.error(e)
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
        webhook = Webhook.from_url(webhookurl, session=session)
        await webhook.send(embed=content)


#################### MAIN BODY #########################
async def itscheckintime():

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
    new_stories = bc.get_new_stories()

    bc_title = [new_story["title"] for new_story in new_stories]
    print(f"Bleeping Computer Stories: {bc_title}")

    for story in new_stories:
        story_msg = bc.generate_new_story_message(story)
        await send_discord_message(story_msg)

    bc.update_lasttimes()

    # otxalien
    alien = otxalien(
        ALL_VALID,
        DESCRIPTION_KEYWORDS,
        DESCRIPTION_KEYWORDS_I,
        PRODUCT_KEYWORDS,
        PRODUCT_KEYWORDS_I,
    )
    alien.load_lasttimes()
    new_pulses = alien.get_new_pulse()
    mod_pulses = alien.get_modified_pulse()

    pulse_title = [new_pulse["name"] for new_pulse in new_pulses]
    print(f"OTX Alien pulses: {pulse_title}")

    mod_pulse_title = [mod_pulse["name"] for mod_pulse in mod_pulses]
    print(f"OTX Alien mod pulses: {mod_pulse_title}")

    for pulse in new_pulses:
        pulse_msg = alien.generate_new_pulse_message(pulse)
        await send_discord_message(pulse_msg)

    for mod_pulse in mod_pulses:
        mod_pulse_msg = alien.generate_new_pulse_message(mod_pulse)
        await send_discord_message(mod_pulse_msg)

    alien.update_lasttimes()


if __name__ == "__main__":
    keep_alive()
    scheduler = AsyncIOScheduler()
    scheduler.add_job(itscheckintime, "interval", minutes=5)
    scheduler.start()
    print("Press Ctrl+{0} to exit".format("Break" if os.name == "nt" else "C"))

    # Execution will block here until Ctrl+C (Ctrl+Break on Windows) is pressed.
    try:
        asyncio.get_event_loop().run_forever()
    except (KeyboardInterrupt, SystemExit) as e:
        logger.error(f"{e}")
        raise e
