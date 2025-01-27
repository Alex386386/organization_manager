from decimal import Decimal

from fastapi.encoders import jsonable_encoder
from geoalchemy2.functions import ST_DWithin
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.config import settings
from core.crud_foundation import CRUDBase
from core.logger import logger
from core.models import Building


class BuildingCRUD(CRUDBase):

    async def get_with_organizations(
        self,
        obj_id: int,
        session: AsyncSession,
    ):
        """Получение зданий с вложенными внутрь объектами организаций."""
        db_obj = await session.execute(
            select(self.model)
            .where(self.model.id == obj_id)
            .options(
                joinedload(self.model.organizations)
            )
        )
        return db_obj.scalars().first()

    async def get_buildings_in_radius(
            self,
            latitude: Decimal,
            longitude: Decimal,
            radius_km: int,
            session: AsyncSession
    ):
        """Получение списка зданий находящихся в радиусе от переданной в запросе точки."""
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), settings.wsg_standard)
        logger.debug("Точка отсчёта подготовлена для запроса.")
        radius_meters = radius_km * settings.meter_coefficient

        result = await session.execute(
            select(self.model)
            .where(ST_DWithin(self.model.geo_point, point, radius_meters))
            .options(joinedload(self.model.organizations)))
        return result.unique().scalars().all()

    async def create(self, create_data, session: AsyncSession):
        """Создание здания."""
        create_data = create_data.model_dump()
        create_data["geo_point"] = f"SRID=4326;POINT({create_data['longitude']} {create_data['latitude']})"
        logger.debug("Географическая позиция добавлена в итоговый словарь данных.")
        new_obj = self.model(**create_data)
        try:
            session.add(new_obj)
            await session.commit()
            await session.refresh(new_obj)
            return new_obj
        except IntegrityError as e:
            await session.rollback()
            await self.handle_integrity_error(e)

    async def update(
        self,
        db_obj,
        obj_in,
        session: AsyncSession,
    ):
        """Обновление здания."""
        obj_data = jsonable_encoder(db_obj, exclude={"geo_point"})
        update_data = obj_in.model_dump(exclude_unset=True)

        longitude = update_data.get("longitude")
        latitude = update_data.get("latitude")

        if longitude is not None or latitude is not None:
            longitude = longitude if longitude is not None else db_obj.longitude
            latitude = latitude if latitude is not None else db_obj.latitude
            obj_data["geo_point"] = ""
            update_data["geo_point"] = f"SRID=4326;POINT({longitude} {latitude})"
            logger.debug("Географическая позиция добавлена в итоговый словарь данных.")

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        try:
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await session.rollback()
            await self.handle_integrity_error(e)

building_crud = BuildingCRUD(Building)
