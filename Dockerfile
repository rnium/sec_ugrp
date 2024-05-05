FROM python:3.8-slim-bullseye
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends pango1.0-tools &&\
    pip install --upgrade pip setuptools &&\
    pip install -r requirements.txt
RUN pip install django-cors-headers
RUN pip install sendgrid