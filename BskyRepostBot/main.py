import json
import os
from dotenv import load_dotenv
import scripts
from scripts.bot import Bot
from scripts.TwitterScraper import TwitterScraper
from datetime import datetime


def main():
    print("++++start+++++")
    load_dotenv()
    bot = Bot()
    #url="https://nitter.net/ensemble_stars"
    scraper = TwitterScraper()
    scraper.scrape_xapi()
    print("+++++end+++++")
    # with open('test_tweet.json') as f:
    #     test_tweet:dict = json.load(f)
    # scraper.test_xapi(test_tweet)

if __name__ == "__main__":
    main()