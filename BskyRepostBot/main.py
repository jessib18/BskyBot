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
    url="https://nitter.net/ensemble_stars"
    scraper = TwitterScraper()
    scraper.scrape_nitter(url)

if __name__ == "__main__":
    main()