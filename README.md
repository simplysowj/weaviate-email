# Retrieval-Augmented Generation (RAG) API

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-green.svg)
![Weaviate](https://img.shields.io/badge/Weaviate-1.22+-orange.svg)
![OpenAI](https://img.shields.io/badge/OpenAI-gpt--3.5--turbo-purple.svg)

A high-performance API for question-answering using Retrieval-Augmented Generation (RAG) with Weaviate vector search and OpenAI's language models.

## Features

- **Efficient Retrieval**: Semantic search powered by Weaviate vector database
- **Customizable Responses**: Adjust temperature and top_k parameters
- **Source Attribution**: Tracks document sources for answer verification
- **Production-Ready**: Includes health checks, error handling, and logging
- **Scalable**: Designed with async support for high throughput

## Tech Stack

- **Backend**: FastAPI
- **Vector Database**: Weaviate
- **Embeddings**: OpenAI Embeddings
- **LLM**: GPT-3.5-turbo (OpenAI)
- **Vector Store**: LangChain Weaviate Integration

## Environment Variables

Create a `.env` file with the following variables:

```ini
WEAVIATE_URL=your_weaviate_cluster_url
WEAVIATE_API_KEY=your_weaviate_api_key
OPENAI_API_KEY=your_openai_api_key
