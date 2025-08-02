import argparse
import ast
from pathlib import Path
from typing import Any


class SchemaGenerator:
    """
    Generates settings models (Pydantic or dataclass) from a YAML config.
    Adds *_url fields for specified sections via `urls`.
    Preserves existing field definitions, docstrings, and base classes,
    but always regenerates *_url fields to ensure correct type: Optional[str | list[str]].
    """

    def __init__(self, use_pydantic: bool = False, class_name: str = "Settings", urls: list[str] | None = None) -> None:
        self.use_pydantic = use_pydantic
        self.class_name = class_name
        self.class_name_cache: dict[str, str] = {}
        self.urls = urls or []
        self.existing_classes: dict[str, dict[str, Any]] = {}

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

        if output_path.exists():
            self._load_existing_model(output_path)

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

    def _load_existing_model(self, output_path: Path) -> None:
        source = output_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        self.existing_classes.clear()

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_name = node.name
                fields: dict[str, str] = {}
                docstring: str | None = ast.get_docstring(node)
                bases = [ast.get_source_segment(source, base) for base in node.bases]

                for body_item in node.body:
                    if isinstance(body_item, ast.AnnAssign) and isinstance(body_item.target, ast.Name):
                        field_name = body_item.target.id
                        line = ast.get_source_segment(source, body_item)
                        fields[field_name] = line

                self.existing_classes[class_name] = {
                    "fields": fields,
                    "bases": bases,
                    "docstring": docstring,
                }

    def _build_header(self) -> str:
        lines = ["from typing import Optional"]
        if self.use_pydantic:
            lines.append("from pydantic import BaseModel, Field")
        else:
            lines.append("from dataclasses import dataclass")
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

        # Указываем специальный тип для *_url полей
        if name == self.class_name:
            for section in self.urls:
                field_types[f"{section}_url"] = "Optional[str | list[str]]"

        existing = self.existing_classes.get(class_name, {})
        existing_fields = existing.get("fields", {})
        existing_doc = existing.get("docstring")
        existing_bases = existing.get("bases", [])

        decorator = "@dataclass" if not self.use_pydantic else ""
        base = f"({', '.join(existing_bases)})" if existing_bases else ("(BaseModel)" if self.use_pydantic else "")

        lines.append(f"{ind}{decorator}")
        lines.append(f"{ind}class {class_name}{base}:")

        if existing_doc:
            lines.append(f'{ind}    """{existing_doc}"""')

        if not field_types:
            lines.append(f"{ind}    pass")
        else:
            for fname, ftype in field_types.items():
                # всегда перегенерируем *_url поля, даже если они уже есть
                if fname in existing_fields and not fname.endswith("_url"):
                    lines.append(f"{ind}    {existing_fields[fname]}")
                else:
                    lines.append(f"{ind}    {fname}: {ftype} = None")

        return "\n\n".join(nested_blocks + ["\n".join(lines)])


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Python settings model from a YAML template.")
    parser.add_argument("--settings", required=True, help="Path to YAML file containing the settings structure.")
    parser.add_argument("--output", required=True, help="Path to output .py file.")
    parser.add_argument("--type", choices=["pydantic", "dataclass"], default="dataclass", help="Type of model to generate.")
    parser.add_argument("--profile", default="dev", help="Profile section to generate schema from (default: dev).")
    parser.add_argument("--urls", nargs="*", help="Sections for which to generate *_url fields", default=[])

    args = parser.parse_args()

    generator = SchemaGenerator(
        use_pydantic=(args.type == "pydantic"),
        urls=args.urls
    )
    generator.generate(Path(args.settings), Path(args.output), profile=args.profile)


if __name__ == "__main__":
    main()
