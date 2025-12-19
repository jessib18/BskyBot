## About
This is a simple python based webscraper which scrapes the newest posts from a twitter account (using nitter) and reposts them, including working hashtags, links and images to a specified bsky account via the atproto API 

The bot is deployed via Docker and can then be run on a crontab to regularly check for new posts

> [TwitterScraper.py](BskyRepostBot/scripts/TwitterScraper.py)
    Searches for the newest posts and scrapes the data

> [bot.py](BskyRepostBot/scripts/bot.py)
    Creates the bsky post with the tweet data and posts it via atproto API

Working example: [link](https://bsky.app/profile/enstars-bot.bsky.social)
