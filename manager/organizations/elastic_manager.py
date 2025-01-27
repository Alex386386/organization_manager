from elasticsearch import AsyncElasticsearch

from core.config import settings
from core.logger import logger
from core.models import Organization


class ElasticManager:
    def __init__(self, es_host: str):
        self.es = AsyncElasticsearch(es_host)

    async def close(self):
        await self.es.close()
        logger.debug("Соединение с Elastic Search разорвано.")

    async def load_organizations_to_es(self, organizations: list[Organization]):
        for org in organizations:
            await self.add_organization_to_es(org_id=org.id, org_name=org.name)
            await self.es.index(
                index="organizations",
                id=org.id,
                document={
                    "id": org.id,
                    "name": org.name,
                },
            )
        logger.debug("Все переданные организации переданы в индекс Elastic Search.")

    async def add_organization_to_es(
        self, org_id: int, org_name: str,
    ):
        response = await self.es.index(
            index="organizations",
            id=org_id,
            document={"id": org_id, "name": org_name},
        )
        logger.debug(f"Добавлена организация {org_name} в индекс.")
        return response

    async def update_organization_in_es(self, org_id: int, org_name: str):
        await self.es.update(
            index="organizations",
            id=org_id,
            body={"doc": {"name": org_name}},
        )
        logger.debug(f"Организация {org_name} обновлена в индексе Elastic Search.")

    async def delete_organization_from_es(self, org_id: int):
        await self.es.delete(index="organizations", id=org_id)
        logger.debug(f"Организация с id {org_id} удалена из индекса Elastic Search.")

    async def search_organizations_by_name(self, name: str, size: int = 10):
        response = await self.es.search(
            index="organizations",
            body={"query": {"match": {"name": name}}, "size": size},
        )
        return [hit["_source"] for hit in response["hits"]["hits"]]


elastic_manager = ElasticManager(settings.es_address)
