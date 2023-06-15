# GraphQL for Ensembl

A [GraphQL trial](https://graphql.org/) for [Ensembl](https://www.ensembl.org) to reduce the need for RESTful web services.

This application is implemented with [Ariadne](https://ariadnegraphql.org/), a schema-first graphql framework for Python

GraphQL requires a schema (in /common) and implementation of resolver functions that know how to interpret specific parts of a GraphQL query. Resolvers are found in /resolver, and may also make use of "data loaders" to overcome inherent deficiencies in GraphQL implementations.

https://www.ebi.ac.uk/seqdb/confluence/display/EA/Thoas+Docs

## Installation
Requires Python 3.8+.  

To install dependencies, run:

`pip install -r requirements.txt` for just the API.  Use this when deploying the service.

`pip install -r requirements-dev.txt` installs everything including dev dependencies like pytest, mypy etc.

## Running the API locally
Add MongoDB and GRPC configuration `./connections.conf`

The file follows the following template:
```
mongo_host=MONGO_IP_ADDRESS
mongo_port=MONGO_PORT
mongo_user=MONGO_USER
mongo_password=MONGO_PASS
mongo_db=MONGO_DB_NAME
mongo_collection=MONGO_COLLECTION
grpc_host=GRPC_HOST
grpc_port=GRPC_PORT
```

This command will start the server:

```uvicorn --workers 1 --host=0.0.0.0 graphql_service.server:APP```


If you're developing in PyCharm, you will probably find it useful to create a run 
configuration so that you can use the debugger.  Create a run configuration that 
looks like this:

![Uvicorn run config](thoas_run_config.png)

## Development

### Testing

```
cd ensembl-thoas
pytest .
```

### Linting

From the root of the repository:

```
cd ensembl-thoas
pylint $(git ls-files '*.py') --fail-under=9.5
```

### Type checking

```
cd ensembl-thoas
mypy graphql_service
```

### Formatting

`black . --check --diff` previews the formatting.

`black .` applies the formatting in-place.

## Containerisation

Build the image using `./Dockerfile`:

`docker build -t $NAME:$VERSION .`

Run a container with the image (`--publish` below is exposing the container's ports to the host network):

`docker container run --publish 0.0.0.0:80:80/tcp --publish 0.0.0.0:8000:8000/tcp -ti $NAME:$VERSION`

The connection configuration is assumed to exist in the repo as the file `./connections.conf` and gets built into the Docker 
image. On Kubernetes cluster, these configs are passed through k8s objects called a escrets.  If we want to emulate this 
in Docker then we could look into using Docker [bind mounts](https://docs.docker.com/storage/bind-mounts/).
