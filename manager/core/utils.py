from enum import Enum
from http import HTTPStatus

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from .crud_foundation import CRUDBase
from .logger import logger


class Tags(Enum):
    buildings = "Buildings"
    activities = "Activities"
    organizations = "Organizations"


def log_and_raise_error(
    message_log: str, message_error: str | dict, status_code: HTTPStatus
) -> None:
    """Логирование ошибки и возврат ошибки обратно в качестве ответа на запрос."""
    logger.error(message_log)
    raise HTTPException(status_code=status_code, detail=message_error)


async def check_exists_and_get_or_return_error(
    db_id: any,
    crud: CRUDBase,
    method_name: str,
    error: str,
    status_code: HTTPStatus,
    session: AsyncSession,
) -> any:
    """
    Стандартная функция получения объекта по id или ключу из БД с вызовом указанного метода,
    а также с возвращением конкретной ошибки и указанного статус кода в случае отсутствия подобного объекта в БД.
    """
    method = getattr(crud, method_name, None)
    if method is None:
        log_and_raise_error(
            f"Метод {method_name} не найден в CRUD",
            f"Метод {method_name} не найден в CRUD",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )

    model_object = await method(db_id, session)
    if model_object is None:
        log_and_raise_error(
            f"Объект с id или name ({db_id}) не найден в БД",
            f"{error}",
            status_code,
        )
    logger.info(f"Объект с id или name ({db_id}) успешно получен из БД")
    return model_object
