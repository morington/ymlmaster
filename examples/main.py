from pathlib import Path
from ymlmaster.main import SettingsLoader

# Сгенерированные модели (одна на pydantic, другая на dataclass)
from settings_model_pydantic import Settings as SettingsModelPydantic
from settings_model_dataclass import Settings as SettingsModelDataClass


def main() -> None:
    # Алиасы для переменных окружения -> YAML ключей
    ALIASES_MAP = {
        'PGUSER': 'POSTGRESQL__USER',
        'PGPASSWORD': 'POSTGRESQL__PASSWORD',
        'PGPORT': 'POSTGRESQL__PORT',
        'PGDB': 'POSTGRESQL__DB',
    }

    # === Пример использования с Pydantic ===
    loader_pydantic = SettingsLoader(
        settings_path=Path("settings.yml"),
        env_path=Path(".env"),
        model_class=SettingsModelPydantic,
        url_templates={
            "postgresql": "postgresql+asyncpg",
            "redis": "redis",
            "nats": "nats",
        },
        env_alias_map=ALIASES_MAP,
        dev_block="dev",
    )
    settings_pydantic: SettingsModelPydantic = loader_pydantic.load()

    print("=== Results: Pydantic ===")
    print("Application admin_id:", settings_pydantic.application.admin_id)
    print("Redis port:", settings_pydantic.redis.port)
    print("PostgreSQL host:", settings_pydantic.postgresql.host)
    print("Redis URL:", settings_pydantic.redis_url)
    print("PostgreSQL URL(s):", settings_pydantic.postgresql_url)  # может быть str или list[str]

    # === Пример использования с Dataclass ===
    loader_dataclass = SettingsLoader(
        settings_path=Path("settings.yml"),
        env_path=Path(".env"),
        model_class=SettingsModelDataClass,
        # Без url_templates — *_url поля не будут заполняться
        env_alias_map=ALIASES_MAP,
    )
    settings_dataclass: SettingsModelDataClass = loader_dataclass.load()

    print("\n=== Results: Dataclass ===")
    print("Application admin_id:", settings_dataclass.application.admin_id)
    print("Redis port:", settings_dataclass.redis.port)
    print("PostgreSQL host:", settings_dataclass.postgresql.host)
    print("Redis URL:", settings_dataclass.redis_url)  # -> None (не задан template)
    print("PostgreSQL URL:", settings_dataclass.postgresql_url)  # -> None (аналогично)


if __name__ == "__main__":
    main()
