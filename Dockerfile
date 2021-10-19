FROM python:3.8
RUN apt-get update && apt-get install build-essential libjpeg-dev zlib1g-dev python3-dev -y
RUN pip install cython
RUN pip install --no-cache-dir python-telegram-bot tinydb wordcloud_fa stop-words
WORKDIR /app
COPY bot.py ./
CMD [ "python", "./bot.py" ]