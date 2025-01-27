from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from core.authentication_utils import check_token
from core.db import get_async_session
from core.logger import logger, request_log
from core.models import Building, Activity, activity_hierarchy, Organization
from organizations.elastic_manager import elastic_manager
from routers import main_router


@asynccontextmanager
async def close_es_connection_lifespan(app: FastAPI):
    logger.debug("Приложение запущено и готов к работе.")
    yield
    await elastic_manager.close()


app = FastAPI(title="Bet Maker", lifespan=close_es_connection_lifespan)

origins = ["*"]
app.add_middleware(BaseHTTPMiddleware, dispatch=request_log)

app.include_router(main_router)


@app.get("/", dependencies=[Depends(check_token)])
async def root() -> JSONResponse:
    logger.warning("Авторизованная попытка подключения к базовому URL!")
    return JSONResponse(content={"detail": "This route is disabled"}, status_code=403)


@app.post("/load-initial-data", dependencies=[Depends(check_token)])
async def load_initial_data(
    session: AsyncSession = Depends(get_async_session),
):
    db_obj = await session.execute(select(Building))
    db_obj = db_obj.scalars().first()
    if db_obj:
        logger.debug("Попытка загрузки данных во второй раз!")
        return {"message": "Данные уже загружены в БД."}
    buildings = [
        Building(
            address="Address 1",
            latitude=55.6575,
            longitude=37.5733,
            geo_point=f"SRID=4326;POINT({37.5733} {55.6575})",
        ),
        Building(
            address="Address 2",
            latitude=55.6601,
            longitude=37.5761,
            geo_point=f"SRID=4326;POINT({37.5761} {55.6601})",
        ),
        Building(
            address="Address 3",
            latitude=55.6579,
            longitude=37.5878,
            geo_point=f"SRID=4326;POINT({37.5878} {55.6579})",
        ),
        Building(
            address="Address 4",
            latitude=55.6534,
            longitude=37.5932,
            geo_point=f"SRID=4326;POINT({37.5932} {55.6534})",
        ),
    ]
    session.add_all(buildings)
    logger.debug("Первичные здания добавлены в сессию.")
    await session.flush()

    activity1 = Activity(name="Еда", level=1)
    activity2 = Activity(name="Мясная продукция", level=2)
    activity3 = Activity(name="Мясная Колбасы", level=3)
    activity4 = Activity(name="Автомобили", level=1)
    activity5 = Activity(name="Грузовые", level=2)
    activity6 = Activity(name="Аксессуары", level=3)
    session.add_all([activity1, activity2, activity3, activity4, activity5, activity6])
    logger.debug("Виды деятельности добавлены в сессию.")
    await session.flush()

    await session.execute(
        activity_hierarchy.insert().values(
            [
                {"parent_id": activity1.id, "child_id": activity2.id},
                {"parent_id": activity2.id, "child_id": activity3.id},
                {"parent_id": activity4.id, "child_id": activity5.id},
                {"parent_id": activity5.id, "child_id": activity6.id},
            ]
        )
    )
    logger.debug("Связи между видами деятельности добавлены в сессию.")

    organizations = [
        Organization(
            name="Продуктовая корпорация",
            building_id=buildings[0].id,
            activities=[activity3],
        ),
        Organization(
            name="Птицефабрика", building_id=buildings[1].id, activities=[activity2]
        ),
        Organization(
            name="Колбасное производство",
            building_id=buildings[2].id,
            activities=[activity1],
        ),
        Organization(
            name="Автомобильная компания",
            building_id=buildings[3].id,
            activities=[activity4],
        ),
        Organization(
            name="Грузовые автомобили",
            building_id=buildings[0].id,
            activities=[activity5],
        ),
        Organization(
            name="ОАО Аксессуары",
            building_id=buildings[1].id,
            activities=[activity6, activity3],
        ),
    ]
    session.add_all(organizations)
    logger.debug("Организации добавлены в сессию.")
    await session.flush()

    await elastic_manager.load_organizations_to_es(organizations=organizations)
    await session.commit()
    logger.debug("Первичные данные успешно загружены в БД.")

    return {"message": "Данные загружены успешно."}
