# 0.1.0 验证记录

日期：2026-10-26（Asia/Shanghai）。开发及文档均位于用户指定的 `~/myCode/pythonCode/latex-starter`。原始四份启动文档保持原样，其旧目标路径仅为历史输入。

## 环境与安装

Ubuntu 22.04.5、Python 3.10.12、XeTeX 0.999993、latexmk 4.76、Biber 2.17、Noto CJK 与 Fandol 均可用。系统 setuptools 59.6.0 对本项目 pyproject 元数据支持不足，初次安装未正确识别；已清理本次产生的 UNKNOWN 元数据，随后仅在项目 `.venv` 中更新构建依赖，使用独立环境完成安装。

最终虚拟环境：Jinja2 3.1.6、pytest 9.1.1、setuptools 84.2.1；系统 setuptools 仍为 59.6.0，没有更新系统包、字体、TeX Live 或编辑器扩展。早期测试另验证了系统 Jinja2 3.0.3 与 pytest 6.2.5。最终完整测试以虚拟环境版本为准。

以下安装与 CLI 命令已实际运行（命令中的 python/latex-starter 均为项目 `.venv/bin/` 对应程序）：

```sh
python -m pip install -e ".[dev]"
latex-starter --help
latex-starter --version
latex-starter list
latex-starter doctor --language zh --bibliography
python -m pip check
```

均成功；doctor 的必需项均为 OK；pip check 无损坏依赖。未提交或推送 Git。

## 自动化测试

```sh
.venv/bin/python -m pytest -q
# 116 passed, 6 skipped in 1.41s

LATEX_STARTER_INTEGRATION=1 .venv/bin/python -m pytest -q --basetemp=/tmp/latex-starter-validation/pytest-final
# 122 passed in 18.02s（0 failed, 0 skipped）
```

覆盖三个模板 × 三种语言 × 两种结构 × 文献开关共 36 组生成组合，独立功能开关、标题/作者/机构转义、交互及参数模式、dry-run 无副作用、非空目录与符号链接保护、描述文件/schema/条件校验、路径穿越、暂存失败回滚、工具缺失、字体精确匹配及 Fandol 回退、编译成功/失败/超时/PDF 缺失判定。

六个真实编译测试的 PDF 如下，所有路径均在临时目录；测试过程中没有在原始样例内运行编译。包含特殊字符标题、含空格与中文的输出父目录。

| 实际场景 | PDF |
| --- | --- |
| 中文论文、split、Biber | [main.pdf](</tmp/latex-starter-validation/pytest-final/test_real_compile_academic_art0/父目录 with spaces/test/build/main.pdf>) |
| 英文论文、single、无文献 | [main.pdf](</tmp/latex-starter-validation/pytest-final/test_real_compile_academic_art1/父目录 with spaces/test/build/main.pdf>) |
| 中文论文、single、无文献 | [main.pdf](</tmp/latex-starter-validation/pytest-final/test_real_compile_academic_art2/父目录 with spaces/test/build/main.pdf>) |
| 课程报告、mixed、split、Biber | [main.pdf](</tmp/latex-starter-validation/pytest-final/test_real_compile_course_repor0/父目录 with spaces/test/build/main.pdf>) |
| 中文笔记、single | [main.pdf](</tmp/latex-starter-validation/pytest-final/test_real_compile_notes_zh_sin0/父目录 with spaces/test/build/main.pdf>) |
| 展开后的 LaTeX Workshop recipe、中文论文、Biber | [main.pdf](</tmp/latex-starter-validation/pytest-final/test_actual_workshop_recipe_co0/with spaces/recipe/build/main.pdf>) |

另通过已安装 CLI 生成并编译了 [中文文献项目](/tmp/latex-starter-validation/zh-bib/build/main.pdf)。在真实 PTY 中运行 `latex-starter new`，逐项完成 notes/en/single 向导与最终确认，成功生成 `/tmp/latex-starter-validation/interactive-smoke`，按选择跳过编译和编辑器启动。

## 打包与源码外验证

```sh
.venv/bin/python -m pip wheel . --no-deps --no-build-isolation --no-cache-dir -w /tmp/latex-starter-wheels
.venv/bin/python -m pip install --target /tmp/latex-starter-wheel-check --no-deps --no-index --no-cache-dir /tmp/latex-starter-wheels/latex_starter-0.1.0-py3-none-any.whl
cd /tmp
PYTHONPATH=/tmp/latex-starter-wheel-check python3 -m latex_starter list
PYTHONPATH=/tmp/latex-starter-wheel-check python3 -m latex_starter new en-wheel --yes --language en --structure single --no-bibliography --compile --output-dir /tmp/latex-starter-validation
```

成功验证导入文件来自 wheel 安装目录、三模板均可发现、共享/条件模板资源完整，以及源码目录外真实编译。独立英文成品：[main.pdf](/tmp/latex-starter-validation/en-wheel/build/main.pdf)。wheel 文件为 `/tmp/latex-starter-wheels/latex_starter-0.1.0-py3-none-any.whl`。所有 PDF 均为本次生成样例，不是复制原项目产物。

## 编译一致性与限制

终端与 LaTeX Workshop 的编译参数由同一 BUILD_FLAGS 生成，均使用 XeLaTeX、-norc、项目 .latexmkrc、SyncTeX、nonstopmode、halt-on-error、file-line-error 和 build 输出目录。实际展开生成 recipe 的 `%DIR%/%DOC%` 占位符后，从项目外目录运行，并验证 PDF/Biber 结果均在项目 build/ 中。文献项目实际生成含示例引用的 .bbl，最终 TeX 日志没有 undefined citations。

本机已安装 LaTeX Workshop 10.20.0，其配置 schema 确认上述占位符。未通过 VS Code 图形界面点击 recipe，也未自动打开用户编辑器；当前执行环境禁止在 VS Code 用户日志目录写入，CLI 扩展清单查询虽成功但带只读日志错误。命令级一致性已经实测，GUI 触发与 PDF 预览仍待人工复核。

仅 Ubuntu 22.04 / Python 3.10 在本机真实测试；GitHub Actions 已配置 Python 3.10–3.14，尚未在托管 CI 执行。项目未自动发布，其他系统兼容性尚未实测。临时目录内 PDF 不应作为长期归档。

## 原始样例与内容保护

开发前后比较原始 latex-test 全部常规文件：12 个 SHA-256 与完整文件清单一致。没有新增、修改、删除或重命名原始文件。未复制私人论文正文、文献字段、附件路径、Word、PDF 或构建产物；运行时代码及模板扫描未发现家目录绝对路径。样例文献独立编写，只含公开的 TeXbook 书目信息。构建验证产物留在 /tmp，源码仓库中的虚拟环境和安装元数据由 .gitignore 排除。
