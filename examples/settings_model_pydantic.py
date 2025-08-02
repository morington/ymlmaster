from typing import Optional
from pydantic import BaseModel, Field


class Postgresql(BaseModel):
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    port: Optional[str] = None
    db: Optional[str] = None


class Redis(BaseModel):
    host: Optional[str] = None
    port: Optional[str] = None


class Application(BaseModel):
    token: Optional[str] = Field(..., description="token")
    admin_id: Optional[str] = None
    s: Optional[str] = None


class Settings(BaseModel):
    postgresql: Postgresql = None
    redis: Redis = None
    application: Application = Field(..., description="class")
    postgresql_url: Optional[str | list[str]] = None
    redis_url: Optional[str | list[str]] = None