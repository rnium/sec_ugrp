FROM python:3.8-slim-bullseye
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip setuptools &&\
    pip install -r requirements.txt