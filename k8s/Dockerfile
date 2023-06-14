FROM python:3.8
# Contains relevant basics for Python, like GCC and similar by default
LABEL maintainer="ensembl-applications@ebi.ac.uk"

COPY . /app

RUN pip3 install -r /app/requirements.txt -e /app/

ENV PYTHONPATH=\$PYTHONPATH:/app

EXPOSE 8000

WORKDIR /app

CMD uvicorn --workers 2 --env /app/k8s/k8s-mongo.conf --host=0.0.0.0 graphql_service.server:app