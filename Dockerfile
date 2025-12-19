FROM python:3.12-bookworm

WORKDIR /app
COPY BskyRepostBot/requirements.txt .


RUN pip install playwright && \
    playwright install --with-deps

#webp support 
RUN apt-get update && apt-get install -y \
    libwebp-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt
COPY BskyRepostBot .


CMD ["python", "main.py"]
