from decimal import Decimal
from typing import Optional

from geoalchemy2 import Geography
from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    Table,
    Column,
    Numeric,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

organization_activity = Table(
    "organization_activities",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("organization_id", ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
    Column("activity_id", ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint(
        "organization_id", "activity_id", name="idx_unique_organization_activity"
    ),
)


class Building(Base):
    __tablename__ = 'buildings'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    address: Mapped[str] = mapped_column(
        String(256), comment="Адрес строения", nullable=False
    )
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 6), comment="Долгота строения",
                                              nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(10, 6), comment="Широта строения",
                                               nullable=False)
    geo_point: Mapped[Optional[str]] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        comment="Географическая точка (широта/долгота)"
    )
    organizations = relationship('Organization', back_populates='building')


activity_hierarchy = Table(
    "activity_hierarchy",
    Base.metadata,
    Column("id", Integer, primary_key=True),
    Column("parent_id", ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
    Column("child_id", ForeignKey("activities.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint(
        "parent_id", "child_id", name="idx_unique_parent_child"
    ),
)


class Activity(Base):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(256), comment="Название деятельности", nullable=False
    )
    level: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    children = relationship(
        'Activity',
        secondary=activity_hierarchy,
        primaryjoin=id == activity_hierarchy.c.parent_id,
        secondaryjoin=id == activity_hierarchy.c.child_id,
        backref='parents',
        single_parent=True,
        lazy='subquery',
    )
    organizations = relationship(
        'Organization',
        secondary=organization_activity,
        back_populates='activities',
    )


class Organization(Base):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(
        String(256), comment="Название организации", nullable=False
    )
    phones: Mapped[ARRAY] = mapped_column(ARRAY(String), comment="Список телефонов организации", nullable=True)
    building_id: Mapped[Optional[Integer]] = mapped_column(
        ForeignKey("buildings.id", ondelete="SET NULL"),
        comment="Строение в котором находится организация",
        nullable=True
    )
    building = relationship('Building', back_populates='organizations')
    activities = relationship(
        'Activity',
        secondary=organization_activity,
        back_populates='organizations',
    )
