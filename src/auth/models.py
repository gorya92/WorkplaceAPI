from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.params import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTable
from datetime import datetime
from sqlalchemy import Table, Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Boolean, MetaData, LargeBinary, \
    DateTime
from sqlalchemy.orm import relationship
from src.database import Base
from pydantic import BaseModel, Field

metadata = MetaData()

role = Table(
    "role",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("permissions", JSON),
)

user = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("email", String, nullable=False),
    Column("username", String, nullable=False),
    Column("registered_at", TIMESTAMP, default=datetime.utcnow),
    Column("role_id", Integer, ForeignKey(role.c.id)),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True, nullable=False),
    Column("is_superuser", Boolean, default=False, nullable=False),
    Column("is_verified", Boolean, default=False, nullable=False),
    Column("device_token", String, default="", nullable=True),
)

workplace = Table(
    "workplace",
    metadata,

    Column("id", Integer, primary_key=True),
    Column("title", String, nullable=False),
    Column("max_people", Integer, nullable=False),
    Column("current_people", Integer, nullable=True),
    Column("camera_url", String, nullable=False),
    Column("green_zone_coordinates", JSON, nullable=True),
    Column("red_zone_coordinates", JSON, nullable=True),
    Column("alert_period", Integer, nullable=True),
    Column("face_detection", Boolean,default=False, nullable=True),
    Column("last_notification_sent_at", DateTime, nullable=True)
)

user_workplace = Table(
    "user_workplace",
    metadata,
    Column("user_id", Integer, ForeignKey(user.c.id), primary_key=True),
    Column("workplace_id", Integer, ForeignKey(workplace.c.id), primary_key=True)
)

worker = Table(
    "worker",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String, nullable=False),
    Column("image_url", String, nullable=True),
    Column("workplace_id", Integer, ForeignKey("workplace.id")),
)


class WorkerSchema(BaseModel):
    id: int
    name: str
    workplace_id: int

    class Config:
        orm_mode = True


class Role(Base):
    __tablename__ = "role"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    permissions = Column(JSON)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    email = Column(String, nullable=False)
    username = Column(String, nullable=False)
    registered_at = Column(TIMESTAMP, default=datetime.utcnow)
    role_id = Column(Integer, ForeignKey("role.id"))
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    device_token = Column(String, default="", nullable=True)

    workplaces = relationship(
        "Workplace",
        secondary="user_workplace",
        back_populates="users"
    )


class Workplace(Base):
    __tablename__ = "workplace"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    max_people = Column(Integer, nullable=False)
    current_people = Column(Integer, nullable=True)
    camera_url = Column(String, nullable=False)
    green_zone_coordinates = Column(JSON, nullable=True)
    red_zone_coordinates = Column(JSON, nullable=True)
    alert_period = Column(Integer, nullable=True)
    face_detection = Column(Boolean, default=False, nullable=True)
    last_notification_sent_at = Column(DateTime, nullable=True)
    users = relationship(
        "User",
        secondary="user_workplace",
        back_populates="workplaces"
    )


class UserWorkplace(Base):
    __tablename__ = "user_workplace"
    user_id = Column(Integer, ForeignKey("user.id"), primary_key=True)
    workplace_id = Column(Integer, ForeignKey("workplace.id"), primary_key=True)


class Worker(Base):
    __tablename__ = "worker"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    image_url = Column(String, nullable=True)
    workplace_id = Column(Integer, ForeignKey("workplace.id"))

class WorkplaceCreate(BaseModel):
    max_people: int
    camera_url: str
    green_zone_coordinates: Optional[list] = None
    red_zone_coordinates: Optional[list] = None

    class Config:
        orm_mode = True
