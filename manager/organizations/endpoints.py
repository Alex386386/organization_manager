from fastapi import APIRouter, HTTPException, status
from fastapi.params import Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from activities.crud import activity_crud
from core.authentication_utils import check_token
from core.db import get_async_session
from core.utils import Tags, check_exists_and_get_or_return_error
from organizations.crud import organization_crud
from organizations.elastic_manager import elastic_manager
from organizations.schemas import OrganizationCreate, OrganizationUpdate, OrganizationDB, OrganizationShortDB
from organizations.validators import check_first_level_activity

router = APIRouter(
    prefix="/organizations",
    tags=[Tags.organizations],
    dependencies=[Depends(check_token)],
)


@router.get(
    "/get-one/{organization_id}",
    response_model=OrganizationDB
)
async def get_organization_by_id(
        organization_id: int = Path(...), session: AsyncSession = Depends(get_async_session)
):
    return await check_exists_and_get_or_return_error(
        db_id=organization_id,
        crud=organization_crud,
        method_name="get_with_activities_and_building",
        error="Такой организации нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )


@router.get(
    "/get-by-building-id/{building_id}",
    response_model=list[OrganizationShortDB]
)
async def get_organizations_by_building_id(
        building_id: int = Path(...), session: AsyncSession = Depends(get_async_session)
):
    return await organization_crud.get_by_building_id(building_id=building_id, session=session)


@router.get(
    "/get-by-activity-id/{activity_id}",
    response_model=list[OrganizationShortDB]
)
async def get_organizations_by_activity_id(
        activity_id: int = Path(...), session: AsyncSession = Depends(get_async_session)
):
    return await organization_crud.get_by_activity_id(activity_id=activity_id, session=session)


@router.get(
    "/get-by-first-level-activities/{activity_id}",
    response_model=list[OrganizationShortDB]
)
async def get_organizations_by_first_level_activity(
        activity_id: int = Path(...), session: AsyncSession = Depends(get_async_session)
):
    await check_first_level_activity(activity_id=activity_id, session=session)
    return await organization_crud.get_activity_tree_ids(activity_id=activity_id, session=session)


@router.get(
    "/search_by_name",
    response_model=list[OrganizationShortDB]
)
async def search_organizations(
        name: str, session: AsyncSession = Depends(get_async_session)
):
    try:
        organizations = await elastic_manager.search_organizations_by_name(name)
        ids = [organization["id"] for organization in organizations]
        return await organization_crud.get_by_list_of_ids(ids=ids, session=session)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/get-all",
    response_model=list[OrganizationShortDB]
)
async def get_all_organizations(
        session: AsyncSession = Depends(get_async_session),
):
    try:
        return await organization_crud.get_multi(session=session)
    except Exception as e:
        raise HTTPException(
            detail=f"{e}",
            status_code=500,
        )


@router.post(
    "/create",
    response_model=OrganizationShortDB
)
async def create_new_organization(
        client_data: OrganizationCreate, session: AsyncSession = Depends(get_async_session)
):
    return await organization_crud.create(client_data, session)


@router.post(
    "/add-activity",
    response_model=OrganizationDB
)
async def add_activity(
        organization_id: int, activity_id: int, session: AsyncSession = Depends(get_async_session)
):
    organization = await check_exists_and_get_or_return_error(
        db_id=organization_id,
        crud=organization_crud,
        method_name="get_with_activities_and_building",
        error="Такой организации нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    activity = await check_exists_and_get_or_return_error(
        db_id=activity_id,
        crud=activity_crud,
        method_name="get",
        error="Такого вида деятельности нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    return await organization_crud.add_activity(organization, activity, session)


@router.post(
    "/remove-activity",
    response_model=OrganizationDB
)
async def remove_activity(
        organization_id: int, activity_id: int, session: AsyncSession = Depends(get_async_session)
):
    organization = await check_exists_and_get_or_return_error(
        db_id=organization_id,
        crud=organization_crud,
        method_name="get_with_activities_and_building",
        error="Такой организации нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    activity = await check_exists_and_get_or_return_error(
        db_id=activity_id,
        crud=activity_crud,
        method_name="get",
        error="Такого вида деятельности нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    return await organization_crud.remove_activity(organization, activity, session)


@router.patch(
    "/update-organization/{organization_id}",
    response_model=OrganizationShortDB
)
async def update_organization(
        organization_data: OrganizationUpdate,
        organization_id: int = Path(...),
        session: AsyncSession = Depends(get_async_session),
):
    organization = await check_exists_and_get_or_return_error(
        db_id=organization_id,
        crud=organization_crud,
        method_name="get",
        error="Такой организации нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    return await organization_crud.update(
        db_obj=organization, obj_in=organization_data, session=session
    )


@router.delete("/delete-organization-by-id/{organization_id}")
async def delete_organization_by_id(
        organization_id: int = Path(...),
        session: AsyncSession = Depends(get_async_session),
):
    organization = await check_exists_and_get_or_return_error(
        db_id=organization_id,
        crud=organization_crud,
        method_name="get",
        error="Такой организации нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    try:
        await organization_crud.remove(db_obj=organization, session=session)
        return "Объект успешно удалён из БД"
    except Exception as e:
        raise HTTPException(
            detail=f"Ошибка во время удаления: {e}",
            status_code=400,
        )
