from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.crud_foundation import CRUDBase
from core.logger import logger
from core.models import Organization, Building, Activity, organization_activity, activity_hierarchy
from organizations.elastic_manager import elastic_manager


class OrganizationCRUD(CRUDBase):

    async def get_with_activities_and_building(
        self,
        obj_id: int,
        session: AsyncSession,
    ):
        """Получить организации с видами деятельности и зданием."""
        db_obj = await session.execute(
            select(self.model)
            .where(self.model.id == obj_id)
            .options(
                joinedload(self.model.activities),
                joinedload(self.model.building)
            )
        )
        return db_obj.scalars().first()

    async def get_by_list_of_ids(
        self,
        ids: list[int],
        session: AsyncSession,
    ):
        """Получить список организаций по списку id."""
        db_obj = await session.execute(
            select(self.model)
            .where(self.model.id.in_(ids))
        )
        return db_obj.scalars().all()

    async def get_by_building_id(
        self,
        building_id: int,
        session: AsyncSession,
    ):
        """Получить организации по id строения."""
        db_obj = await session.execute(
            select(Organization)
            .join(Building.organizations)
            .where(Building.id == building_id)
        )
        return db_obj.scalars().all()

    async def get_by_activity_id(
        self,
        activity_id: int,
        session: AsyncSession,
    ):
        """Получить организации по id вида деятельности."""
        db_obj = await session.execute(
            select(Organization)
            .join(Activity.organizations)
            .where(Activity.id == activity_id)
        )
        return db_obj.scalars().all()

    async def get_activity_tree_ids(self, activity_id: int, session: AsyncSession):
        """Получить организации по id вида деятельности первого уровня, то есть во всех вложенных видах деятельности."""
        cte = select(activity_hierarchy.c.child_id).filter(activity_hierarchy.c.parent_id == activity_id).cte(
            name="activity_tree", recursive=True
        )

        recursive_cte = cte.union_all(
            select(activity_hierarchy.c.child_id)
            .join(cte, activity_hierarchy.c.parent_id == cte.c.child_id)
        )

        result = await session.execute(
            select(activity_hierarchy.c.parent_id)
            .filter(activity_hierarchy.c.parent_id == activity_id)
            .union_all(
                select(recursive_cte.c.child_id)
            )
        )
        activity_ids = [row[0] for row in result.fetchall()]

        if not activity_ids:
            activity_ids = [activity_id]

        result = await session.execute(
            select(Organization)
            .join(organization_activity, Organization.id == organization_activity.c.organization_id)
            .filter(organization_activity.c.activity_id.in_(activity_ids))
        )
        organizations = result.unique().scalars().all()

        return organizations

    async def handle_integrity_error(self, e: IntegrityError):
        error_message = str(e.orig)
        if "organizations_building_id_fkey" in str(e.orig):
            raise HTTPException(
                status_code=404,
                detail="Такого здания нет в системе.",
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"{error_message}",
            )

    async def add_activity(
        self, organization, activity, session: AsyncSession
    ):
        """Добавление связи с объектом вида деятельности."""
        if activity in organization.activities:
            raise HTTPException(
                status_code=400,
                detail="Активность уже связана с организацией.",
            )
        logger.info("hfjdkf")
        organization.activities.append(activity)
        try:
            await session.commit()
        except IntegrityError as e:
            await self.handle_integrity_error(e)
        return organization

    async def remove_activity(
        self, organization, activity, session: AsyncSession
    ):
        """Разрыв связи с объектом вида деятельности."""
        if activity not in organization.activities:
            raise HTTPException(
                status_code=400,
                detail="Активность не связана с организацией.",
            )

        organization.activities.remove(activity)
        try:
            await session.commit()
        except IntegrityError as e:
            await self.handle_integrity_error(e)
        return organization

    async def create(self, create_data, session: AsyncSession):
        """Создание объекта организации, а так же добавление в индекс Elastic Search."""
        create_data = create_data.model_dump()
        new_obj = self.model(**create_data)
        try:
            session.add(new_obj)
            await session.commit()
            await session.refresh(new_obj)
            await elastic_manager.add_organization_to_es(org_id=new_obj.id, org_name=new_obj.name)
            logger.debug("Имя добавлено в индекс Elastic Search")
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
        """Обновление объекта организации, а так же обновление имени в Elastic Search при необходимости."""
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True)

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        try:
            session.add(db_obj)
            await session.commit()
            await session.refresh(db_obj)
            if update_data.get("name", None) is not None:
                await elastic_manager.update_organization_in_es(org_id=db_obj.id, org_name=db_obj.name)
                logger.debug("Имя обновлено в индексе Elastic Search")
            return db_obj
        except IntegrityError as e:
            await session.rollback()
            await self.handle_integrity_error(e)

    @staticmethod
    async def remove(
        db_obj,
        session: AsyncSession,
    ):
        """Удаление объекта организации, а так же из индекса Elastic Search."""
        await session.delete(db_obj)
        await session.commit()
        await elastic_manager.delete_organization_from_es(org_id=db_obj.id)
        logger.debug("Имя удалено из Elastic Search")
        return db_obj

organization_crud = OrganizationCRUD(Organization)