from typing import Optional
from dataclasses import dataclass

"""
poetry run generate-schema --settings .\settings.yml --output settings_model_dataclass.py --profile dev --url-fields postgresql redis
"""

@dataclass
class Postgresql:
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    port: Optional[str] = None
    db: Optional[str] = None

@dataclass
class Redis:
    host: Optional[str] = None
    port: Optional[str] = None

@dataclass
class Application:
    token: Optional[str] = None
    admin_id: Optional[str] = None

@dataclass
class Settings:
    postgresql: Postgresql = None
    redis: Redis = None
    application: Application = None
    postgresql_url: Optional[str] = None
    redis_url: Optional[str] = None