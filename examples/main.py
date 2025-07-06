from pathlib import Path

from ymlmaster.main import SettingsLoader

from settings_model_pydantic import Settings as SettingsModelPydantic
from settings_model_dataclass import Settings as SettingsModelDataClass


def main() -> None:
    # aliases map for faster implementation (or library testing) in the existing configuration
    ALIASES_MAP = {
        'PGUSER': 'POSTGRESQL__USER',
        'PGPASSWORD': 'POSTGRESQL__PASSWORD',
        'PGPORT': 'POSTGRESQL__PORT',
        'PGDB': 'POSTGRESQL__DB',
    }

    # Pydantic Model
    loader_pydantic = SettingsLoader(
        settings_path=Path("settings.yml"),
        env_path=Path(".env"),
        model_class=SettingsModelPydantic,
        # default:
        # use_release=False,
        # profile=None
        url_templates={
            "postgresql": "postgresql+asyncpg",
            "redis": "redis",
            "nats": "nats"
        },
        env_alias_map=ALIASES_MAP
    )
    settings_pydantic: SettingsModelPydantic = loader_pydantic.load()

    print("Results model pydantic:")
    print(settings_pydantic.application.admin_id)
    print(settings_pydantic.redis.port)
    print(settings_pydantic.postgresql.host)
    print(settings_pydantic.redis_url)
    print(settings_pydantic.postgresql_url)

    # Dataclass
    loader_dataclass = SettingsLoader(
        settings_path=Path("settings.yml"),
        env_path=Path(".env"),
        model_class=SettingsModelDataClass,
        # default:
        # use_release=False,
        # profile=None,
        # url_templates=None,
        # env_alias_map=ALIASES_MAP
    )
    settings_dataclass: SettingsModelDataClass = loader_dataclass.load()

    print("\nResults model dataclass:")
    print(settings_dataclass.application.admin_id)
    print(settings_dataclass.redis.port)
    print(settings_dataclass.postgresql.host)
    print(settings_dataclass.redis_url)  # None -> not schema url_templates=None
    print(settings_dataclass.postgresql_url)  # None -> not schema url_templates=None


if __name__ == "__main__":
    main()
