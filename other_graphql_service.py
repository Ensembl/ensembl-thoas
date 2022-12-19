import uvicorn
from ariadne import QueryType, make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.contrib.federation import make_federated_schema

type_defs = """
  type Query {
    allele: Allele
    version: Version
  }
  
  type Allele {
    sequence: String
  }
  
  type Version {
    api: Api!
  }
  
  type Api {
    major: String!
    minor: String!
    patch: String!
  }

"""

query = QueryType()


@query.field("allele")
def resolve_allele(_, info):
    return {"sequence": "acgt"}


@query.field("version")
def resolve_version(_, info):
    return {"api": {"major": "a", "minor": "b", "patch": "c"}}


schema = make_federated_schema(type_defs, query)
application = GraphQL(schema)

if __name__ == "__main__":
    uvicorn.run(application, host="0.0.0.0", port=5002)
