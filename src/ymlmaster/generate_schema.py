import argparse
from pathlib import Path
from typing import Any


class SchemaGenerator:
    """
    A class for generating Python data models from a YAML settings structure.
    Supports Pydantic and standard dataclass generation.
    """

    def __init__(self, use_pydantic: bool = False, class_name: str = "Settings") -> None:
        """
        Args:
            use_pydantic: If True, generate Pydantic models. Otherwise, use dataclasses.
            class_name: The name of the root-level class to generate.
        """
        self.use_pydantic: bool = use_pydantic
        self.class_name: str = class_name
        self.class_name_cache: dict[str, str] = {}

        if self.use_pydantic:
            self._ensure_pydantic_installed()

    @staticmethod
    def _ensure_pydantic_installed() -> None:
        """Raises an error if Pydantic is not installed when required."""
        try:
            import pydantic  # noqa
        except ImportError:
            raise ImportError(
                "Pydantic is required but not installed. "
                "Install it via `pip install pydantic`, or use `--type dataclass`."
            )

    def generate(self, settings_path: Path, output_path: Path, profile: str = "dev") -> None:
        """
        Generate a model file based on a given YAML profile.

        Args:
            settings_path: Path to the YAML file.
            output_path: Path where the Python model file will be written.
            profile: The root section name in the YAML (e.g., "dev", "release").
        """
        import yaml

        with settings_path.open("r", encoding="utf-8") as f:
            all_settings: dict[str, Any] = yaml.safe_load(f)

        profile_settings: dict[str, Any] | None = all_settings.get(profile)
        if not profile_settings:
            print(
                f"[error] Profile '{profile}' not found in file: `{settings_path}`\n\n"
                f"Hint: use '--profile <section>' to specify a valid section.\n"
                f"Available sections: {', '.join(all_settings.keys())}"
            )
            exit(1)

        code: str = self._build_class_code(self.class_name, profile_settings)
        header: str = self._build_header()
        full_code: str = header + "\n\n" + code

        output_path.write_text(full_code, encoding="utf-8")
        print(f"✅ Schema generated from profile '{profile}': {output_path}")

    def _build_header(self) -> str:
        """
        Returns:
            Python import header string required for the generated classes.
        """
        lines: list[str] = ["from typing import Optional"]
        if self.use_pydantic:
            lines.append("from pydantic import BaseModel")
        else:
            lines.append("from dataclasses import dataclass")
        return "\n".join(lines)

    def _to_camel_case(self, name: str) -> str:
        """
        Converts a snake_case string to CamelCase and caches the result.

        Args:
            name: The snake_case name.

        Returns:
            CamelCase version of the name.
        """
        if name in self.class_name_cache:
            return self.class_name_cache[name]
        parts: list[str] = name.split('_')
        camel: str = ''.join(word.capitalize() for word in parts)
        self.class_name_cache[name] = camel
        return camel

    def _build_class_code(self, name: str, data: dict[str, Any], indent: int = 0) -> str:
        """
        Recursively generates nested class definitions from a dictionary.

        Args:
            name: Class name (root or nested).
            data: Dictionary structure representing fields.
            indent: Indentation level.

        Returns:
            Full class definition as a string.
        """
        lines: list[str] = []
        nested_blocks: list[str] = []
        ind: str = "    " * indent
        field_types: dict[str, str] = {}

        class_name: str = self._to_camel_case(name)
        self.class_name_cache[name] = class_name

        for key, val in data.items():
            if isinstance(val, dict):
                sub_class_name: str = self._to_camel_case(key)
                self.class_name_cache[key] = sub_class_name
                nested_code: str = self._build_class_code(key, val, indent=0)
                nested_blocks.append(nested_code)
                field_types[key] = sub_class_name
            else:
                field_types[key] = "Optional[str]"

        decorator: str = "@dataclass" if not self.use_pydantic else ""
        base: str = "" if not self.use_pydantic else "(BaseModel)"

        lines.append(f"{ind}{decorator}")
        lines.append(f"{ind}class {class_name}{base}:")

        if not data:
            lines.append(f"{ind}    pass")
        else:
            for field_name, field_type in field_types.items():
                lines.append(f"{ind}    {field_name}: {field_type} = None")

        return "\n\n".join(nested_blocks + ["\n".join(lines)])


def main() -> None:
    """
    Entry point for CLI execution.
    Parses arguments and triggers schema generation.
    """
    parser = argparse.ArgumentParser(description="Generate Python settings model from a YAML template.")
    parser.add_argument("--settings", required=True, help="Path to YAML file containing the settings structure.")
    parser.add_argument("--output", required=True, help="Path to output .py file.")
    parser.add_argument("--type", choices=["pydantic", "dataclass"], default="dataclass", help="Type of model to generate.")
    parser.add_argument("--profile", default="dev", help="Profile section to generate schema from (default: dev).")

    args = parser.parse_args()

    generator = SchemaGenerator(use_pydantic=(args.type == "pydantic"))
    generator.generate(Path(args.settings), Path(args.output), profile=args.profile)


if __name__ == "__main__":
    main()
