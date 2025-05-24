import argparse
from pathlib import Path
from typing import Any


class SchemaGenerator:
    """
    Generates settings models (Pydantic or dataclass) from a YAML config.
    Adds *_url fields for specified sections via `url_fields`.
    """

    def __init__(self, use_pydantic: bool = False, class_name: str = "Settings", url_fields: list[str] | None = None) -> None:
        self.use_pydantic = use_pydantic
        self.class_name = class_name
        self.class_name_cache: dict[str, str] = {}
        self.url_fields = url_fields or []

        if self.use_pydantic:
            self._ensure_pydantic_installed()

    @staticmethod
    def _ensure_pydantic_installed() -> None:
        try:
            import pydantic  # noqa
        except ImportError:
            print("[error] Pydantic not installed. Use `--type dataclass` or install via `poetry add pydantic`.")
            exit(1)

    def generate(self, settings_path: Path, output_path: Path, profile: str = "dev") -> None:
        import yaml

        with settings_path.open("r", encoding="utf-8") as f:
            all_settings: dict[str, Any] = yaml.safe_load(f)

        profile_settings = all_settings.get(profile)
        if not profile_settings:
            print(f"[error] Profile '{profile}' not found.")
            exit(1)

        code: str = self._build_class_code(self.class_name, profile_settings)
        header: str = self._build_header()
        full_code: str = header + "\n\n" + code
        output_path.write_text(full_code, encoding="utf-8")
        print(f"✅ Schema generated: {output_path}")

    def _build_header(self) -> str:
        lines = ["from typing import Optional"]
        lines.append("from pydantic import BaseModel" if self.use_pydantic else "from dataclasses import dataclass")
        return "\n".join(lines)

    def _to_camel_case(self, name: str) -> str:
        if name in self.class_name_cache:
            return self.class_name_cache[name]
        camel = ''.join(part.capitalize() for part in name.split('_'))
        self.class_name_cache[name] = camel
        return camel

    def _build_class_code(self, name: str, data: dict[str, Any], indent: int = 0) -> str:
        lines: list[str] = []
        nested_blocks: list[str] = []
        ind = "    " * indent
        class_name = self._to_camel_case(name)
        field_types: dict[str, str] = {}

        for key, val in data.items():
            if isinstance(val, dict):
                sub_class_name = self._to_camel_case(key)
                nested_code = self._build_class_code(key, val, indent=0)
                nested_blocks.append(nested_code)
                field_types[key] = sub_class_name
            else:
                field_types[key] = "Optional[str]"

        # Add *_url fields to root class
        if name == self.class_name:
            for section in self.url_fields:
                field_types[f"{section}_url"] = "Optional[str]"

        decorator = "@dataclass" if not self.use_pydantic else ""
        base = "(BaseModel)" if self.use_pydantic else ""

        lines.append(f"{ind}{decorator}")
        lines.append(f"{ind}class {class_name}{base}:")
        if not field_types:
            lines.append(f"{ind}    pass")
        else:
            for fname, ftype in field_types.items():
                lines.append(f"{ind}    {fname}: {ftype} = None")

        return "\n\n".join(nested_blocks + ["\n".join(lines)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Python settings model from a YAML template.")
    parser.add_argument("--settings", required=True, help="Path to YAML file containing the settings structure.")
    parser.add_argument("--output", required=True, help="Path to output .py file.")
    parser.add_argument("--type", choices=["pydantic", "dataclass"], default="dataclass", help="Type of model to generate.")
    parser.add_argument("--profile", default="dev", help="Profile section to generate schema from (default: dev).")
    parser.add_argument("--url-fields", nargs="*", help="Sections for which to generate *_url fields", default=[])

    args = parser.parse_args()

    generator = SchemaGenerator(
        use_pydantic=(args.type == "pydantic"),
        url_fields=args.url_fields
    )
    generator.generate(Path(args.settings), Path(args.output), profile=args.profile)


if __name__ == "__main__":
    main()
