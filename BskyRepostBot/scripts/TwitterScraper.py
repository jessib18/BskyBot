import json
import os.path
import re
from datetime import datetime, timezone, timedelta
from .bot import Bot
import requests


from playwright.sync_api import Page, sync_playwright, Playwright

class TwitterScraper:

    image_folder:str = '././img'
    time_format:str = "%b %d, %Y · %I:%M %p %Z"

    def __init__(self):
        print("init TwitterScraper")
        self.timestamp_path='/persistent_data/timestamp.json'
        #self.timestamp_path = 'timestamp.json'

        if not os.path.exists(self.timestamp_path):
            raise Exception("timestamp file missing!")

    def save_timestamp(self, time:str):
        print("attempting to save " , time)
        with open(self.timestamp_path, 'w') as f:
            json.dump({"timestamp": time}, f, ensure_ascii=False)
            print("saved timestamp successfully")

    def get_timestamp(self):
        try:
            with open(self.timestamp_path, 'r') as f:  # Open file in read mode
                data = json.load(f)
                return datetime.strptime(data.get("timestamp"), self.time_format)
        except FileNotFoundError:
            print("failed to get timestamp")
            return None


    def scrape_images(self, urls):
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

        saved_paths = []
        for i, url in enumerate(urls):
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an error for bad responses

            # Extract the image file name from the URL
            image_name = f"image_{i + 1}.jpg"
            image_path = os.path.join(self.image_folder, image_name)

            # Save the image to the disk
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            print(f"Image {image_name} downloaded successfully!")
            saved_paths.append(image_path)

        return saved_paths

    def scrape_nitter(self, url):
        # go to nitter ensemble_stars
        print("start scrape nitter")
        bot = Bot()
        with sync_playwright() as playwright:
            browser = playwright.firefox.launch(headless=True)
            page = browser.new_page()
            page.goto(url)
            page.reload()

            my_time = self.get_timestamp() + timedelta(minutes=1)
            print("Last Timestamp: " + datetime.strftime(my_time, self.time_format))
            #get all recent tweets
            tweets: list = page.locator("div.timeline-item").all()
            tweets_to_repost: list = []
            for t in tweets :
                #exclude qrt and pinned
                if t.locator("div.quote").count() > 0 or t.locator("div.pinned").count() > 0 or t.locator("div.retweet-header").count() > 0:
                    continue
                time_posted = datetime.strptime(t.locator("span.tweet-date > a").get_attribute("title"), self.time_format)
                print("Posted at : " + datetime.strftime(time_posted, self.time_format))
                #include retweets
                if my_time < time_posted :
                    print("added")
                    tweets_to_repost.append(t)
                else:
                    print("Too old")
                    print("stop searching")
                    break

            i: int = len(tweets_to_repost) - 1
            for l in reversed(tweets_to_repost):
                post = self.scrape_post_nitter(page, l)
                if post["images"]:
                    bot.post_with_images(post["images"],post["text"])
                else: bot.post_text(post["text"])
                self.save_timestamp(tweets_to_repost[i].locator("span.tweet-date > a").get_attribute("title"))
                i -= 1



    def scrape_post_nitter(self, page, tweet):
        print("scraping post")
        post = {}
        content = tweet.locator("div.tweet-content")
        tweet_text = content.inner_text()
        print("tweet text: " + tweet_text)
        links = content.locator("a").all()

        print("replace links")
        for link in links:
            link_text = link.inner_text()
            print("link: " + link_text)
            url = link.get_attribute("href")
            if url and link_text[0] != '#':
                print("link replaced with: " + url)
                tweet_text = tweet_text.replace(link_text, url)
        post["text"] = tweet_text
        post["images"] = self.scrape_image_nitter(page, tweet)
        return post


    def scrape_image_nitter(self, page, tweet):
        print("scraping images")
        if not os.path.exists(self.image_folder):
            os.makedirs(self.image_folder)

        saved_paths = []

        images = tweet.locator("div.attachments a.still-image").all()
        urls = []

        for link in images:
            url = link.get_attribute("href")
            print("added image link: " + url)
            urls.append("https://nitter.net" + url)


        for i,url in enumerate(urls):
            response = requests.get(url, stream=True)
            response.raise_for_status()  # Raise an error for bad responses

            # Extract the image file name from the URL
            image_name = f"image_{i + 1}.jpg"  # You can customize the naming scheme here
            image_path = os.path.join(self.image_folder, image_name)

            # Save the image to the disk
            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            print(f"Image {image_name} downloaded successfully!")
            saved_paths.append(image_path)

        return saved_paths

    #
    # def scrape_tweet_data(self,link):
    #     print("scraping ", link)
    #
    #     post = {}
    #
    #     with sync_playwright() as playwright:
    #         browser = playwright.firefox.launch(headless=True)
    #         page = browser.new_page()
    #         page.goto(link)
    #         page.wait_for_selector("[data-testid='tweet']")
    #
    #         tweet_text = page.query_selector('div[data-testid="tweetText"]').inner_text()
    #         print(page.query_selector('div[data-testid="tweetText"]').inner_text())
    #         post["text"] = tweet_text
    #
    #         print("check for images")
    #         images = page.query_selector_all('img[src*="pbs.twimg.com/media/"]')
    #         print("images found: " + str(len(images)))
    #         image_links = []
    #
    #         ad_image = "https://pbs.twimg.com/media/G2mXZqkWMAAhLlQ?format=jpg&name=240x240"
    #
    #         for i in images:
    #             image_url:str = i.get_attribute('src')
    #             if image_url and image_url != ad_image:
    #                 image_links.append(image_url)
    #                 print("image added: ", image_url)
    #
    #             if len(image_links) >= 4:
    #                 break
    #
    #         post["images"] = self.scrape_images(image_links)
    #         browser.close()
    #         return post