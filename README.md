# GraphQL for Ensembl

A [GraphQL trial](https://graphql.org/) for [Ensembl](https://www.ensembl.org) to reduce the need for RESTful web services.

This application is implemented with [Ariadne](https://ariadnegraphql.org/), a schema-first graphql framework for Python

/scripts contains tooling for populating backend databases

GraphQL requires a schema (in /common) and implementation of resolver functions that know how to interpret specific parts of a GraphQL query. Resolvers are found in /resolver, and may also make use of "data loaders" to overcome inherent deficiencies in GraphQL implementations.

## Installation

Set up Python 3
pip install -r .

## Running the service directly
Put configuration MongoDB configuration in a file e.g. mongo.conf

The file follows the following template:
```
[MONGO DB]
host = 
port = 
user = 
password = 
db = 
collection = 
```

GQL_CONF=mongo.conf uvicorn --workers 1 --host=0.0.0.0 graphql_service.server:APP

## Testing and development

Set this environment variable:
```
export META_CLASSIFIER_PATH=$PWD/docs/metadata_classifiers/
```
Then to run all the tests run ```pytest .```

## Containerisation
docker build -t $NAME:$VERSION .

Designed to be run in a Kubernetes-like environment, so configuration is externalised as a variable to tell it where the config is, and a config file that will be injected from the container environment.

This can be emulated at great effort using docker run's --mount command

docker container run --env GQL_CONF=/app/mongo.conf -w /app --publish 0.0.0.0:80:80/tcp --publish 0.0.0.0:8000:8000/tcp -ti $NAME:$VERSION uvicorn --workers 5 --host=0.0.0.0 graphql_service.server:app --env-file /app/$FILE_MOUNT

--publish above is exposing the container's ports to the host network

--env-file is the only apparent way to get any non-uvicorn environment variables into the application. It can point to the file mount of a k8s configmap, but in just a container, this would have to be created manually
