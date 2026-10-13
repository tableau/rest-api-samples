# (Beta) LLM Open Connector API

This Beta spec is for your use when creating the integration between your LLM gateway and the Tableau Agent through the Tableau LLM gateway. 

It is based on the Open AI standard with modifications for the Tableau gateway requirements.

It describes the endpoints, along with their  parameter and property schemas, that match the Tableau gateway request and response pattern.

The two operations of the spec are:

- Create embedding vector (/embeddings) - Creates an embedding vector representing the input text.

- Create chat response (chat/completions ) - Creates a model response for the given chat conversation.

Adjust security configuration to suit your needs. This spec shows the configuration for a simple API key.