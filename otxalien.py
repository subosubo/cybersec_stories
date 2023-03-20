import datetime
import logging
import os
import pytz
import requests
from enum import Enum
from os.path import join

utc = pytz.UTC


class time_type(Enum):
    created = "created"
    modified = "modified"


class otxalien:
    def __init__(self, valid, keywords, keywords_i, product, product_i, last_created, last_modified, time_format):
        self.valid = valid
        self.keywords = keywords
        self.keywords_i = keywords_i
        self.product = product
        self.product_i = product_i

        self.ALIENVAULT_UR = "https://otx.alienvault.com/api/v1/pulses/subscribed?"
        self.ALIEN_TIME_FORMAT = time_format
        self.ALIEN_MODIFIED = last_modified
        self.ALIEN_CREATED = last_created
        self.logger = logging.getLogger("__main__")
        self.logger.setLevel(logging.DEBUG)
        self.new_pulses = []
        self.pulse_title = []
        self.mod_pulses = []
        self.mod_pulse_title = []

    ################## GET PULSES FROM OTX ALIEN  ####################

    def get_sub_pulse(self):

        now = datetime.datetime.now() - datetime.timedelta(days=1)
        now_str = now.strftime("%Y-%m-%d")
        limit = 100

        headers = {
            "Content-Type": "application/json",
            "X-OTX-API-KEY": os.getenv("ALIEN_VAULT_API"),
        }

        r = requests.get(
            f"{self.ALIENVAULT_UR}limit={limit}&modified_since={now_str}",
            headers=headers,
        )

        return r.json()

    def filter_pulse(
        self, pulses, last_create: datetime.datetime, tt_filter: time_type
    ):

        filtered_pulses = []
        new_last_time = last_create

        for pulse in pulses:
            if not (pulse["description"] and pulse['references']):
                continue

            pulse_time = datetime.datetime.strptime(
                pulse[tt_filter.value], self.ALIEN_TIME_FORMAT
            )
            if pulse_time > last_create:
                if self.valid or self.is_summ_keyword_present(pulse["description"]):

                    filtered_pulses.append(pulse)

            if pulse_time > new_last_time:
                new_last_time = pulse_time

        return filtered_pulses, new_last_time

    def is_summ_keyword_present(self, summary: str):
        # Given the summary check if any keyword is present

        return any(w in summary for w in self.keywords) or any(
            w.lower() in summary.lower() for w in self.keywords_i
        )  # for each of the word in description keyword config, check if it exists in summary.

    def get_new_pulse(self):

        stories = self.get_sub_pulse()
        self.new_pulses, self.ALIEN_CREATED = self.filter_pulse(
            stories["results"], self.ALIEN_CREATED, time_type.created
        )

        self.pulse_title = [new_pulse["name"] for new_pulse in self.new_pulses]
        self.logger.info(f"OTX Alien pulses: {self.pulse_title}")

    def get_modified_pulse(self):

        stories = self.get_sub_pulse()
        filtered_pulses, self.ALIEN_MODIFIED = self.filter_pulse(
            stories["results"], self.ALIEN_MODIFIED, time_type.modified
        )

        self.mod_pulses = [
            mpulse
            for mpulse in filtered_pulses
            if mpulse["name"] not in self.pulse_title
        ]

        self.mod_pulse_title = [mpulse["name"] for mpulse in self.mod_pulses]
        self.logger.info(f"OTX Alien mod pulses: {self.mod_pulse_title}")
