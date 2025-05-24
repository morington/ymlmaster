from pathlib import Path

from ymlmaster import SettingsLoader

from settings_model_pydantic import Settings as SettingsModelPydantic
from settings_model_dataclass import Settings as SettingsModelDataClass


def main() -> None:

    # Pydantic Model
    loader_pydantic = SettingsLoader(
        settings_path=Path("settings.yml"),
        env_path=Path(".env"),
        model_class=SettingsModelPydantic,
        # default:
        # use_release=False,
        # profile=None
    )
    settings_pydantic: SettingsModelPydantic = loader_pydantic.load()

    print("Results model pydantic:")
    print(settings_pydantic.application.admin_id)
    print(settings_pydantic.redis.port)
    print(settings_pydantic.postgresql.host)

    # Dataclass
    loader_dataclass = SettingsLoader(
        settings_path=Path("settings.yml"),
        env_path=Path(".env"),
        model_class=SettingsModelDataClass,
        # default:
        # use_release=False,
        # profile=None
    )
    settings_dataclass: SettingsModelDataClass = loader_dataclass.load()

    print("\nResults model dataclass:")
    print(settings_dataclass.application.admin_id)
    print(settings_dataclass.redis.port)
    print(settings_dataclass.postgresql.host)


if __name__ == "__main__":
    main()
