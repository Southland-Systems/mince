from __future__ import annotations

import json
import math
import re
import shlex
from copy import deepcopy
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Callable


def validate_storage_name(name: str, label: str = "name") -> str:
    name = name.strip()
    if (
        not name
        or name in (".", "..")
        or any(character in name for character in ("/", "\\"))
        or any(ord(character) < 32 for character in name)
    ):
        raise ValueError(f"invalid {label}")
    return name


def validate_profile_name(name: str) -> str:
    name = name.strip()
    if not name.isidentifier():
        raise ValueError(f"invalid profile name '{name}'")
    return name


def read_json_document(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read {label} {path} ({exc})") from exc


def write_json_document(path: Path, document: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def read_text_preserving_line_endings(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as file:
        return file.read()


def read_file(path: Path, *, raise_errors: bool = False) -> str:
    try:
        return read_text_preserving_line_endings(path)
    except UnicodeDecodeError:
        return path.read_bytes().decode("utf-8", errors="replace")
    except Exception as exc:
        if raise_errors:
            raise
        return f"ERROR: cannot read file {path} ({exc})"


def append_suffix_to_path(original_path: Path, suffix: str) -> Path:
    return original_path.with_name(original_path.name + suffix)


def join_prompt_sections(*parts: str) -> str:
    return "\n\n".join(
        part.strip() for part in parts if part.strip()
    )


def read_prompt_files(paths: Path | list[Path]) -> str:
    prompt_paths = paths if isinstance(paths, list) else [paths]
    return join_prompt_sections(*(
        read_file(prompt_path, raise_errors=True)
        for prompt_path in prompt_paths
    ))


def format_config_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if value is None:
        return ""
    return str(value)


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in ("on", "true", "yes", "1"):
        return True
    if normalized in ("off", "false", "no", "0"):
        return False
    raise ValueError("expected a boolean value (true/false)")


def coerce_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        try:
            return parse_bool(value)
        except ValueError:
            pass
    return default


def coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_optional_float(value: Any) -> float | None:
    if value is None or (
        isinstance(value, str) and value.strip().lower() == "off"
    ):
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("expected a finite number or 'off'")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("expected a finite number or 'off'") from exc
    if not math.isfinite(number):
        raise ValueError("expected a finite number or 'off'")
    return number


def parse_optional_float_range(
    value: Any,
    maximum: float,
    minimum: float = 0.0,
) -> float | None:
    number = parse_optional_float(value)
    if number is not None and not minimum <= number <= maximum:
        raise ValueError(
            f"must be between {minimum:g} and {maximum} or off"
        )
    return number


def parse_nonnegative_float(value: Any, *, unit: str = "") -> float:
    number = parse_optional_float(value)
    if number is None or number < 0:
        raise ValueError(
            "must be a finite non-negative number"
            + (f" of {unit}" if unit else "")
        )
    return number


def parse_retry_count(value: Any) -> int:
    if isinstance(value, bool):
        raise ValueError("retry count must be a non-negative integer")
    if isinstance(value, int):
        retry_count = value
    elif isinstance(value, str) and re.fullmatch(r"\d+", value.strip()):
        retry_count = int(value.strip())
    else:
        raise ValueError("retry count must be a non-negative integer")
    if retry_count < 0:
        raise ValueError("retry count must be a non-negative integer")
    return retry_count


def parse_config_integer(value: Any, *, positive: bool = False) -> int:
    try:
        number = parse_retry_count(value)
    except ValueError as exc:
        raise ValueError("must be a non-negative integer") from exc
    if positive and number == 0:
        raise ValueError("must be a positive integer")
    return number


def parse_string(
    value: Any,
    *,
    strip: bool = False,
    nonempty: bool = False,
    allow_null: bool = True,
) -> str:
    if not isinstance(value, str):
        raise ValueError("must be a string")
    if strip:
        value = value.strip()
    if nonempty and not value:
        raise ValueError("cannot be empty")
    if not allow_null and "\x00" in value:
        raise ValueError("cannot contain a null byte")
    return value


def parse_filename_suffix(value: Any) -> str:
    value = parse_string(value, allow_null=False)
    append_suffix_to_path(Path("file"), value)
    return value


def parse_bool_or_string(value: Any, name: str) -> bool | str:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        raw_value = value.strip()
        if raw_value:
            try:
                return parse_bool(raw_value)
            except ValueError:
                return raw_value
    raise ValueError(f"{name} must be a boolean or non-empty string")


def resolve_optional_string_setting(value: Any, name: str) -> str | None:
    if value == "":
        return ""
    parsed = parse_bool_or_string(value, name)
    if isinstance(parsed, bool):
        return "" if parsed else None
    return parsed


def split_config_values(
    value: Any,
    separators: str = ":",
    *,
    split_items: bool = False,
) -> list[Any]:
    if isinstance(value, (list, tuple)):
        return [
            part
            for item in value
            for part in (
                split_config_values(item, separators)
                if split_items and isinstance(item, str)
                else [item]
            )
        ]
    if not isinstance(value, str):
        raise ValueError("expected space- or colon-separated values")
    lexer = shlex.shlex(value, posix=True)
    lexer.whitespace_split = True
    lexer.whitespace += separators
    lexer.commenters = ""
    return list(lexer)


def parse_config_files(value: Any) -> list[str]:
    if value is None:
        return []
    files = split_config_values(value, ":|")
    if any(not isinstance(path, str) or not path.strip() for path in files):
        raise ValueError("config files must not contain empty or non-string paths")
    if any("\x00" in path for path in files):
        raise ValueError("paths cannot contain a null byte")
    return files


def parse_backup_paths(value: Any, name: str = "backup") -> list[str] | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return [] if value else None
    parts = split_config_values(value)
    if any(not isinstance(part, str) for part in parts):
        raise ValueError("expected destination and source directory paths")
    parts = [part.strip() for part in parts]
    if any("\x00" in part for part in parts):
        raise ValueError("paths cannot contain a null byte")
    if any(not part for part in parts[1:]):
        raise ValueError("source directory paths cannot be empty")
    if parts:
        destination = resolve_optional_string_setting(parts[0], name)
        if destination is None:
            if len(parts) > 1:
                raise ValueError("off cannot be combined with source directories")
            return None
        parts[0] = destination
    return parts


def parse_token_cost(value: Any) -> tuple[float, float] | None:
    if value is None:
        return None
    parts = split_config_values(value, split_items=True)
    if (
        len(parts) == 1
        and isinstance(parts[0], str)
        and parts[0].strip().lower() == "off"
    ):
        return None
    if len(parts) != 2:
        raise ValueError(
            "expected two space- or colon-separated costs or 'off' (ex: 0.27 2.27)"
        )
    try:
        input_cost, output_cost = (parse_optional_float(part) for part in parts)
    except ValueError as exc:
        raise ValueError("token costs must be finite non-negative floats") from exc
    if any(cost is None or cost < 0 for cost in (input_cost, output_cost)):
        raise ValueError("token costs must be finite non-negative floats")
    return input_cost, output_cost


def parse_key_value_object(s: str) -> dict[str, Any]:
    s = s.strip()
    if not s:
        return {}
    if s.startswith(("{", "[")):
        try:
            value = json.loads(s)
        except ValueError as exc:
            raise ValueError(f"invalid JSON ({exc})") from exc
        if not isinstance(value, dict):
            raise ValueError("must contain a JSON object")
        return value
    result: dict[str, Any] = {}
    for pair in s.split(","):
        if "=" not in pair:
            raise ValueError(f"expected key=value, got {pair.strip()!r}")
        key, value = pair.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("key=value names cannot be empty")
        value = value.strip()
        low = value.lower()
        if low == "true":
            result[key] = True
        elif low == "false":
            result[key] = False
        else:
            try:
                result[key] = int(value)
            except ValueError:
                try:
                    result[key] = float(value)
                except ValueError:
                    result[key] = value
    return result


def parse_object_setting(value: Any) -> dict[str, Any]:
    if value is None:
        value = ""
    if isinstance(value, str):
        value = parse_key_value_object(value)
    if not isinstance(value, dict):
        raise ValueError("must be a JSON object or key=value string")
    json.dumps(value, ensure_ascii=False, allow_nan=False).encode("utf-8")
    return value


def parse_turn_interval(value: Any) -> int | None:
    if value is None or (
        isinstance(value, str) and value.strip().lower() == "off"
    ):
        return None
    try:
        interval = parse_retry_count(value)
    except ValueError as exc:
        raise ValueError(
            "expected a non-negative integer turn interval or 'off'"
        ) from exc
    return interval or None


def parse_profile_interval(
    value: Any,
    name: str,
    *,
    default: Any,
    reasoning_parser: Callable[[Any], str],
    model_parser: Callable[[Any], str],
) -> tuple[int | None, str | None, str | None, str | None]:
    parts = (
        split_config_values(value, "")
        if isinstance(value, (str, list, tuple))
        else [value]
    )
    if not parts:
        parts = [default]
    if len(parts) > 4:
        raise ValueError(
            f"{name} requires INTERVAL [PROFILE] [REASONING] [MODEL]"
        )
    interval = parse_turn_interval(parts[0])
    profile = None
    if len(parts) > 1:
        if not isinstance(parts[1], str):
            raise ValueError(f"{name} profile must be a string")
        profile = validate_profile_name(parts[1])
    reasoning = reasoning_parser(parts[2]) if len(parts) > 2 else None
    model = model_parser(parts[3]) if len(parts) > 3 else None
    return interval, profile, reasoning, model


def format_profile_interval(
    value: tuple[int | None, str | None, str | None, str | None],
) -> int | str:
    interval, profile, reasoning, model = value
    if profile is None:
        return interval or "off"
    parts = [str(interval or 0), profile]
    if reasoning is not None:
        parts.append(reasoning)
    if model is not None:
        parts.append(model)
    return shlex.join(parts)


def parse_context_expires(
    value: Any,
    defaults: tuple[int, int, int],
    name: str = "context_expires",
) -> tuple[int, int, int]:
    parts = split_config_values(value, split_items=True)
    if not 1 <= len(parts) <= 3:
        raise ValueError(f"{name} requires DEFAULT [MIN] [MAX]")
    try:
        numbers = [parse_retry_count(part) for part in parts]
    except ValueError as exc:
        raise ValueError(
            f"{name} values must be non-negative integers"
        ) from exc
    default = numbers[0]
    minimum = numbers[1] if len(numbers) > 1 else defaults[1]
    maximum = numbers[2] if len(numbers) > 2 else defaults[2]
    if not minimum <= default <= maximum:
        raise ValueError(f"{name} requires MIN <= DEFAULT <= MAX")
    return default, minimum, maximum


class ConfigValues:
    def __init__(
        self,
        defaults: dict[str, Any],
        *,
        boolean_keys: tuple[str, ...] = (),
        choices: dict[str, tuple[str, ...]] | None = None,
        parsers: dict[str, Callable[[Any], Any]] | None = None,
        none_values: dict[str, Any] | None = None,
    ) -> None:
        self.defaults = deepcopy(defaults)
        self.boolean_keys = tuple(boolean_keys)
        self.choices = dict(choices or {})
        self.parsers = dict(parsers or {})
        self.none_values = deepcopy(none_values or {})

    def default_value(self, name: str) -> Any:
        if name not in self.defaults:
            raise ValueError(f"{name} has no built-in default value")
        return deepcopy(self.defaults[name])

    def parse_value(self, name: str, value: Any) -> Any:
        if name not in self.defaults:
            return value
        default = self.defaults[name]
        try:
            if isinstance(value, str):
                value.encode("utf-8")
            if value is None and name in self.none_values:
                value = deepcopy(self.none_values[name])
            parser = self.parsers.get(name)
            if parser is not None:
                value = parser(value)
            elif name in self.boolean_keys or isinstance(default, bool):
                if not isinstance(value, bool):
                    if not isinstance(value, str):
                        raise ValueError("must be a boolean")
                    value = parse_bool(value)
            elif isinstance(default, int):
                value = parse_config_integer(value)
            elif isinstance(default, float):
                value = parse_optional_float(value)
                if value is None:
                    raise ValueError("must be a finite number")
            else:
                value = parse_string(value)
            choices = self.choices.get(name)
            if choices is not None:
                value = parse_string(value, strip=True).lower()
                if value not in choices:
                    raise ValueError("must be one of " + ", ".join(choices))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{name}: {exc}") from exc
        return value

    def parse_values(self, config: dict[str, Any]) -> dict[str, Any]:
        parsed_config = config.copy()
        for name, default in self.defaults.items():
            parsed_config[name] = self.parse_value(
                name, config.get(name, default)
            )
        return parsed_config


@dataclass(frozen=True)
class ConfigAssignment:
    name: str
    value: Any = None
    reset: bool = False


def _warn(handler: Callable[[str], None] | None, message: str) -> None:
    if handler is not None:
        handler(message)


class ConfigStore:
    def __init__(
        self,
        directory: Path,
        values: ConfigValues,
        *,
        default_profile: str = "config",
        inherit_key: str = "_inherit_profile",
        builtin_profiles: dict[str, dict[str, Any]] | None = None,
        profile_aliases: dict[str, str] | None = None,
        deprecated_keys: dict[str, str | None] | None = None,
        read_only_prefixes: tuple[str, ...] = (),
        legacy_directory: Path | None = None,
        assignment_parsers: dict[str, Callable[[str], Any]] | None = None,
        managed_assignment_keys: dict[str, str] | None = None,
        warning_handler: Callable[[str], None] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.values = values
        self.default_profile = validate_profile_name(default_profile)
        self.inherit_key = inherit_key
        self.builtin_profiles = deepcopy(builtin_profiles or {})
        self.profile_aliases = dict(profile_aliases or {})
        self.deprecated_keys = dict(deprecated_keys or {})
        self.read_only_prefixes = tuple(read_only_prefixes)
        self.legacy_directory = legacy_directory
        self.assignment_parsers = dict(assignment_parsers or {})
        self.managed_assignment_keys = {
            inherit_key: f"{inherit_key} is managed by profile inheritance",
            **(managed_assignment_keys or {}),
        }
        self.warning_handler = warning_handler

    @property
    def default_path(self) -> Path:
        return self.profile_path(self.default_profile)

    def profile_path(self, name: str) -> Path:
        return self.directory / f"{validate_profile_name(name)}.json"

    def profile_name(self, path: Path) -> str | None:
        if path.suffix == ".json" and path.parent.resolve() == self.directory.resolve():
            return path.stem
        return None

    def builtin_document(self, path: Path) -> dict[str, Any] | None:
        name = self.profile_name(path)
        if name is None:
            return None
        document = self.builtin_profiles.get(name)
        if document is not None:
            return deepcopy(document)
        if not path.exists():
            if name == self.default_profile:
                return deepcopy(self.values.defaults)
            parent_name = self.profile_aliases.get(name)
            if parent_name is not None:
                return {self.inherit_key: parent_name}
        return None

    def document_exists(self, path: Path) -> bool:
        return self.builtin_document(path) is not None or path.is_file()

    def ensure_writable(self, path: Path) -> None:
        name = self.profile_name(path)
        if name is not None and (
            name in self.builtin_profiles
            or name.startswith(self.read_only_prefixes)
        ):
            raise ValueError(f"internal profile '{name}' is read-only")

    def inherit_profile_name(
        self,
        document: dict[str, Any],
        path: Path,
    ) -> str | None:
        if self.inherit_key not in document:
            return None
        value = document[self.inherit_key]
        try:
            if not isinstance(value, str):
                raise ValueError("profile name must be a string")
            return validate_profile_name(value)
        except ValueError as exc:
            raise ValueError(
                f"invalid {self.inherit_key} in {path}: "
                f"invalid inherited profile name: {value!r}"
            ) from exc

    def normalize_document(
        self,
        config: dict[str, Any],
        path: Path,
        *,
        repair_invalid: bool = False,
    ) -> dict[str, Any]:
        normalized_config = config.copy()
        for deprecated, replacement in self.deprecated_keys.items():
            if deprecated not in normalized_config:
                continue
            if replacement is not None and replacement not in normalized_config:
                normalized_config[replacement] = normalized_config[deprecated]
            del normalized_config[deprecated]
        parent_name = self.inherit_profile_name(normalized_config, path)
        fallback = (
            "inherited value" if parent_name is not None else "built-in default"
        )
        for name, default in self.values.defaults.items():
            value = normalized_config.get(name)
            if value is not None:
                try:
                    self.values.parse_value(name, value)
                except ValueError as exc:
                    if not repair_invalid:
                        raise
                    _warn(
                        self.warning_handler,
                        f"Invalid configuration value in {path}: {exc}; "
                        f"using the {fallback}.",
                    )
                else:
                    continue
            if parent_name is None:
                normalized_config[name] = deepcopy(default)
            else:
                normalized_config.pop(name, None)
        return normalized_config

    def read_document(
        self,
        path: Path,
        missing_ok: bool = False,
        *,
        write_updates: bool = True,
    ) -> dict[str, Any]:
        builtin_document = self.builtin_document(path)
        if builtin_document is not None:
            return builtin_document
        if not path.exists():
            if missing_ok:
                return {}
            raise ValueError(f"configuration file does not exist: {path}")
        raw = read_json_document(path, "configuration file")
        if not isinstance(raw, dict):
            raise ValueError(f"configuration file {path} must contain a JSON object")
        normalized_config = self.normalize_document(
            raw, path, repair_invalid=True
        )
        if write_updates and normalized_config != raw:
            try:
                write_json_document(path, normalized_config)
            except OSError as exc:
                _warn(
                    self.warning_handler,
                    f"Failed to update configuration file {path}: {exc}",
                )
        return normalized_config

    def _merged_from_path(
        self,
        path: Path,
        active_paths: set[Path],
        *,
        write_updates: bool = True,
    ) -> dict[str, Any]:
        resolved_path = path.parent.resolve() / path.name
        if resolved_path in active_paths:
            raise ValueError(f"configuration inheritance cycle detected at {path}")
        active_paths.add(resolved_path)
        try:
            config = deepcopy(self.values.defaults)
            raw = self.read_document(
                path, missing_ok=True, write_updates=write_updates
            )
            parent_name = self.inherit_profile_name(raw, path)
            if parent_name is not None:
                parent_path = self.profile_path(parent_name)
                if not self.document_exists(parent_path):
                    raise ValueError(
                        f"inherited profile '{parent_name}' does not exist"
                    )
                config.update(self._merged_from_path(
                    parent_path, active_paths, write_updates=write_updates
                ))
            config.update(raw)
            return config
        finally:
            active_paths.remove(resolved_path)

    def merged(
        self,
        path: Path | None = None,
        *,
        write_updates: bool = True,
    ) -> dict[str, Any]:
        return self._merged_from_path(
            self.default_path if path is None else path,
            set(),
            write_updates=write_updates,
        )

    def inherited_names(self, path: Path) -> set[str]:
        document = self.read_document(path, missing_ok=True)
        parent_name = self.inherit_profile_name(document, path)
        if parent_name is None:
            return set()
        parent_config = self.merged(self.profile_path(parent_name))
        return set(parent_config) - set(document)

    def ensure_directory(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.legacy_directory is None:
            return
        for path in sorted(self.legacy_directory.glob("*.json")):
            if not path.is_file():
                continue
            destination = self.directory / path.name
            if destination.exists() or destination.is_symlink():
                raise ValueError(
                    f"cannot migrate configuration file {path}: "
                    f"destination already exists: {destination}"
                )
            path.rename(destination)

    def ensure_exists(self, path: Path | None = None) -> None:
        self.ensure_directory()
        if not self.default_path.exists():
            self.save(deepcopy(self.values.defaults), self.default_path)
        path = self.default_path if path is None else path
        if not self.document_exists(path):
            self.save(deepcopy(self.values.defaults), path)

    def _prune_inherited(
        self,
        config: dict[str, Any],
        parent_name: str,
        path: Path,
    ) -> dict[str, Any]:
        parent_path = self.profile_path(parent_name)
        if not self.document_exists(parent_path):
            raise ValueError(f"inherited profile '{parent_name}' does not exist")
        parent_config = self._merged_from_path(
            parent_path, {path.parent.resolve() / path.name}
        )
        pruned: dict[str, Any] = {self.inherit_key: parent_name}
        for name, value in config.items():
            if name == self.inherit_key:
                continue
            if name not in parent_config or value != parent_config[name]:
                pruned[name] = value
        return pruned

    def save(self, config: dict[str, Any], path: Path | None = None) -> None:
        path = self.default_path if path is None else path
        self.ensure_writable(path)
        raw_document = self.read_document(path, missing_ok=True)
        parent_name = self.inherit_profile_name(
            raw_document if path.exists() else config, path
        )
        output_config = config.copy()
        if parent_name is None:
            output_config.pop(self.inherit_key, None)
        else:
            output_config[self.inherit_key] = parent_name
        output_config = self.normalize_document(output_config, path)
        if parent_name is not None:
            output_config = self._prune_inherited(
                output_config, parent_name, path
            )
        write_json_document(path, output_config)

    def document_paths(self) -> list[Path]:
        return sorted(self.directory.glob("*.json"))

    def profile_names(self) -> list[str]:
        names = {
            path.stem for path in self.document_paths() if path.is_file()
        }
        names.update(self.builtin_profiles)
        return [self.default_profile] + sorted(names - {self.default_profile})

    def profile_configs(
        self,
        names: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        selected_names: list[str] = []
        for name in names or self.profile_names():
            name = validate_profile_name(name)
            if not self.document_exists(self.profile_path(name)):
                raise ValueError(f"profile '{name}' does not exist")
            if name not in selected_names:
                selected_names.append(name)
        return {
            name: self.merged(self.profile_path(name))
            for name in selected_names
        }

    def copy_profile(
        self,
        source_name: str,
        destination_name: str,
        inherit: bool = False,
    ) -> tuple[str, str]:
        source_name = validate_profile_name(source_name)
        destination_name = validate_profile_name(destination_name)
        if destination_name == self.default_profile and inherit:
            raise ValueError(
                f"cannot create a profile named '{self.default_profile}'"
            )
        if source_name == destination_name:
            raise ValueError("source and destination profiles must differ")
        source_path = self.profile_path(source_name)
        destination_path = self.profile_path(destination_name)
        self.ensure_writable(destination_path)
        if not self.document_exists(source_path):
            raise ValueError(f"source profile '{source_name}' does not exist")
        if destination_path.exists() and destination_name != self.default_profile:
            raise ValueError(
                f"destination profile '{destination_name}' already exists"
            )
        if destination_name == self.default_profile:
            config = self.merged(source_path)
            config.pop(self.inherit_key, None)
            write_json_document(destination_path, config)
        else:
            config = (
                {self.inherit_key: source_name}
                if inherit
                else self.read_document(source_path)
            )
            self.save(config, destination_path)
        return source_name, destination_name

    def remove_profile(self, name: str) -> tuple[str, str | None]:
        name = validate_profile_name(name)
        if name == self.default_profile:
            raise ValueError(
                f"cannot remove the default '{self.default_profile}' profile"
            )
        path = self.profile_path(name)
        self.ensure_writable(path)
        if not path.exists():
            if name in self.profile_aliases:
                raise ValueError(f"profile '{name}' has no user override to remove")
            raise ValueError(f"profile '{name}' does not exist")
        path.unlink()
        return name, self.profile_aliases.get(name)

    def canonical_assignment_name(self, name: str) -> str:
        name = name.strip()
        if not name:
            raise ValueError("configuration name cannot be empty")
        canonical_name = self.deprecated_keys.get(name) or name
        if canonical_name in self.managed_assignment_keys:
            raise ValueError(self.managed_assignment_keys[canonical_name])
        return canonical_name

    def parse_assignment(
        self,
        value: str,
        config: dict[str, Any],
        *,
        inherited_defaults: bool = False,
    ) -> ConfigAssignment:
        if "=" not in value:
            raise ValueError("expected NAME=VALUE")
        name, raw_value = value.split("=", 1)
        name = name.strip()
        canonical_name = self.canonical_assignment_name(name)
        raw_value = raw_value.strip()
        if name in self.deprecated_keys and name not in config:
            raise ValueError(
                f"{name} is deprecated and is not present in the config"
            )
        if raw_value == "DEFAULT":
            if inherited_defaults:
                if name not in config and canonical_name not in config:
                    raise ValueError(f"{name} has no built-in default value")
                return ConfigAssignment(canonical_name, reset=True)
            parsed_value = self.values.default_value(canonical_name)
        elif canonical_name in self.assignment_parsers:
            parsed_value = self.assignment_parsers[canonical_name](raw_value)
        else:
            expected = (
                self.values.defaults[canonical_name]
                if canonical_name in self.values.defaults
                else config.get(name)
            )
            if isinstance(expected, int) and not isinstance(expected, bool):
                try:
                    parsed_value = int(raw_value)
                except ValueError as exc:
                    raise ValueError(f"{name} must be an integer") from exc
            elif isinstance(expected, float):
                try:
                    parsed_value = float(raw_value)
                except ValueError as exc:
                    raise ValueError(f"{name} must be a number") from exc
            elif isinstance(expected, bool):
                try:
                    parsed_value = parse_bool(raw_value)
                except ValueError as exc:
                    raise ValueError(f"{name} must be a boolean") from exc
            else:
                parsed_value = raw_value
        self.values.parse_value(canonical_name, parsed_value)
        return ConfigAssignment(canonical_name, parsed_value)

    def update_document(
        self,
        document: dict[str, Any],
        assignments: list[ConfigAssignment],
    ) -> dict[str, Any]:
        updated_document = document.copy()
        for assignment in assignments:
            name = self.canonical_assignment_name(assignment.name)
            if assignment.reset:
                updated_document.pop(name, None)
            else:
                updated_document[name] = assignment.value
            for deprecated, replacement in self.deprecated_keys.items():
                if replacement == name:
                    updated_document.pop(deprecated, None)
        return updated_document

    def set_values(self, path: Path, values: list[str]) -> None:
        self.ensure_writable(path)
        config = self.merged(path)
        document = self.read_document(path, missing_ok=True)
        parent_name = self.inherit_profile_name(document, path)
        assignments = [
            self.parse_assignment(
                value, config, inherited_defaults=parent_name is not None
            )
            for value in values
        ]
        self.save(self.update_document(
            document if parent_name is not None else config, assignments
        ), path)

    def set_from_profile(
        self,
        path: Path,
        name: str,
        source_profile: str,
    ) -> None:
        name = name.strip()
        canonical_name = self.canonical_assignment_name(name)
        source_profile = validate_profile_name(source_profile)
        source_path = self.profile_path(source_profile)
        source_config = self.read_document(source_path)
        if self.inherit_key in source_config:
            source_config = self.merged(source_path)
        if name in source_config:
            value = source_config[name]
        elif canonical_name in source_config:
            value = source_config[canonical_name]
        else:
            raise ValueError(
                f"configuration value '{name}' does not exist in "
                f"profile '{source_profile}'"
            )
        self.save(self.update_document(
            self.merged(path), [ConfigAssignment(canonical_name, value)]
        ), path)


def validate_prompt_name(name: str) -> str:
    name = validate_storage_name(name, "prompt name")
    if "|" in name:
        raise ValueError("invalid prompt name")
    return name


def parse_prompt_file_definitions(value: Any) -> tuple[list[str], str] | None:
    if not isinstance(value, str):
        return None
    prompt = value.strip()
    if not prompt.startswith(("/", "./", "@")):
        return None
    match = re.match(r"^(\S+)(?:\s+(.*))?$", prompt, re.DOTALL)
    if match is None:
        return None
    definitions = match.group(1).split("|")
    if not definitions or any(
        not definition
        or not definition.startswith(("/", "./", "@"))
        for definition in definitions
    ):
        return None
    return definitions, (match.group(2) or "").strip()


PROMPT_EXPANSION_PATTERN = re.compile(r"\^\^([^^\r\n\s]+?)\^\^")


class PromptStore:
    def __init__(
        self,
        directory: Path,
        *,
        defaults: dict[str, str] | None = None,
        aliases: dict[str, str] | None = None,
        warning_handler: Callable[[str], None] | None = None,
    ) -> None:
        self.directory = Path(directory)
        self.defaults = dict(defaults or {})
        self.aliases = dict(aliases or {})
        self.warning_handler = warning_handler

    def path(self, name: str) -> Path:
        name = validate_prompt_name(name)
        name = validate_prompt_name(self.aliases.get(name, name))
        return self.directory / f"{name}.md"

    def paths(self, names: list[str] | None = None) -> list[Path]:
        if names:
            paths = [self.path(name) for name in names]
            for path in paths:
                if not path.is_file():
                    raise ValueError(f"prompt file does not exist: {path}")
            return paths
        return sorted(
            (path for path in self.directory.glob("*.md") if path.is_file()),
            key=lambda path: path.stem,
        )

    def entries(
        self,
        names: list[str] | None = None,
    ) -> list[tuple[Path, str]]:
        return [
            (path, path.read_text(encoding="utf-8"))
            for path in self.paths(names)
        ]

    def read(self, name: str) -> str:
        path = self.path(name)
        if not path.is_file():
            raise ValueError(f"prompt file does not exist: {path}")
        return path.read_text(encoding="utf-8")

    def write(self, name: str, content: str) -> Path:
        path = self.path(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def seed_defaults(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        for name, prompt in self.defaults.items():
            try:
                with self.path(name).open("x", encoding="utf-8") as prompt_file:
                    prompt_file.write(prompt)
            except FileExistsError:
                pass

    def reset_defaults(self, names: list[str] | None = None) -> list[Path]:
        entries: list[tuple[Path, str]] = []
        for name in self.defaults if names is None else names:
            path = self.path(name)
            if path.stem not in self.defaults:
                raise ValueError(f"prompt '{name}' has no built-in default")
            if path.exists() and not path.is_file():
                raise ValueError(f"prompt path is not a file: {path}")
            entries.append((path, self.defaults[path.stem]))
        for path, prompt in entries:
            self.write(path.stem, prompt)
        return [path for path, _ in entries]

    def remove(self, name: str) -> Path:
        path = self.path(name)
        if path.exists() and not path.is_file():
            raise ValueError(f"prompt path is not a file: {path}")
        if path.exists():
            path.unlink()
        return path

    def configured_path(self, value: str) -> Path:
        candidate = value.strip()
        if candidate.startswith("@"):
            return self.path(candidate[1:])
        if candidate.startswith("./"):
            filename = candidate[2:]
            if (
                not filename
                or filename in (".", "..")
                or Path(filename).name != filename
            ):
                raise ValueError(
                    "relative configured prompt files must be filenames"
                )
            return self.directory / filename
        return Path(candidate)

    def path_matches(self, value: str, prompt_path: Path) -> bool:
        candidate = value.strip()
        if candidate == str(prompt_path):
            return True
        if not candidate.startswith(("/", "./", "@")):
            return False
        try:
            return self.configured_path(candidate).resolve() == prompt_path.resolve()
        except Exception:
            return False

    def remove_reference(
        self,
        value: Any,
        prompt_path: Path,
    ) -> tuple[Any, bool]:
        parsed = parse_prompt_file_definitions(value)
        if parsed is None:
            return value, False
        definitions, prompt_text = parsed
        remaining: list[str] = []
        removed = False
        for definition in definitions:
            if self.path_matches(definition, prompt_path):
                removed = True
            else:
                remaining.append(definition)
        if not removed:
            return value, False
        if not remaining:
            return prompt_text or None, True
        new_value = "|".join(remaining)
        if prompt_text:
            new_value += f" {prompt_text}"
        return new_value, True

    def expand(self, value: str, enabled: bool = False) -> str:
        if not enabled:
            return value

        def expand(text: str, active_names: frozenset[str]) -> str:
            def replace_name(match: re.Match[str]) -> str:
                display_name = match.group(1).strip()
                try:
                    prompt_path = self.path(display_name)
                    name = prompt_path.stem
                    if name in active_names:
                        raise ValueError("recursive prompt expansion")
                    if not prompt_path.is_file():
                        raise FileNotFoundError(
                            f"prompt library entry does not exist: {prompt_path}"
                        )
                    prompt_text = prompt_path.read_text(encoding="utf-8").strip()
                    return expand(prompt_text, active_names | {name})
                except Exception as exc:
                    _warn(
                        self.warning_handler,
                        f"Could not expand prompt name '{display_name}': {exc}",
                    )
                    return match.group(0)

            return PROMPT_EXPANSION_PATTERN.sub(replace_name, text)

        return expand(value, frozenset())

    def resolve(self, value: Any, default: str) -> str:
        prompt = str(value if value is not None else default).strip()
        parsed = parse_prompt_file_definitions(prompt)
        if parsed is None:
            return prompt
        file_definitions, prompt_text = parsed
        try:
            prompt_paths = [
                self.configured_path(definition)
                for definition in file_definitions
            ]
            return join_prompt_sections(
                read_prompt_files(prompt_paths), prompt_text
            )
        except Exception as exc:
            raise ValueError(
                f"cannot read configured system prompt file {value} ({exc})"
            ) from exc


class ProfilePrompts:
    def __init__(
        self,
        configs: ConfigStore,
        prompts: PromptStore,
        *,
        prompt_types: dict[str, str],
        default_references: dict[str, str],
    ) -> None:
        self.configs = configs
        self.prompts = prompts
        self.prompt_types = dict(prompt_types)
        self.default_references = dict(default_references)
        self.keys = tuple(dict.fromkeys(self.prompt_types.values()))

    def type_key(self, value: str) -> str:
        normalized = " ".join(
            value.strip().lower().replace("_", " ").replace("-", " ").split()
        )
        try:
            return self.prompt_types[normalized]
        except KeyError as exc:
            names = list(self.prompt_types)
            choices = (
                ", ".join(names[:-1]) + f", or {names[-1]}"
                if len(names) > 1
                else ", ".join(names)
            )
            raise ValueError(
                f"unknown prompt type '{value}'; choose {choices}"
            ) from exc

    def default_keys(self, value: str = "") -> list[str]:
        if not value:
            return list(self.keys)
        selected: list[str] = []
        for raw_type in value.split(","):
            key = self.type_key(raw_type)
            if key not in selected:
                selected.append(key)
        return selected

    def reset_defaults(self, keys: list[str]) -> list[Path]:
        names = [
            self.prompts.configured_path(self.default_references[key]).stem
            for key in keys
        ]
        return self.prompts.reset_defaults(names)

    def unassign_from_document(
        self,
        document: dict[str, Any],
        prompt_path: Path,
        keys: tuple[str, ...],
    ) -> bool:
        changed = False
        for key in keys:
            if key not in document:
                continue
            new_value, removed = self.prompts.remove_reference(
                document[key], prompt_path
            )
            if not removed:
                continue
            if new_value is None:
                if self.configs.inherit_key in document:
                    document.pop(key, None)
                else:
                    document[key] = self.configs.values.default_value(key)
            else:
                document[key] = new_value
            changed = True
        return changed

    def assign(
        self,
        name: str,
        prompt_type: str,
        profile: str,
        assignment_mode: str = "prepend",
    ) -> tuple[Path, str, str]:
        prompt_path = self.prompts.path(name)
        if not prompt_path.is_file():
            raise ValueError(f"prompt file does not exist: {prompt_path}")
        if assignment_mode not in ("prepend", "replace", "string"):
            raise ValueError(f"unknown prompt assignment mode '{assignment_mode}'")
        profile = validate_profile_name(profile)
        config_key = self.type_key(prompt_type)
        profile_path = self.configs.profile_path(profile)
        self.configs.ensure_writable(profile_path)
        config = self.configs.read_document(profile_path, missing_ok=True)
        prompt_reference = f"./{prompt_path.name}"
        existing = config.get(config_key)
        if (
            config_key not in config
            and self.configs.inherit_profile_name(config, profile_path) is not None
        ):
            existing = self.configs.merged(profile_path).get(config_key)
        if assignment_mode == "string":
            config[config_key] = self.prompts.read(name).strip()
        elif assignment_mode == "replace":
            config[config_key] = prompt_reference
        else:
            parsed = parse_prompt_file_definitions(existing)
            if parsed is None:
                existing_string = existing.strip() if isinstance(existing, str) else ""
                config[config_key] = f"{prompt_reference} {existing_string}".strip()
            else:
                references, prompt_text = parsed
                if not any(
                    self.prompts.path_matches(reference, prompt_path)
                    for reference in references
                ):
                    references.insert(0, prompt_reference)
                config[config_key] = "|".join(references)
                if prompt_text:
                    config[config_key] += f" {prompt_text}"
        self.configs.save(config, profile_path)
        return prompt_path, profile, config_key

    def unassign(
        self,
        name: str,
        profile: str,
        prompt_type: str | None = None,
    ) -> tuple[Path, str, tuple[str, ...]]:
        prompt_path = self.prompts.path(name)
        profile = validate_profile_name(profile)
        profile_path = self.configs.profile_path(profile)
        self.configs.ensure_writable(profile_path)
        config = self.configs.read_document(profile_path)
        keys = (self.type_key(prompt_type),) if prompt_type is not None else self.keys
        if self.unassign_from_document(config, prompt_path, keys):
            self.configs.save(config, profile_path)
        return prompt_path, profile, keys

    def remove(self, name: str) -> Path:
        prompt_path = self.prompts.path(name)
        if prompt_path.exists() and not prompt_path.is_file():
            raise ValueError(f"prompt path is not a file: {prompt_path}")
        if prompt_path.stem in self.prompts.defaults:
            self.prompts.reset_defaults([prompt_path.stem])
        else:
            documents = [
                (path, self.configs.read_document(path))
                for path in self.configs.document_paths()
            ]
            for path, document in documents:
                if self.unassign_from_document(document, prompt_path, self.keys):
                    self.configs.save(document, path)
            self.prompts.remove(name)
        return prompt_path

    def assignments(self) -> list[tuple[Path, tuple[str, ...]]]:
        prompt_paths = self.prompts.paths()
        documents = [
            (path.stem, self.configs.read_document(path))
            for path in self.configs.document_paths()
        ]
        assignments: list[tuple[Path, tuple[str, ...]]] = []
        for prompt_path in prompt_paths:
            profiles: set[str] = set()
            for profile_name, document in documents:
                for key in self.keys:
                    parsed = parse_prompt_file_definitions(document.get(key))
                    if parsed is not None and any(
                        self.prompts.path_matches(reference, prompt_path)
                        for reference in parsed[0]
                    ):
                        profiles.add(profile_name)
                        break
            assignments.append((prompt_path, tuple(sorted(profiles))))
        return assignments


@dataclass(frozen=True)
class AgentProfile:
    name: str
    profile_type: str
    content: str
    description: str = ""


class AgentProfileRepository:
    def __init__(
        self,
        directory: Path,
        *,
        builtin_schemas: dict[str, dict[str, Any]],
        tool_prefix: str,
        custom_type: str = "custom",
        type_aliases: dict[str, str] | None = None,
        maximum_tool_name_length: int = 64,
    ) -> None:
        self.directory = Path(directory)
        self.builtin_schemas = deepcopy(builtin_schemas)
        self.tool_prefix = tool_prefix
        self.custom_type = custom_type
        self.type_aliases = dict(type_aliases or {})
        self.maximum_tool_name_length = maximum_tool_name_length

    @property
    def types(self) -> tuple[str, ...]:
        return self.custom_type, *self.builtin_schemas

    def validate_name(self, name: str) -> str:
        name = name.strip()
        if (
            re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) is None
            or len(f"{self.tool_prefix}{name}") > self.maximum_tool_name_length
        ):
            raise ValueError(f"invalid agent profile name '{name}'")
        return name

    def type_choices(self) -> str:
        return "|".join(self.types)

    def normalize_type(self, value: str) -> str:
        profile_type = value.strip().lower()
        profile_type = self.type_aliases.get(profile_type, profile_type)
        if profile_type not in self.types:
            raise ValueError(
                f"invalid agent profile type '{value}'; choose {self.type_choices()}"
            )
        return profile_type

    def path(self, name: str) -> Path:
        return self.directory / f"{self.validate_name(name)}.json"

    def read_with_document(
        self,
        name: str,
    ) -> tuple[AgentProfile, dict[str, Any]]:
        valid_name = self.validate_name(name)
        path = self.path(valid_name)
        if not path.is_file():
            raise ValueError(f"agent profile does not exist: {path}")
        document = read_json_document(path, "agent profile")
        if not isinstance(document, dict):
            raise ValueError(f"agent profile must contain a JSON object: {path}")
        allowed_fields = {"type", "content", "description"}
        if not set(document).issubset(allowed_fields):
            raise ValueError(
                "agent profile may contain only type, content, and description: "
                f"{path}"
            )
        profile_type_value = document.get("type", self.custom_type)
        content = document.get("content", "")
        description = document.get("description", "")
        if not isinstance(profile_type_value, str):
            raise ValueError(f"agent profile type must be a string: {path}")
        if not isinstance(content, str):
            raise ValueError(f"agent profile content must be a string: {path}")
        if not isinstance(description, str):
            raise ValueError(f"agent profile description must be a string: {path}")
        profile_type = self.normalize_type(profile_type_value)
        if "content" not in document and profile_type == self.custom_type:
            raise ValueError(
                f"{self.custom_type} agent profiles must contain content: {path}"
            )
        return (
            AgentProfile(
                name=valid_name,
                profile_type=profile_type,
                content=content,
                description=description,
            ),
            document,
        )

    def read(self, name: str) -> AgentProfile:
        return self.read_with_document(name)[0]

    def write(
        self,
        name: str,
        profile_type: str,
        content: str,
        description: str = "",
    ) -> Path:
        name = self.validate_name(name)
        profile_type = self.normalize_type(profile_type)
        if not isinstance(content, str):
            raise ValueError("agent profile content must be a string")
        if not isinstance(description, str):
            raise ValueError("agent profile description must be a string")
        path = self.path(name)
        write_json_document(
            path,
            {
                "type": profile_type,
                "content": content,
                "description": description,
            },
        )
        return path

    def names(self) -> list[str]:
        if not self.directory.is_dir():
            return []
        return sorted(
            path.stem
            for path in self.directory.glob("*.json")
            if path.is_file() and path.stem.isidentifier()
        )

    def parse_names(self, values: list[str] | None) -> list[str]:
        names: list[str] = []
        for value in values or []:
            for raw_name in value.split(","):
                name = self.validate_name(raw_name)
                if name not in names:
                    names.append(name)
        return names

    def load(self, values: list[str] | None) -> list[AgentProfile]:
        return [self.read(name) for name in self.parse_names(values)]

    def profiles(self) -> list[AgentProfile]:
        return [self.read(name) for name in self.names()]

    def documents(
        self,
        values: list[str] | None = None,
    ) -> dict[str, dict[str, Any]]:
        documents: dict[str, dict[str, Any]] = {}
        for name in self.parse_names(values) or self.names():
            profile, document = self.read_with_document(name)
            documents[profile.name] = document
        return documents

    def load_or_create(self, name: str) -> AgentProfile:
        name = self.validate_name(name)
        if self.path(name).exists():
            return self.read(name)
        return AgentProfile(name=name, profile_type=self.custom_type, content="")

    def set_type(self, name: str, profile_type: str) -> AgentProfile:
        profile = self.load_or_create(name)
        profile_type = self.normalize_type(profile_type)
        self.write(profile.name, profile_type, profile.content, profile.description)
        return replace(profile, profile_type=profile_type)

    def transfer(
        self,
        source_name: str,
        destination_name: str,
        rename: bool = False,
    ) -> tuple[str, str]:
        source_name = self.validate_name(source_name)
        destination_name = self.validate_name(destination_name)
        if source_name == destination_name:
            raise ValueError("source and destination agent profiles must differ")
        profile = self.read(source_name)
        destination_path = self.path(destination_name)
        if destination_path.exists():
            raise ValueError(
                f"destination agent profile already exists: {destination_path}"
            )
        if rename:
            self.path(profile.name).rename(destination_path)
        else:
            self.write(
                destination_name, profile.profile_type,
                profile.content, profile.description,
            )
        return source_name, destination_name

    def remove(self, name: str) -> AgentProfile:
        profile = self.read(name)
        self.path(profile.name).unlink()
        return profile

    def response_schema(self, profile: AgentProfile) -> dict[str, Any]:
        profile_type = self.normalize_type(profile.profile_type)
        builtin_schema = self.builtin_schemas.get(profile_type)
        if builtin_schema is not None:
            response_schema = deepcopy(builtin_schema)
        else:
            try:
                response_schema = json.loads(profile.content)
            except (TypeError, json.JSONDecodeError) as exc:
                raise ValueError(
                    f"agent profile '{profile.name}' response schema must be valid JSON"
                ) from exc
        if not isinstance(response_schema, dict):
            raise ValueError(
                f"agent profile '{profile.name}' response schema must be a JSON object"
            )
        if response_schema.get("type") == "json_schema":
            response_schema = response_schema.get("schema")
            if not isinstance(response_schema, dict):
                raise ValueError(
                    f"agent profile '{profile.name}' response format must contain "
                    "a schema object"
                )
        return {
            "type": "json_schema",
            "name": self.tool_name(profile.name),
            "strict": True,
            "schema": response_schema,
        }

    def tool_name(self, name: str) -> str:
        return f"{self.tool_prefix}{self.validate_name(name)}"
