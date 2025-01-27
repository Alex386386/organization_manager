import asyncio
import os

from dotenv import load_dotenv, find_dotenv
from elasticsearch import AsyncElasticsearch

load_dotenv(find_dotenv())

async def create_index():
    es = AsyncElasticsearch(os.getenv("ES_ADDRESS", "http://elasticsearch:9200"))
    index_name = "organizations"

    index_exists = await es.indices.exists(index=index_name)
    if index_exists:
        print(f"Index '{index_name}' already exists.")
    else:
        response = await es.indices.create(
            index=index_name,
            body={
                "mappings": {
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "text"}
                    }
                }
            }
        )
        print(f"Index '{index_name}' created. Response: {response}")

    await es.close()

if __name__ == "__main__":
    asyncio.run(create_index())
