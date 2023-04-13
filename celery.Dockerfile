FROM python:3.8

RUN apt-get update

RUN pip install --upgrade pip

RUN mkdir /app

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt