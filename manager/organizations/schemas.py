from datetime import datetime
from decimal import Decimal
from typing import Optional

from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, field_validator

from activities.schemas import ActivityDB
from organizations.validators import check_phones


class OrganizationBase(BaseModel):
    name: str
    phones: Optional[list[str]] = None
    building_id: Optional[int] = None


class OrganizationUpdate(OrganizationBase):
    name: Optional[str] = None

    @field_validator("phones", mode="before")
    def validate_phones(cls, phones: Optional[list[str]]) -> Optional[list[str]]:
        if phones is None:
            return phones
        return check_phones(phones)


class OrganizationCreate(OrganizationBase):
    pass

    @field_validator("phones", mode="before")
    def validate_phones(cls, phones: Optional[list[str]]) -> Optional[list[str]]:
        if phones is None:
            return phones
        return check_phones(phones)


class NonCircularBuildingDB(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    address: str
    latitude: Decimal
    longitude: Decimal
    geo_point: str
    create_date: datetime
    update_date: datetime

    @field_validator("geo_point", mode="before")
    def validate_geo_point(cls, geo_point: WKBElement) -> str:
        shaped_wkb_element = to_shape(geo_point)
        return shaped_wkb_element.wkt


# class ActivityDB(BaseModel):
#     model_config = ConfigDict(from_attributes=True)
#     id: int
#     name: str
#     level: int
#     create_date: datetime
#     update_date: datetime


class OrganizationDB(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    building: Optional[NonCircularBuildingDB] = None
    activities: Optional[list[ActivityDB]] = None
    create_date: datetime
    update_date: datetime


class OrganizationShortDB(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    create_date: datetime
    update_date: datetime
