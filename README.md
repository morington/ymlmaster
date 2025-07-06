# ymlmaster

**ymlmaster** is a configuration loading utility for Python 3.11+. It provides a unified interface for loading deeply structured YAML configuration files (optionally combined with `.env` overrides) into statically typed Python classes using either `dataclass` or `pydantic`.

## Features

- Schema generation from YAML into `@dataclass` or `Pydantic` models
- Nested structures supported automatically
- Optional `.env` merging with environment variable fallback
- Profile support (e.g., `dev`, `release`)
- CLI generator for schema models

## Installation

Installation is done in the project using `pip` or `poetry`:

```bash
pip install ymlmaster
```

```bash
poetry add ymlmaster
```

## Model Generation CLI

To generate data models from a YAML configuration file:

```bash
poetry run generate-schema
  --settings settings.yml
  --output settings_model.py
  --type dataclass # or --type pydantic,  default: dataclass
  --profile dev # or custom name block,  default: dev
  --url-fields postgresql redis # added url services
```

This will generate Python code like:

```python
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
```

## Using the Loader

You can then load values from `settings.yml` and `.env` into your model:

```python
from pathlib import Path
from ymlmaster import SettingsLoader
from <settings-model> import Settings

loader = SettingsLoader(
    settings_path=Path("settings.yml"),
    env_path=Path(".env"),
    model_class=Settings,
    use_release=False, # true - release block, false - dev
    profile=None, # specify the exact loading block
    url_templates={
        "postgresql": "postgresql+asyncpg",
        "redis": "redis",
        "nats": "nats"
    }, # url generation instructions   <block name>:<circuit name>
    env_alias_map={"OLD_NAME": "NEW__NAME"}
)

config = loader.load()

print(config.redis.host)
print(config.application.admin_id)
```

### Parameter Description:
- `settings_path` - _(pathlib.Path)_ - Path to the file with the YAML schema of the configuration, in my case `settings.yml`
- `env_path` - _(pathlib.Path)_ - Path to the `.env` file that contains all the data for the configuration
- `model_class` - _(dataclasses.dataclass | pydantic.BaseModel)_ - The generated class from the YAML schema of the configuration
- `use_release` - _(bool)_ - Parameter to automatically define dev/release configuration, more details below*
- `profile` - _(str)_ - Name of the block in the YAML configuration schema which configuration data to take (_example: dev, release, stage, development_) The default is `dev`.
- `url_templates` - _(dict)_ - Dictionary schema for generating URL services (_example: postgresql, redis, nats, celery, rabbitmq, ..._)
- `env_alias_map` - _(dict)_ - Aliases map for faster implementation (or library testing) in the existing configuration
---
\* The `use_release` parameter is used to automatically determine where the project is launched.
I use the following method: on the local machine there is a file `.developer` which is located in `.gitignore`, in `SettingsLoader` I write `use_release=not Path(‘.developer’)`, it means, if the file is not found - it will be `True` and since `profile` is not specified, the block `release` will be automatically pulled up. If the file is found, so we are on a local machine in development mode, it will be `False` and therefore the `dev` configuration will be pulled.
This is handy to use when you have one clear configuration for development and one for your sell.

## Environment Variable Override Behavior

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
