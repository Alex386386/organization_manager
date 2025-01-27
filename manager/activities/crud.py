from fastapi import status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.crud_foundation import CRUDBase
from core.logger import logger
from core.models import Activity, activity_hierarchy
from core.utils import log_and_raise_error


class ActivityCRUD(CRUDBase):

    async def get_activity_tree_with_children(self, session: AsyncSession, max_level: int = 3):
        """Получение дерева видов деятельности начиная от объектов с level==1."""
        result = await session.execute(
            select(Activity.id, Activity.name, Activity.level)
            .filter(Activity.level == 1)
        )
        root_activity_ids = [row[0] for row in result.fetchall()]

        if not root_activity_ids:
            return []

        cte = select(activity_hierarchy.c.child_id).filter(
            activity_hierarchy.c.parent_id.in_(root_activity_ids)
        ).cte(name="activity_tree", recursive=True)

        recursive_cte = cte.union_all(
            select(activity_hierarchy.c.child_id)
            .join(cte, activity_hierarchy.c.parent_id == cte.c.child_id)
        )

        result = await session.execute(
            select(Activity)
            .join(recursive_cte, Activity.id == recursive_cte.c.child_id)
            .filter(Activity.level <= max_level)  # Ограничиваем уровни
        )
        activities = result.scalars().all()

        result_level_1 = await session.execute(
            select(Activity).filter(Activity.level == 1)
        )
        level_1_activities = result_level_1.scalars().all()
        activities.extend(level_1_activities)

        result_hierarchy = await session.execute(
            select(activity_hierarchy.c.parent_id, activity_hierarchy.c.child_id)
        )
        hierarchy_data = result_hierarchy.fetchall()

        def build_tree(activity, all_activities, hierarchy_data):
            tree_item = {
                "id": activity.id,
                "name": activity.name,
                "level": activity.level,
            }
            children = [
                child for child in all_activities
                if (activity.id, child.id) in hierarchy_data
            ]
            if children:
                tree_item["children"] = [build_tree(child, all_activities, hierarchy_data) for child in children]
            return tree_item

        tree = [build_tree(activity, activities, hierarchy_data) for activity in activities if activity.id in root_activity_ids]
        return tree

    async def create(self, create_data, session: AsyncSession):
        """Создание вида деятельности."""
        create_data = create_data.model_dump()
        parent_id = create_data.pop("parent_id", None)
        if parent_id:
            parent = await self.get(parent_id, session)
            if not parent:
                log_and_raise_error(
                    message_log="Нет такого",
                    message_error="Нет такого",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            if parent.level == 3:
                log_and_raise_error(
                    message_log="Достигнут предел глубины дерева видов деятельности",
                    message_error="Попытка привязать новый вид деятельности к объекту с максимальной глубинной вложенности",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            elif parent.level < 3:
                create_data["level"] = parent.level + 1
        new_obj = self.model(**create_data)
        try:
            session.add(new_obj)
            if parent_id:
                await session.flush()
                await session.execute(
                    activity_hierarchy.insert().values(
                        parent_id=parent_id,
                        child_id=new_obj.id
                    )
                )
                logger.debug("В сессии зарегистрирована связь с родительским элементом.")
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
        """Обновление вида деятельности, а в случае изменения родителя обновление и связной модели в activity_hierarchy."""
        obj_data = jsonable_encoder(db_obj)
        update_data = obj_in.model_dump(exclude_unset=True)

        parent_id = update_data.pop("parent_id", None)
        db_obj_level = obj_data.get("level")
        if parent_id:
            if db_obj_level == 1:
                log_and_raise_error(
                    message_log="Нельзя назначить родителя для корневого вида деятельности.",
                    message_error=f"Попытка назначить родителя для корневого вида деятельности с id {db_obj.id}",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            parent = await self.get(parent_id, session)
            if not parent:
                log_and_raise_error(
                    message_log="Нет такого",
                    message_error="Нет такого",
                    status_code=status.HTTP_403_FORBIDDEN
                )
            if parent.level != db_obj_level - 1:
                log_and_raise_error(
                    message_log="Уровень родителя не позволяет переназначить текущий вид деятельности к нему.",
                    message_error="Попытка привязать вид деятельности к объекту с некорректной глубинной вложенности",
                    status_code=status.HTTP_403_FORBIDDEN
                )

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        try:
            session.add(db_obj)
            if parent_id:
                await session.execute(
                    activity_hierarchy.update()
                    .where(activity_hierarchy.c.child_id == db_obj.id)
                    .values(parent_id=parent_id)
                )
                logger.debug("В сессии изменена связь с родительским элементом.")
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
        """Удаление вида деятельности, поведение меняется в зависимости от вложенности."""
        if db_obj.level == 3:
            await session.delete(db_obj)
            await session.commit()
            logger.debug(f"Объект с id {db_obj.id} удалён из системы.")
            return db_obj
        if db_obj.level in [1, 2]:
            result = await session.execute(
                select(activity_hierarchy.c.child_id)
                .where(activity_hierarchy.c.parent_id == db_obj.id)
            )
            children = result.scalars().all()

            if children:
                logger.debug(f"Для объекта с id {db_obj.id} получен список дочерних элементов.")
                raise ValueError(f"Нельзя удалить объект уровня {db_obj.level}, так как у него есть дочерние элементы.")

            await session.execute(
                activity_hierarchy.delete().where(
                    activity_hierarchy.c.child_id == db_obj.id
                )
            )
            await session.delete(db_obj)
            await session.commit()
            return db_obj

activity_crud = ActivityCRUD(Activity)
