FROM python:3.10-slim

RUN apt-get update
RUN apt-get install unzip curl -y

WORKDIR  /app

RUN mkdir /app/API
COPY ./Update .
COPY requirements.txt .
COPY WorkJson.py .
COPY ./API /app/API

RUN pip install -r requirements.txt

CMD [ "python", "update_elements.py" ]