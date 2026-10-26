"""Collect answers only; no file writes or process launches."""
from __future__ import annotations

from .catalog import FEATURES, Template


def ask(prompt: str, default: str = "", choices: tuple[str, ...] = ()) -> str:
    while True:
        suffix = f" ({'/'.join(choices)})" if choices else ""
        answer = input(f"{prompt}{suffix} [{default}]: ").strip() or default
        if not choices or answer in choices:
            return answer
        print("Choose one of: " + ", ".join(choices))


def yes_no(prompt: str, default: bool = False) -> bool:
    return ask(prompt, "y" if default else "n", ("y", "n")) == "y"


def collect(values: dict, templates: dict[str, Template]) -> tuple[dict, Template]:
    values = dict(values)
    if not values.get("template"):
        for template in templates.values():
            print(f"  {template.id}: {template.name} — {template.description}")
        values["template"] = ask("Template / 模板", "academic-article", tuple(templates))
    template = templates[values["template"]]
    if values.get("language") is None:
        values["language"] = ask("Language / 语言", template.default_language, template.supported_languages)
    if values.get("structure") is None:
        values["structure"] = ask("Structure / 结构", template.default_structure, template.supported_structures)
    for feature in FEATURES:
        if values.get(feature) is None and template.features[feature]:
            values[feature] = yes_no(feature.replace("_", " "), template.defaults[feature])
    if not values.get("project_name"):
        values["project_name"] = ask("Project name / 项目名")
    for key, label, default in (("title", "Title / 标题", values["project_name"]),
                                ("author", "Author / 作者", ""),
                                ("institution", "Institution / 机构", ""),
                                ("output_dir", "Output parent / 输出父目录", ".")):
        if values.get(key) is None:
            values[key] = ask(label, default)
    if not values.get("dry_run"):
        if values.get("compile") is None:
            values["compile"] = yes_no("Compile once / 首次编译")
        if values.get("open_editor") is None:
            values["open_editor"] = yes_no("Open VS Code after a successful build / 编译成功后打开")
    return values, template
