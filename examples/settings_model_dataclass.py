from typing import Optional
from dataclasses import dataclass

@dataclass
class Postgresql:
    host: Optional[str] = None
    user: Optional[int] = None
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
    s: Optional[str] = None

@dataclass
class Settings:
    postgresql: Postgresql = None
    redis: Redis = None
    application: Application = None
    postgresql_url: Optional[str | list[str]] = None
    redis_url: Optional[str | list[str]] = None