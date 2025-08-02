from pathlib import Path
from typing import Any, TypeVar, Type
from dataclasses import is_dataclass, fields
from dotenv import dotenv_values
from yarl import URL
import yaml
import os

T = TypeVar("T")


class SettingsLoader:
    """
    Loads settings from YAML and .env, injects *_url fields, and instantiates the given config class.
    """

    def __init__(
        self,
        settings_path: Path,
        env_path: Path,
        model_class: type,
        use_release: bool = False,
        profile: str | None = None,
        url_templates: dict[str, str] | None = None,
        env_alias_map: dict[str, str] | None = None,
        dev_block: str = "dev",
        release_block: str = "release",
    ) -> None:
        self.settings_path = settings_path
        self.env_path = env_path
        self.model_class = model_class
        self.profile = profile or (release_block if use_release else dev_block)
        self.url_templates = url_templates or dict()
        self.env_alias_map = env_alias_map or dict()

        self.env_data: dict[str, str] = {**dotenv_values(self.env_path), **os.environ}

        if self.env_alias_map:
            aliased_env_data = {
                **{
                    nested: self.env_data[flat]
                    for flat, nested in self.env_alias_map.items()
                    if flat in self.env_data and nested not in self.env_data
                },
                **self.env_data,
            }
            os.environ.update(aliased_env_data)
        else:
            os.environ.update(self.env_data)

        self.yaml_data: dict[str, Any] = self._load_profile_data()
        self.final_data: dict[str, Any] = self._inject_env(self.yaml_data)
        self._inject_generated_urls()

    def _load_profile_data(self) -> dict[str, Any]:
        with self.settings_path.open("r", encoding="utf-8") as f:
            all_settings: dict[str, Any] = yaml.safe_load(f)

        profile_settings = all_settings.get(self.profile)
        if not profile_settings:
            print(f"[error] Profile '{self.profile}' not found in file: `{self.settings_path}`")
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

    def _inject_generated_urls(self) -> None:
        for section, scheme in self.url_templates.items():
            cfg = self.final_data.get(section)
            if not cfg:
                continue

            # Parse all values into lists (comma-separated)
            def parse_list(val: str | None) -> list[str]:
                if not val:
                    return []
                return [v.strip() for v in val.split(",") if v.strip()]

            hosts = parse_list(cfg.get("host"))
            users = parse_list(cfg.get("user"))
            passwords = parse_list(cfg.get("password"))
            ports = parse_list(cfg.get("port"))
            dbs = parse_list(cfg.get("db") or os.getenv(f"{section.upper()}__DB", ""))

            urls = []
            for i in range(len(hosts)):
                host = hosts[i]
                user = users[i] if i < len(users) else users[0] if users else None
                password = passwords[i] if i < len(passwords) else passwords[0] if passwords else None
                db_name = dbs[i] if i < len(dbs) else dbs[0] if dbs else None
                raw_port = ports[i] if i < len(ports) else ports[0] if ports else None

                port: int | None = None
                if raw_port:
                    raw_port = raw_port.strip().replace("127.0.0.1:", "").replace("0.0.0.0:", "")
                    try:
                        port = int(raw_port)
                    except ValueError:
                        print(f"[warn] Invalid port '{raw_port}' for {section}, skipping.")

                path = f"/{db_name}" if db_name else ""

                try:
                    url = URL.build(
                        scheme=scheme,
                        user=user,
                        password=password,
                        host=host,
                        port=port,
                        path=path
                    )
                    urls.append(str(url))
                except Exception as e:
                    print(f"[warn] Failed to build URL for {section}: {e}")

            if urls:
                self.final_data[f"{section}_url"] = urls if len(urls) > 1 else urls[0]

    def _build_dataclass(self, cls: Type[T] | T, data: dict[str, Any]) -> T:
        if not is_dataclass(cls):
            raise TypeError(f"Expected dataclass type, got: {type(cls)}")

        kwargs = {}
        for field in fields(cls):
            value = data.get(field.name)
            if value is not None and is_dataclass(field.type):
                kwargs[field.name] = self._build_dataclass(field.type, value)
            else:
                kwargs[field.name] = value
        return cls(**kwargs)

    def load(self) -> Any:
        if is_dataclass(self.model_class):
            return self._build_dataclass(self.model_class, self.final_data)
        return self.model_class(**self.final_data)
