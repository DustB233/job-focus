from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


BrowserFieldType = Literal["text", "textarea", "file", "checkbox"]


@dataclass(frozen=True, slots=True)
class BrowserFormField:
    key: str
    value: str | bool | Path
    field_type: BrowserFieldType = "text"
    selectors: tuple[str, ...] = ()
    label_hints: tuple[str, ...] = ()
    name_hints: tuple[str, ...] = ()
    required: bool = False


@dataclass(slots=True)
class BrowserFormFillResult:
    filled_fields: list[str] = field(default_factory=list)
    missing_required_fields: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)


class GenericFormFiller:
    def fill_form(self, page, fields: list[BrowserFormField]) -> BrowserFormFillResult:  # noqa: ANN001
        result = BrowserFormFillResult()
        for form_field in fields:
            locator = self._resolve_locator(page, form_field)
            if locator is None:
                if form_field.required:
                    result.missing_required_fields.append(form_field.key)
                continue

            try:
                self._fill_locator(locator, form_field)
            except Exception as error:  # pragma: no cover - safety belt for live browser issues
                result.issues.append(f"{form_field.key}: {error}")
                continue

            result.filled_fields.append(form_field.key)
        return result

    def submit_form(self, page, submit_selectors: tuple[str, ...]) -> bool:  # noqa: ANN001
        for selector in submit_selectors:
            locator = page.locator(selector)
            if self._locator_exists(locator):
                locator.click()
                wait_for_load_state = getattr(page, "wait_for_load_state", None)
                if callable(wait_for_load_state):
                    wait_for_load_state("networkidle")
                return True
        return False

    def _resolve_locator(self, page, field: BrowserFormField):  # noqa: ANN001
        for selector in field.selectors:
            locator = page.locator(selector)
            if self._locator_exists(locator):
                return locator

        for name_hint in field.name_hints:
            for selector in (
                f'input[name="{name_hint}"]',
                f'textarea[name="{name_hint}"]',
                f'select[name="{name_hint}"]',
                f'input[id="{name_hint}"]',
                f'textarea[id="{name_hint}"]',
                f'select[id="{name_hint}"]',
            ):
                locator = page.locator(selector)
                if self._locator_exists(locator):
                    return locator

        get_by_label = getattr(page, "get_by_label", None)
        if callable(get_by_label):
            for label in field.label_hints:
                locator = get_by_label(label, exact=False)
                if self._locator_exists(locator):
                    return locator

        return None

    def _fill_locator(self, locator, field: BrowserFormField) -> None:  # noqa: ANN001
        if field.field_type == "checkbox":
            if bool(field.value):
                locator.check()
            return

        if field.field_type == "file":
            file_path = Path(str(field.value))
            if not file_path.is_file():
                raise FileNotFoundError(f"Upload file '{file_path}' does not exist.")
            locator.set_input_files(str(file_path))
            return

        locator.fill(str(field.value))

    def _locator_exists(self, locator) -> bool:  # noqa: ANN001
        count = getattr(locator, "count", None)
        if callable(count):
            try:
                return int(count()) > 0
            except Exception:  # pragma: no cover - defensive fallback
                return False

        is_visible = getattr(locator, "is_visible", None)
        if callable(is_visible):
            try:
                return bool(is_visible())
            except Exception:  # pragma: no cover - defensive fallback
                return False

        return locator is not None
