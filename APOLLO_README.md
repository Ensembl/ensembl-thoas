# Federating GraphQL services with Apollo

This repo contains an example implementation of an Apollo Gateway federating two GraphQL services.  The implementation 
is based on this documentation:

1. https://ariadnegraphql.org/docs/apollo-federation
2. https://www.apollographql.com/docs/apollo-server/using-federation/apollo-gateway-setup

The two GraphQL services are the Thoas service and a simple dummy service defined in `other_graphql_service.py`.

## Setup

Requirements: Python, NodeJS

1. Install node dependencies: `npm install`

2. Install Python dependencies: `pip install -r requirements-dev.txt`

3. Run the Thoas service: `PYTHONPATH='.' python3 graphql_service/server.py`
4. Run the other GraphQL service: `PYTHONPATH='.' python3 other_graphql_service.py`
5. Run the federated Apollo service: `node index.js`
6. Submit queries through the Apollo UI at http://localhost:4000/

## Notes
This is not the way to federate services that Apollo recommends.  Apollo docs recommend using an "Apollo router" instead
of an Apollo Gateway (https://www.apollographql.com/docs/federation/building-supergraphs/router).  I used an Apollo 
Gateway here because that's the method described in the Ariadne docs.