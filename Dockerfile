FROM python:3.10.14
# Contains relevant basics for Python, like GCC and similar by default
LABEL maintainer="ensembl-applications@ebi.ac.uk"

COPY . /app

RUN pip3 install -r /app/requirements.txt -e /app/

ENV PYTHONPATH=\$PYTHONPATH:/app

EXPOSE 8000

WORKDIR /app

ENV WORKER_COUNT=2
CMD uvicorn --workers $WORKER_COUNT --host=0.0.0.0 graphql_service.server:APP