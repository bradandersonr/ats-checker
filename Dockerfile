# syntax=docker/dockerfile:1
FROM python:3.12-bookworm
WORKDIR /code
ENV FLASK_APP=app/main.py
ENV FLASK_RUN_HOST=0.0.0.0
RUN set -ex; \
	apt-get update; \
	apt-get install -y build-essential
COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
EXPOSE 5000
COPY . .
CMD ["flask", "run"]