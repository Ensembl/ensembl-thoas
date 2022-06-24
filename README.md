# GraphQL for Ensembl

A [GraphQL trial](https://graphql.org/) for [Ensembl](https://www.ensembl.org) to reduce the need for RESTful web services.

This application is implemented with [Ariadne](https://ariadnegraphql.org/), a schema-first graphql framework for Python

/scripts contains tooling for populating backend databases on Codon.

GraphQL requires a schema (in /common) and implementation of resolver functions that know how to interpret specific parts of a GraphQL query. Resolvers are found in /resolver, and may also make use of "data loaders" to overcome inherent deficiencies in GraphQL implementations.

## Installation
Requires Python 3.7+.  

To install dependencies, run:

`pip install -r requirements-api.txt` for just the API.  Use this when deploying the service.

`pip install -r requirements-loading.txt` for just the data loading scripts.  Use this when running the loading scripts on Codon.

`pip install -r requirements-dev.txt` installs everything including dev dependencies like pytest, mypy etc.

## Running the API locally
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

This command will start the server:

```GQL_CONF=mongo.conf uvicorn --workers 1 --host=0.0.0.0 graphql_service.server:APP```


If you're developing in PyCharm, you will probably find it useful to create a run 
configuration so that you can use the debugger.  Create a run configuration that 
looks like this:

![Uvicorn run config](thoas_run_config.png)

## Development

### Testing

Navigate to the root of this repository and set this environment variable:
```
export META_CLASSIFIER_PATH=$PWD/docs/metadata_classifiers/
```
Then to run all the tests run ```pytest .```

### Linting

From the root of the repository:

`pylint $(git ls-files '*.py') --fail-under=9.5`

### Type checking

At the moment we only enforce type-checking in the API code.  Run this command from the root of the repository:

`mypy graphql_service`

## Containerisation
`docker build -t $NAME:$VERSION .`

Designed to be run in a Kubernetes-like environment, so configuration is externalised as a variable to tell it where the config is, and a config file that will be injected from the container environment.

This can be emulated at great effort using docker run's --mount command:

`docker container run --env GQL_CONF=/app/mongo.conf -w /app --publish 0.0.0.0:80:80/tcp --publish 0.0.0.0:8000:8000/tcp -ti $NAME:$VERSION uvicorn --workers 5 --host=0.0.0.0 graphql_service.server:app --env-file /app/$FILE_MOUNT`

`--publish` above is exposing the container's ports to the host network

`--env-file` is the only apparent way to get any non-uvicorn environment variables into the application. It can point to the file mount of a k8s configmap, but in just a container, this would have to be created manually

## Data loading

Instructions for loading Thoas data are here: https://www.ebi.ac.uk/seqdb/confluence/display/EA/Data+loading+on+Codon

### Data loading architecture

![Data loading architecture](loading_architecture.png)
