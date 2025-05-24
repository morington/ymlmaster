from pathlib import Path
from typing import Any
from dataclasses import is_dataclass, fields
from dotenv import dotenv_values
import yaml


class SettingsLoader:
    """
    Loads settings from YAML and .env, and instantiates the given config class.
    Supports both Pydantic and dataclass-based models.
    """

    def __init__(
        self,
        settings_path: Path,
        env_path: Path,
        model_class: type,
        use_release: bool = False,
        profile: str | None = None
    ) -> None:
        """
        Args:
            settings_path: Path to the YAML settings file.
            env_path: Path to the .env file.
            model_class: The class to populate (Pydantic or dataclass).
            use_release: Use 'release' section if profile not provided.
            profile: Optional profile name (e.g., 'dev', 'release').
        """
        self.settings_path: Path = settings_path
        self.env_path: Path = env_path
        self.model_class: type = model_class
        self.profile: str = profile or ("release" if use_release else "dev")

        self.env_data: dict[str, str] = dotenv_values(self.env_path)
        self.yaml_data: dict[str, Any] = self._load_profile_data()
        self.final_data: dict[str, Any] = self._inject_env(self.yaml_data)

    def _load_profile_data(self) -> dict[str, Any]:
        with self.settings_path.open("r", encoding="utf-8") as f:
            all_settings: dict[str, Any] = yaml.safe_load(f)

        profile_settings = all_settings.get(self.profile)
        if not profile_settings:
            print(
                f"[error] Profile '{self.profile}' not found in file: `{self.settings_path}`\n\n"
                f"Hint: pass a valid '--profile' name or use 'use_release=True'.\n"
                f"Available sections: {', '.join(all_settings.keys())}"
            )
            exit(1)

        return profile_settings

    def _inject_env(self, data: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        for key, val in data.items():
            full_key = f"{prefix}__{key}".upper() if prefix else key.upper()

            if isinstance(val, dict):
                data[key] = self._inject_env(val, full_key)
            elif val is None:
                env_value = self.env_data.get(full_key)
                if env_value is not None:
                    if "port" in key.lower() and ":" not in env_value:
                        env_value = f"127.0.0.1:{env_value}"
                    data[key] = env_value
        return data

    def _build_dataclass(self, cls: type, data: dict[str, Any]) -> Any:
        """
        Recursively constructs a dataclass from nested dictionary data.

        Args:
            cls: Dataclass type to instantiate.
            data: Dictionary with values.

        Returns:
            Instance of the dataclass.
        """
        kwargs = {}
        for field in fields(cls):
            value = data.get(field.name)
            if value is not None and is_dataclass(field.type):
                kwargs[field.name] = self._build_dataclass(field.type, value)
            else:
                kwargs[field.name] = value
        return cls(**kwargs)

    def load(self) -> Any:
        """
        Instantiates and returns the provided model class with loaded settings.

        Returns:
            An instance of model_class with populated fields.
        """
        if is_dataclass(self.model_class):
            return self._build_dataclass(self.model_class, self.final_data)
        return self.model_class(**self.final_data)
