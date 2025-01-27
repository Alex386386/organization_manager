from datetime import datetime
from decimal import Decimal
from typing import Optional

from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from pydantic import BaseModel, ConfigDict, field_validator, Field

from buildings.validators import fractional_part_validator
from organizations.schemas import OrganizationShortDB


class BuildingBase(BaseModel):
    address: str
    latitude: Decimal
    longitude: Decimal


class BuildingUpdate(BuildingBase):
    address: Optional[str] = None
    latitude: Optional[Decimal] = Field(None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(None, ge=-180, le=180)

    @field_validator("latitude", mode="before")
    def validate_latitude(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            fractional_part_validator(v)
        return v

    @field_validator("longitude", mode="before")
    def validate_longitude(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        if v is not None:
            fractional_part_validator(v)
        return v


class BuildingCreate(BuildingBase):
    latitude: Decimal = Field(..., ge=-90, le=90)
    longitude: Decimal = Field(..., ge=-180, le=180)

    @field_validator("latitude", mode="before")
    def validate_latitude(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        fractional_part_validator(v)
        return v

    @field_validator("longitude", mode="before")
    def validate_longitude(cls, v: Optional[Decimal]) -> Optional[Decimal]:
        fractional_part_validator(v)
        return v


class BuildingDB(BuildingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    geo_point: str
    organizations: Optional[list[OrganizationShortDB]] = None
    create_date: datetime
    update_date: datetime

    @field_validator("geo_point", mode="before")
    def validate_geo_point(cls, geo_point: WKBElement) -> str:
        shaped_wkb_element = to_shape(geo_point)
        return shaped_wkb_element.wkt


class BuildingShortDB(BuildingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    geo_point: str
    create_date: datetime
    update_date: datetime

    @field_validator("geo_point", mode="before")
    def validate_geo_point(cls, geo_point: WKBElement) -> str:
        shaped_wkb_element = to_shape(geo_point)
        return shaped_wkb_element.wkt
