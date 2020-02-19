FROM python:3.8.1-slim as build
# Contains relevant basics for Python, like GCC and similar by default
LABEL maintainer="ktaylor@ebi.ac.uk"

COPY . /app

RUN pip3 install -r /app/requirements.txt -e /app/

ENV PYTHONPATH=\$PYTHONPATH:/app

# The file must contain MongoDB configuration. 
# mongo.conf is not in the container by default, and this will fail
ENV GQL_CONF=/app/mongo.conf

ENV WORKER_COUNT=10
CMD uvicorn --workers $WORKER_COUNT --env GQL_CONF --host=0.0.0.0 graphql_service.server:app