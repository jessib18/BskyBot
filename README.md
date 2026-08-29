## About
Pulls tweets via xapi and reposts them to bsky

The bot is deployed via Docker and can then be run on a crontab to regularly check for new posts

> [TwitterScraper.py](BskyRepostBot/scripts/TwitterScraper.py)
    Searches for the newest posts and scrapes the data

> [bot.py](BskyRepostBot/scripts/bot.py)
    Creates the bsky post with the tweet data and posts it via atproto API

Working example: [link](https://bsky.app/profile/enstars-bot.bsky.social)
