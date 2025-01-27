from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDBase:

    def __init__(self, model):
        self.model = model

    async def get(
        self,
        obj_id: int,
        session: AsyncSession,
    ):
        db_obj = await session.execute(
            select(self.model).where(self.model.id == obj_id)
        )
        return db_obj.scalars().first()

    async def get_multi(self, session: AsyncSession):
        db_objs = await session.execute(select(self.model))
        return db_objs.scalars().all()

    async def handle_integrity_error(self, e: IntegrityError):
        """Обрабатывает ошибки IntegrityError при работе с базой данных."""
        error_message = str(e.orig)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{error_message}",
        )

    async def create(self, create_data, session: AsyncSession):
        create_data = create_data.model_dump()
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
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True)

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

    @staticmethod
    async def remove(
        db_obj,
        session: AsyncSession,
    ):
        await session.delete(db_obj)
        await session.commit()
        return db_obj
