import re

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from activities.crud import activity_crud
from core.utils import check_exists_and_get_or_return_error


async def check_first_level_activity(activity_id: int, session: AsyncSession):
    activity = await check_exists_and_get_or_return_error(
        db_id=activity_id,
        crud=activity_crud,
        method_name="get",
        error="Такого вида деятельности нет в БД!",
        status_code=status.HTTP_404_NOT_FOUND,
        session=session,
    )
    if activity.level != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Для данного эндпоинта можно использовать только виды деятельности первой ступени вложенности.",
        )

def check_phones(phones: list[str]) -> list[str]:
    unique_phones = list(set(phones))

    phone_pattern = re.compile(r"^\d{7}$|^8\d{10}$")
    for phone in unique_phones:
        if not phone_pattern.match(phone):
            raise ValueError(
                f"Неверный формат номера телефона: {phone}. "
                f"Телефон должен состоять из 7 или 11 знаков, и во втором случае начинаться с 8"
            )
    return unique_phones
