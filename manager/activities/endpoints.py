from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from activities.crud import activity_crud
from activities.schemas import ActivityCreate, ActivityUpdate
from core.authentication_utils import check_token
from core.db import get_async_session
from core.utils import Tags, check_exists_and_get_or_return_error

router = APIRouter(
    prefix="/activities",
    tags=[Tags.activities],
    dependencies=[Depends(check_token)],
)


@router.get("/get-one/{activity_id}")
async def get_activity_by_id_for_admin(
        activity_id: int = Path(...), session: AsyncSession = Depends(get_async_session)
):
    return await check_exists_and_get_or_return_error(
        db_id=activity_id,
        crud=activity_crud,
        method_name="get",
        error="Такого вида деятельности нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )


@router.get("/get-all")
async def get_all_activities(
        session: AsyncSession = Depends(get_async_session),
):
    try:
        return await activity_crud.get_activity_tree_with_children(session=session)
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=500,
        )


@router.post("/create")
async def create_new_activity(
        activity_data: ActivityCreate,
        session: AsyncSession = Depends(get_async_session)
):
    return await activity_crud.create(activity_data, session)


@router.patch("/update-activity/{activity_id}")
async def update_activity(
        activity_data: ActivityUpdate,
        activity_id: int = Path(...),
        session: AsyncSession = Depends(get_async_session),
):
    activity = await check_exists_and_get_or_return_error(
        db_id=activity_id,
        crud=activity_crud,
        method_name="get",
        error="Такого вида деятельности нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    return await activity_crud.update(
        db_obj=activity, obj_in=activity_data, session=session
    )


@router.delete("/delete-activity-by-id/{activity_id}")
async def delete_activity_by_id(
        activity_id: int = Path(...),
        session: AsyncSession = Depends(get_async_session),
):
    activity = await check_exists_and_get_or_return_error(
        db_id=activity_id,
        crud=activity_crud,
        method_name="get",
        error="Такого вида деятельности нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    try:
        await activity_crud.remove(db_obj=activity, session=session)
        return "Объект успешно удалён из БД"
    except Exception as e:
        raise HTTPException(
            detail=f"Ошибка во время удаления: {e}",
            status_code=400,
        )
