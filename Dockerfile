FROM python:3.12-bookworm
ENV DISPLAY=:99

WORKDIR /app
COPY BskyRepostBot/requirements.txt .


RUN pip install playwright && \
    playwright install --with-deps

#webp support 
RUN apt-get update && apt-get install -y \
    libwebp-dev \
    libpci3 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -r requirements.txt
COPY BskyRepostBot .
COPY /persistent_data/timestamp.json .
COPY entrypoint.sh .

#CMD ["/app/entrypoint.sh"]
CMD ["python", "-u", "main.py"]