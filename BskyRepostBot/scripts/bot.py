import io
import os
import time
import re
from typing import List, Dict
from http.client import responses

from dotenv import load_dotenv
from atproto import Client
from PIL import Image




BLUESKY_USER=""
BLUESKY_PW=""


class Bot:
    def __init__(self):
        load_dotenv()
        self.client = Client()
        self.max_retries = 5
        self.delay = 1.0

    def try_login(self):
        retries = 0
        while retries < self.max_retries:
            try:
                self.client.login(
                    os.getenv("BLUESKY_USER"),
                    os.getenv("BLUESKY_PW"))
                print("login success")
                return
            except Exception as e:
                print("fail")
                if "RateLimitExceeded" in str(e):
                    time.sleep(self.delay)
                    retries += 1
                else:
                    raise e
        raise Exception("Max retries exceeded. Could not log in to Bluesky.")

    def post_text(self,text:str):
        self.try_login()

        # post_data = {"text": text,
        #              "createdAt": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
        #              "facets": self.parse_facets(text)}
        facets:List[Dict] = self.parse_facets(text)
        v=None
        try:
            response = self.client.post(text,v,v,v,v, facets)
            print("just posted")
        except Exception as e:
            print(e)



    def get_aspect_ratio(self,path):
        with Image.open(path) as img:
            width, height = img.size
            print(width,height)
        return {"width": width, "height":height}


    def extract_hashtags(self,text):
        text_bytes = text.encode("UTF-8")

        # Regex to find hashtags in the text (works in byte format)
        hashtag_regex = rb"#(\S+)"

        facets = []
        current_position = 0

        # Search for hashtags
        for m in re.finditer(hashtag_regex, text_bytes):
            hashtag = m.group(0).decode("UTF-8")
            print("extracted hashtag: ",hashtag)
            start = m.start(0)
            end = m.end(0)

            # Create the facet for the hashtag
            facets.append({
                "index": {
                    "byteStart": start,
                    "byteEnd": end,
                },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        "uri": f"https://bsky.app/hashtag/{hashtag[1:]}",
                        # Remove the '#' from the hashtag for the URI
                    }
                ],
            })

        return facets


    def parse_facets(self,text):
        facets = []
        for u in self.parse_urls(text):
            facets.append({
                "index": {
                    "byteStart": u["start"],
                    "byteEnd": u["end"],
                },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#link",
                        "uri": u["url"],
                    }
                ],
            })

        for h in self.parse_hashtags(text):
            facets.append({
                "index": {
                    "byteStart": h["start"],
                    "byteEnd": h["end"],
                },
                "features": [
                    {
                        "$type": "app.bsky.richtext.facet#tag",
                        "tag": h['tag'][1:],
                    }
                ],
            })

        return facets

    def expand_urls(self, text, x_facets):
        for u in x_facets.get("urls", []):
            short_url = u.get("url")
            expanded = u.get("expanded_url")
            if short_url and short_url in text:
                text = text.replace(short_url, expanded)

        text = re.sub(r'\s+https://t\.co/\S+', '', text)
        return text

    def parse_urls(self,text: str) -> List[Dict]:
        spans = []
        # partial/naive URL regex based on: https://stackoverflow.com/a/3809435
        # tweaked to disallow some training punctuation
        url_regex = rb"[$|\W](https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*[-a-zA-Z0-9@%_\+~#//=])?)"
        text_bytes = text.encode("UTF-8")
        for m in re.finditer(url_regex, text_bytes):
            spans.append({
                "start": m.start(1),
                "end": m.end(1),
                "url": m.group(1).decode("UTF-8"),
            })
        return spans

    def parse_hashtags(self, text:str) -> List[Dict]:
        hashtag_regex = rb"#(\S+)"
        hashtags = []
        text_bytes = text.encode("UTF-8")

        for m in re.finditer(hashtag_regex, text_bytes):
            hashtag = m.group(0).decode("UTF-8")  # Decode back to UTF-8 string
            print("extracted hashtag: ",hashtag)
            hashtags.append({
                "start": m.start(1)-1,
                "end": m.end(1),
                "tag": hashtag
            })

        return hashtags

    def post_with_images(self, image_paths,text):
        f = self.parse_facets(text)
        self.try_login()

        # Loop through images and attach them
        uploaded_images = []
        ratios = []
        for path in image_paths:
            with Image.open(path) as img:
                if img.mode not in ["RGB", "RGBA"]:
                    img = img.convert("RGB")

                img_bytes = io.BytesIO()
                img.save(img_bytes, format="WEBP", quality=85)
                uploaded_images.append(img_bytes.getvalue())
            ratios.append(self.get_aspect_ratio(path))

        retry_counter = 0
        max_retries = 5

        while retry_counter < max_retries:
            retry_counter +=1
            try:

               # self.create_facet_for_hashtags(text)
                # Post text and images
                post = self.client.send_images(
                    text=text,
                    images=uploaded_images,
                    image_aspect_ratios=ratios,
                    facets=f
                )

                print("posted successfully")

                # Clean up images after successful post
                for image_path in image_paths:
                    os.remove(image_path)
                    print("deleted images from disk")
                retry_counter = max_retries +1

            except Exception as e:
                print("failed to post")
                for image_path in image_paths:
                    os.remove(image_path)
                    print("deleted images from disk")
                raise e

    def translate_facets(self, f, text):
        facets = []
        text_bytes = text.encode('utf-8')
        if "hashtags" in f:
            for h in f.get("hashtags"):
                start_char =  h["indices"][0]
                end_char = h["indices"][1]      

                byte_start = len(text[:start_char].encode('utf-8'))
                byte_end = len(text[:end_char].encode('utf-8'))
                facets.append({
                    "index": {
                        "byteStart": byte_start,
                        "byteEnd": byte_end,
                    },
                    "features": [
                        {
                            "$type": "app.bsky.richtext.facet#tag",
                            "tag": f"https://bsky.app/hashtag/{h['text']}",
                        }
                    ],
                })
        if "urls" in f:
            for u in f.get("urls"):
                start_char =  u["indices"][0]
                end_char = u["indices"][1]      

                byte_start = len(text[:start_char].encode('utf-8'))
                byte_end = len(text[:end_char].encode('utf-8'))
                facets.append({
                                "index": {
                                    "byteStart": byte_start,
                                    "byteEnd": byte_end,
                                },
                                "features": [
                                    {
                                        "$type": "app.bsky.richtext.facet#link",
                                        "uri": u["expanded_url"],
                                    }
                                ],
                            })
        return facets


    def post_image_xapi(self, image_paths, text, x_facets):
        text = self.expand_urls(text, x_facets)
        f = self.parse_facets(text)
        self.try_login()
        
        # Loop through images and attach them
        uploaded_images = []
        ratios = []
        for path in image_paths:
            with Image.open(path) as img:
                if img.mode not in ["RGB", "RGBA"]:
                    img = img.convert("RGB")

                img_bytes = io.BytesIO()
                img.save(img_bytes, format="WEBP", quality=85)
                uploaded_images.append(img_bytes.getvalue())
            ratios.append(self.get_aspect_ratio(path))

        retry_counter = 0
        max_retries = 5

        while retry_counter < max_retries:
            retry_counter +=1
            try:

                # self.create_facet_for_hashtags(text)
                # Post text and images
                post = self.client.send_images(
                    text=text,
                    images=uploaded_images,
                    image_aspect_ratios=ratios,
                    facets=f
                )

                print("posted successfully")

                # Clean up images after successful post
                for image_path in image_paths:
                    os.remove(image_path)
                    print("deleted images from disk")
                retry_counter = max_retries +1

            except Exception as e:
                print("failed to post")
                for image_path in image_paths:
                    os.remove(image_path)
                    print("deleted images from disk")
                raise e

    def post_video_xapi(self, video_bytes, text, x_facets):
        text = self.expand_urls(text, x_facets)
        f = self.parse_facets(text)
        self.try_login()
        try:
            post = self.client.send_video(
                video=video_bytes,
                text=text,
                facets=f
            )
            print("posted successfully")
        except Exception as e:
            print("failed to post")
            raise e


    def post_text_xapi(self,text,x_facets):
        self.try_login()
        text = self.expand_urls(text, x_facets)
        # post_data = {"text": text,
        #              "createdAt": time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime()),
        #              "facets": self.parse_facets(text)}
        facets:List[Dict] = self.parse_facets(text)
        v=None
        try:
            response = self.client.post(text,v,v,v,v, facets)
            print("just posted")
        except Exception as e:
            print(e)
        pass


