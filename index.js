import { ApolloServer } from '@apollo/server';
import { startStandaloneServer } from '@apollo/server/standalone';
import { ApolloGateway, IntrospectAndCompose } from '@apollo/gateway';

const gateway = new ApolloGateway({

  supergraphSdl: new IntrospectAndCompose({
    subgraphs: [
      { name: 'thoas', url: 'http://localhost:5001' },
      { name: 'allele_service', url: 'http://localhost:5002' },
    ],
  }),
});

const server = new ApolloServer({
  gateway
});

const { url } = await startStandaloneServer(server);

console.log(`🚀  Server ready at ${url}`);