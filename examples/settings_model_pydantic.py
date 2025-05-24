from typing import Optional
from pydantic import BaseModel


"""
poetry run generate-schema --settings .\settings.yml --output settings_model_pydantic.py --type pydantic --profile dev --url-fields postgresql redis
"""


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
    token: Optional[str] = None
    admin_id: Optional[str] = None


class Settings(BaseModel):
    postgresql: Postgresql = None
    redis: Redis = None
    application: Application = None
    postgresql_url: Optional[str] = None
    redis_url: Optional[str] = None