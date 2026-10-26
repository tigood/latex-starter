# 安装与分发

本次仅增加安装说明、可选分发工具和回归验证，不调整 CLI、向导、配置模型、安全检查、生成逻辑或编译流程。项目元数据仍为 0.1.0，本次分发变更记录在 CHANGELOG 的 Unreleased 中；未向 PyPI 或 GitHub Release 发布。

## 审计与最小改动

修改前执行了 `git status --short`，当前环境的 `.git` 是空只读目录，命令报告“不是 git 仓库”，无法判断 Git 索引状态。因此先将 55 个现有文件复制并记录 SHA-256 到 `/tmp/latex-starter-distribution-baseline-82tnbc9p`，再修改已知文件。最终比较确认原有 src/ 下代码与模板、原有五份测试文件完全未变，没有删除或改写测试。

原 pyproject 已正确声明 Python >=3.10、Jinja2 运行依赖和 `latex-starter = latex_starter.cli:main` 入口。本次补充分类/关键词和可选开发 extra `distribution`，保留原 dev extra。构建时发现旧的许可 table 格式弃用警告，已改为标准 SPDX `MIT`，显式声明 LICENSE，并将支持该格式的构建后端下限设为 setuptools 77；不增加应用运行依赖。新增 build、pipx、PyInstaller 均在 distribution extra 中，普通安装仍只需要 Jinja2 及其传递依赖。干净 wheel 环境额外验证没有安装 PyInstaller。

模板一直位于 Python 包内部，资源清单已覆盖三个 template.json、共享文件清单、所有 .j2 片段、示例 .bib 和其他资源。加载器使用包模块的 `__file__` 相对目录，而不是 cwd。对当前的源码、editable、wheel 解包安装和 PyInstaller 实体文件布局，这种方式已经适用，因此没有迁移资源目录或引入新加载抽象。测试同时用 importlib.resources 验证可访问性，检查 wheel 的完整资源清单，并从其他目录实际生成与编译。

PyInstaller 构建脚本通过 `--collect-data latex_starter` 保持包目录结构，因此现有加载器同样适用。这与 [PyInstaller 运行时数据路径说明](https://pyinstaller.org/en/stable/runtime-information.html) 一致。zipimport/直接运行未解包 wheel 不属于支持方式。

## 普通用户安装与维护

Ubuntu 手动准备 pipx（具体仓库可用版本由发行版决定）：

```sh
sudo apt update
sudo apt install pipx python3-venv
pipx ensurepath
```

重新打开终端后，在源码根目录执行：

```sh
pipx install --editable .
```

随后可以在任意目录直接使用 `latex-starter new/list/doctor`，不需要激活开发虚拟环境。pipx 使用隔离应用环境并暴露命令，见 [pipx 官方项目说明](https://github.com/pypa/pipx)。本次还实际检查了安装版本的 `pipx install --help` 和 `pipx reinstall --help`。

本地维护：更新源码后，Python 与模板修改直接生效；依赖、入口或元数据改变后运行 `pipx reinstall latex-starter`。不需要修改源码的固定副本可用 `pipx install .`。安装 wheel 可用 `pipx install /path/to/latex_starter-0.1.0-py3-none-any.whl`；换新 wheel 时用 `pipx install --force /path/to/new-version.whl`。卸载为 `pipx uninstall latex-starter`，不会删除源码和生成的项目。

本次测试设置临时 PIPX_HOME、PIPX_BIN_DIR、PIPX_MAN_DIR、XDG 缓存/状态目录，并仅给测试子进程设置 PATH，没有执行用户级 ensurepath，也没有永久安装到用户 ~/.local/bin。真正安装到日常终端请执行上述命令。无需 sudo pip；程序不修改全局 VS Code 或系统 LaTeX 配置。更多排查见 README。

## wheel 构建

在开发虚拟环境中：

```sh
python -m pip install -e ".[dev,distribution]"
python -m build --wheel
```

产物是 `dist/latex_starter-0.1.0-py3-none-any.whl`。该 wheel 的纯 Python 标签不等于所有操作系统的 LaTeX/字体集成已测试；当前实际验证平台是 Ubuntu 22.04 x86_64、Python 3.10.12。

## 可选 PyInstaller 构建

```sh
python scripts/build_standalone.py
```

脚本基于自身位置计算源码路径，不硬编码开发者绝对路径；`--output-dir` 可指定产物目录。使用宿主操作系统/CPU 标记输出目录，构建 onefile 控制台程序，然后在临时非项目目录运行 --help、--version、list 和三模板创建。构建失败或 smoke test 失败会以非零状态退出。

- Linux x86_64：`dist/experimental/linux-x86_64/latex-starter`，本机已成功构建并测试。
- Windows：必须在对应 Windows 环境原生构建，生成对应目录的 `latex-starter.exe`；本次没有构建或验证。
- macOS、其他 CPU、其他 Linux/更旧 glibc 环境：没有验证，不承诺兼容。

独立程序约 7.1 MiB，包含 Python 运行时、Jinja2 与内置模板；不包含 XeLaTeX、latexmk、Biber、中文字体、TeX Live 或 VS Code，doctor 仍检查用户本机环境。测试证明生成和编译调用成功，但产物仍为实验性质，未签名、未做跨平台发布验证、未作为正式 Release 发布。构建中间 spec 和缓存位于被忽略的 dist 目录，不应把它们作为可移植配置提交；以源码构建脚本为准。

## 自动验证与真实结果

2026-10-26，Ubuntu 22.04.5 / Python 3.10.12 / PyInstaller 6.22.3 / pipx 1.17.12 / Jinja2 3.1.6。完整安装测试使用预下载 wheelhouse 离线执行；本机镜像的一次 pip 下载校验失败被 pip 拒绝，随后从官方 PyPI 重新下载并保留校验，没有使用失败文件或绕过校验。

```sh
.venv/bin/python -m pytest -q
# 120 passed, 35 skipped in 1.66s

LATEX_STARTER_DISTRIBUTION=1 \
LATEX_STARTER_INTEGRATION=1 \
LATEX_STARTER_WHEELHOUSE=/tmp/latex-starter-dist-wheelhouse \
LATEX_STARTER_EXECUTABLE="$PWD/dist/experimental/linux-x86_64/latex-starter" \
.venv/bin/python -m pytest -q --basetemp=/tmp/latex-starter-distribution-validation-final
# 155 passed in 65.82s（0 failed, 0 skipped）
```

其中原有 122 项全部保留并执行，新增 33 项：4 项包资源/cwd 测试，以及 29 项分发测试。默认跳过的 35 项为原有 6 项真实编译与新增 29 项分发测试。

wheel 测试创建不继承系统 site-packages 的全新 venv，安装 wheel 和运行依赖，确认导入来自新环境。pipx 测试使用新建临时用户目录执行 editable 安装，另建环境验证 reinstall/uninstall。三种安装形态均通过 PATH 中的命令名，从非源码目录执行 --help、--version、list、doctor，生成三个模板，验证功能开启与关闭、文献文件、章节结构和特殊字符转义。

三种形态均真实编译中文 split + Biber 和英文 single 无文献项目，检查 PDF 签名与中文文献 .bbl。加上原有六项真实编译，共执行十二项编译测试。PDF 和日志位于 `/tmp/latex-starter-distribution-validation-final/test_installed_real_compile_*/compiled/build/`；原有编译测试输出位于同一测试根目录相应 test_real_compile_* 子目录。

CI 保留 Python 3.10–3.14 单元矩阵，新增 Ubuntu 22.04 的 wheel/pipx/独立程序分发 job；没有安装 TeX 的 CI 会跳过实际编译项。本次未触发托管 GitHub Actions。

当前未发现已验证形态中的模板资源问题。待验证项为 Windows/macOS/其他 Linux 和 CPU 的原生构建、用户实际 shell 的 PATH 配置及正式发布流程。现有 0.1.0 的 GUI 触发编译人工复核限制仍适用。
