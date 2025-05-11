FROM python:3.12-bookworm
LABEL maintainer="Brad Anderson <brad@andersonr.com>"

ARG UID=1000
ARG GID=1000

WORKDIR /app

ARG FLASK_DEBUG="false"
ENV FLASK_DEBUG="${FLASK_DEBUG}" 
ENV FLASK_APP=app/main.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV USER="python"

# Install build essential for setting up Python env
RUN set -ex; \
	apt-get update; \
	apt-get install -y build-essential

COPY requirements.txt requirements.txt

# Upgrade PIP and install requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Remove build-essential and clean up/harden system
RUN apt-get purge -y build-essential \
    && apt-get autoremove -y \
	&& apt-get clean

RUN rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man
  	
	RUN groupadd -g "${GID}" python \
		&& useradd --create-home --no-log-init -u "${UID}" -g "${GID}" python \
		&& chown python:python -R /app

USER python

COPY --chown=python:python . .

CMD ["flask", "run"]