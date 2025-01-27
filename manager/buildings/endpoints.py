from decimal import Decimal

from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from buildings.crud import building_crud
from buildings.schemas import BuildingCreate, BuildingUpdate, BuildingDB, BuildingShortDB
from core.authentication_utils import check_token
from core.db import get_async_session
from core.utils import Tags, check_exists_and_get_or_return_error

router = APIRouter(
    prefix="/buildings",
    tags=[Tags.buildings],
    dependencies=[Depends(check_token)],
)


@router.get(
    "/get-one/{building_id}",
    response_model=BuildingDB
)
async def get_building_by_id(
        building_id: int = Path(...), session: AsyncSession = Depends(get_async_session)
):
    return await check_exists_and_get_or_return_error(
        db_id=building_id,
        crud=building_crud,
        method_name="get_with_organizations",
        error="Такого строения нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )


@router.get(
    "/get-all",
    response_model=list[BuildingShortDB]
)
async def get_all_buildings(
        session: AsyncSession = Depends(get_async_session),
):
    try:
        return await building_crud.get_multi(session=session)
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=500,
        )


@router.get(
    "/get-in_radius",
    response_model=list[BuildingDB]
)
async def get_all_buildings_in_radius(
        radius_km: int = Query(1, ge=0),
        latitude: Decimal = Query(..., ge=-90, le=90),
        longitude: Decimal = Query(..., ge=-180, le=180),
        session: AsyncSession = Depends(get_async_session),
):
    try:
        return await building_crud.get_buildings_in_radius(
            radius_km=radius_km,
            latitude=latitude,
            longitude=longitude,
            session=session
        )
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=500,
        )


@router.post(
    "/create",
    response_model=BuildingShortDB
)
async def create_building(
        building_data: BuildingCreate, session: AsyncSession = Depends(get_async_session)
):
    return await building_crud.create(building_data, session)


@router.patch(
    "/update-building/{building_id}",
    response_model=BuildingShortDB
)
async def update_building(
        building_data: BuildingUpdate,
        building_id: int = Path(...),
        session: AsyncSession = Depends(get_async_session),
):
    building = await check_exists_and_get_or_return_error(
        db_id=building_id,
        crud=building_crud,
        method_name="get",
        error="Такого строения нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    return await building_crud.update(
        db_obj=building, obj_in=building_data, session=session
    )


@router.delete("/delete-building-by-id/{building_id}")
async def delete_building_by_id(
        building_id: int = Path(...),
        session: AsyncSession = Depends(get_async_session),
):
    building = await check_exists_and_get_or_return_error(
        db_id=building_id,
        crud=building_crud,
        method_name="get",
        error="Такого строения нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    try:
        await building_crud.remove(db_obj=building, session=session)
        return "Объект успешно удалён из БД"
    except Exception as e:
        raise HTTPException(
            detail=f"Ошибка во время удаления: {e}",
            status_code=400,
        )
