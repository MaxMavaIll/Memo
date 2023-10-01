FROM python:3.10-slim

RUN apt-get update 

WORKDIR  /app

COPY . .

RUN pip install -r requirements.txt

CMD [ "python", "main.py" ]