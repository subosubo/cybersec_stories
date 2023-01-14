# cybersec_stories

Description (According to ChatGPT, Kudos)

This is a Python script that appears to be checking for new articles or news stories from various sources (such as BleepingComputer, HackerNews, and AlienVault) and loading them into different lists (e.g. "stories_to_pub", "mod_pulse_to_pub", "pulse_to_pub", "blog_to_pub"). It is also loading keywords, timestamps, and other data from various files or functions (such as "load_stories_to_publish()" and "load_keywords()"). It appears to be using these sources and keywords to filter the articles and only add relevant ones to the lists for later publishing to discord.

Few things to setup before using:
1. Webhook to your discord server
2. AlienVault API Key

- pet project for learning python, so feel free to comment on the code and how I can improve
- ran it on replit and later to rpi, because i didn't know how to handle discord's ratelimit responses. 