FROM python:3.8.1-slim as build
# Contains relevant basics for Python, like GCC and similar by default
LABEL maintainer="ktaylor@ebi.ac.uk"

# Use buildargs to provide credentials
ARG GIT_USER
ARG GIT_TOKEN
ENV GIT_USER=$GIT_USER
ENV GIT_TOKEN=$GIT_TOKEN

# Begin nested build to preserve only data, not crendentials used to make it
FROM build

COPY . /app

RUN pip3 install -r /app/requirements.txt -e /app/

ENV PYTHONPATH=\$PYTHONPATH:/app

# Inject variables for application via SERVERCONF:
# GQL_CONF=/path/to/virtualfile
# The file must contain MongoDB configuration
ARG SERVERCONF
ENV SERVERCONF=$SERVERCONF

ENV WORKER_COUNT=10
CMD uvicorn --workers $WORKER_COUNT --env-file $SERVERCONF --host=0.0.0.0 metadata_service.server:app