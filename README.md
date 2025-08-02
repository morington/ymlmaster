# ymlmaster

**ymlmaster** is a configuration loading utility for Python 3.12+. It provides a unified interface for loading deeply structured YAML configuration files (optionally combined with `.env` overrides) into statically typed Python classes using either `dataclass` or `pydantic`.

---

## Features

- Schema generation from YAML into `@dataclass` or `Pydantic` models
- Nested structures supported automatically
- Preserves docstrings, base class inheritance, and field customizations during regeneration
- `.env` merging with environment variable fallback (and alias remapping support)
- URL field generation (`*_url`) based on structured service info (`host`, `port`, etc.)
- Smart handling of comma-separated env vars to generate multiple URLs
- Profile support (e.g., `dev`, `release`)
- CLI generator for schema models

---

## Installation

```bash
pip install ymlmaster
# or
poetry add ymlmaster
```

---

## Schema Example

Example YAML:

```yaml
dev:
  postgresql:
    host: null
    user: null
    password: null
    port: null
    db: null

  redis:
    host: "127.0.0.1"
    port: null

  application:
    token: null
    admin_id: null
```

Example .env:

```env
POSTGRESQL__USER=user_pg
POSTGRESQL__PASSWORD=password_pg
POSTGRESQL__PORT=5432,2345
POSTGRESQL__HOST=localhost,198.168.0.101
APPLICATION__TOKEN=123456:geJhasfjJD2f
APPLICATION__ADMIN_ID=12345
```

---

## Model Generation CLI

```bash
poetry run generate-schema \
  --settings settings.yml \
  --output settings_model.py \
  --type dataclass \
  --profile dev \
  --urls postgresql redis
```

This will generate (preserving comments, docstrings, fields, and base classes):

```python
@dataclass
class Postgresql:
    host: Optional[str] = None
    user: Optional[str] = None
    ...

@dataclass
class Settings:
    postgresql: Postgresql = None
    postgresql_url: Optional[str | list[str]] = None
    redis_url: Optional[str | list[str]] = None
```

Same works with:

```python
class Postgresql(BaseModel): ...
class Settings(BaseModel): ...
```

---

## How It Works

Block-based configuration:

- YAML supports separate config blocks like `dev`, `release`, `stage`, etc.
- `--profile dev` chooses which one to load
- Default is `dev`

You can automate environment selection via:

```python
use_release = not Path(".developer").exists()
loader = SettingsLoader(..., use_release=use_release)
```

This assumes:
- `.developer` exists on local machines (and ignored via `.gitignore`)
- When not found → production (auto picks `release`)

---

## SettingsLoader Parameters

| Parameter        | Type               | Description                                                                 |
|------------------|--------------------|-----------------------------------------------------------------------------|
| settings_path    | Path               | Path to the YAML schema (e.g. settings.yml)                                |
| env_path         | Path               | Path to .env file (merged with os.environ)                                 |
| model_class      | type               | Pydantic or dataclass class to load into                                   |
| use_release      | bool               | If True and profile not set, auto-uses `release_block`                     |
| profile          | str                | Explicit profile block in YAML to use (e.g. dev, production, staging)      |
| url_templates    | dict[str, str]     | Dict of { section: scheme } to build *_url fields                          |
| env_alias_map    | dict[str, str]     | Flat → nested env key remapping (e.g. PGUSER → POSTGRESQL__USER)           |
| dev_block        | str                | Custom name for development profile (default: `"dev"`)                     |
| release_block    | str                | Custom name for release profile (default: `"release"`)                     |

---

## Smart URL Generation

With `.env` like:

```env
POSTGRESQL__HOST=localhost,10.0.0.2
POSTGRESQL__USER=user1,user2
POSTGRESQL__PORT=5432,5433
```

and:

```python
url_templates = {
  "postgresql": "postgresql+asyncpg"
}
```

`Settings.postgresql_url` becomes:

```python
[
  "postgresql+asyncpg://user1:...@localhost:5432/dbname",
  "postgresql+asyncpg://user2:...@10.0.0.2:5433/dbname"
]
```

You can mix single and multiple values — host count defines length of list.

---

## Example Usage

```python
from ymlmaster import SettingsLoader
from settings_model_pydantic import Settings

ALIASES_MAP = {
    "PGUSER": "POSTGRESQL__USER",
    "PGPASSWORD": "POSTGRESQL__PASSWORD",
    "PGPORT": "POSTGRESQL__PORT",
    "PGDB": "POSTGRESQL__DB",
}

loader = SettingsLoader(
    settings_path=Path("settings.yml"),
    env_path=Path(".env"),
    model_class=Settings,
    use_release=False,
    profile=None,
    url_templates={
        "postgresql": "postgresql+asyncpg",
        "redis": "redis"
    },
    env_alias_map=ALIASES_MAP,
    dev_block="dev",             # you can change to "development"
    release_block="release",     # you can change to "production"
)

cfg = loader.load()
print(cfg.redis_url)
print(cfg.postgresql_url)
```

---

## Docker Compatibility

- Values from `.env` are injected **only if the YAML value is `null`**
- Nested overrides use `__` as separator:
  - For `application.token` → `APPLICATION__TOKEN`
  - For `redis.port` → `REDIS__PORT`

If the key ends with `port` and is an integer, a default IP of `127.0.0.1:` is prepended unless already present.

This separation helps to use sensitive data in Dockerfile/DockerCompose and in your project at once
Example `docker-compose.yml`:

```yml
services:
  q3s2j0pj0fuj:
    image: "postgres:17"
    container_name: "q3s2j0pj0fuj"
    environment:
      POSTGRES_DB: ${POSTGRESQL__DB}
      POSTGRES_USER: ${POSTGRESQL__USER}
      POSTGRES_PASSWORD: ${POSTGRESQL__PASSWORD}
    ports:
      - "${POSTGRESQL__PORT}:5432"
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    networks:
      - Network
    restart: always
```

### [MIT LICENSE](LICENSE)