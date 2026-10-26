# LaTeX Starter 0.1.0

轻量的本地 LaTeX 项目生成器。通过向导或命令行生成中文、英文、中英混排项目，统一使用 XeLaTeX、latexmk 和项目级 VS Code 配置。

需要 Python 3.10+。已在 Ubuntu 22.04 验证；其他系统尚未实测。

## 安装与运行

推荐使用 pipx 为当前用户安装一次。之后在任意目录直接运行命令，无需激活虚拟环境。Ubuntu 如尚未安装 pipx，可手动执行：

```sh
sudo apt update
sudo apt install pipx python3-venv
pipx ensurepath
```

重新打开终端，让 pipx 的应用目录（通常是 `~/.local/bin`）进入 PATH。应用安装使用普通用户权限，不使用 `sudo pip install`。在本仓库根目录安装本地开发版：

```sh
pipx install --editable .
cd /tmp
latex-starter --version
latex-starter list
latex-starter doctor
latex-starter new
```

也可从任意目录执行 `pipx install --editable /path/to/latex-starter`。editable 安装依赖原源码目录，请保留该目录；安装后的命令不依赖当前工作目录。若只想安装固定副本，可在仓库根目录使用 `pipx install .`，或者安装构建好的 wheel：

```sh
pipx install /path/to/latex_starter-0.1.0-py3-none-any.whl
```

目前没有发布到 PyPI，不要依赖 `pipx install latex-starter` 从公开索引取得本项目。

### 升级与卸载

本地 editable 模式的 Python/模板文件修改会立即生效；更新源码后，如果依赖或入口配置发生变化，重建安装环境：

```sh
pipx reinstall latex-starter
latex-starter --version
```

普通本地副本更新后同样可执行 reinstall。更换到新的 wheel 时，使用 `pipx install --force /path/to/new-version.whl`。上述流程使用原本地来源，不要求存在 PyPI 发布。卸载：

```sh
pipx uninstall latex-starter
```

卸载不会删除源码目录或已生成的 LaTeX 项目。

### 故障排查

| 情况 | 处理 |
| --- | --- |
| 找不到 pipx | 按上面的 Ubuntu 步骤安装，或参照 pipx 上游安装说明；无需 sudo pip |
| 找不到 latex-starter | 运行 `pipx list`、`pipx ensurepath`，重开终端；用 `command -v latex-starter` 检查 PATH |
| 命令指向旧虚拟环境 | 退出旧环境，运行 `hash -r`，再检查 `command -v latex-starter` |
| Python 太旧或 venv 创建失败 | 需要 Python 3.10+ 与对应 venv 支持；可用 `pipx install --python python3.10 --editable .` 显式选择 |
| editable 源目录移动/删除 | 从新的源码位置卸载后重新安装 |
| 找不到内置模板 | 重装完整 wheel 或完整源码目录，不要只复制入口脚本；内置资源位于包目录中 |
| doctor 提示缺少编译工具 | 按需自行安装 XeLaTeX、latexmk、Biber/中文字体；生成器与独立程序都不包含 TeX Live |
| 下载失败或校验不一致 | 保留 pip 的校验，检查网络/镜像，必要时为安装指定可信索引；不要关闭校验绕过失败 |

### Python 开发环境

只有开发项目本身才需要虚拟环境；普通使用者采用上面的 pipx 安装方式即可。原开发流程保持可用：

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
latex-starter --help
latex-starter --version
latex-starter list
latex-starter doctor
```

生成源文件只依赖 Jinja2；编译另需本机 XeLaTeX、latexmk、相应 TeX 宏包，启用文献时需 biblatex 和 Biber。中文优先使用 Noto Serif/Sans/Sans Mono CJK SC，缺失时源码回退到 TeX Live 的 Fandol 字体。工具不会安装系统包或字体。

## 创建项目

交互式向导：

```sh
latex-starter new
```

脚本模式必须提供项目名并使用 `--yes`，其余默认值来自模板描述文件。输出目录是父目录，项目名中的空白变成连字符，英文字母转成小写；支持中文项目名和含空格的父目录。

```sh
latex-starter new my-paper --yes --template academic-article \
  --language zh --structure split --bibliography \
  --title '中文论文 & 示例' --author '作者' --output-dir ./projects --compile
latex-starter new english-notes --yes --template notes \
  --language en --structure single --no-bibliography
latex-starter new preview --yes --dry-run --compile --open
```

`--dry-run` 会显示配置和完整文件清单，不写入、不编译、不启动编辑器。已有非空目录或符号链接目标会被拒绝；允许使用已有空目录。传入标题、作者、机构会作为普通文本进行 LaTeX 转义。

| 模板 | 默认结构 | 默认启用功能 |
| --- | --- | --- |
| academic-article | split | 参考文献、图片与表格示例 |
| course-report | split | 图片与表格、代码、目录、附录；含报告封面 |
| notes | single | 简洁正文 |

所有模板支持 `zh/en/mixed`、`single/split`，以及以下功能开关（每项都有 `--no-…` 形式）：

```text
--bibliography
--figures-tables-examples
--code-listing-example
--table-of-contents
--appendix
--compile
--open
```

另外支持 `--title`、`--author`、`--institution`、`--output-dir`。不指定 `--yes` 时仅询问缺失参数，并在完整摘要后请求确认。`--open` 仅在本次首次编译成功后打开 VS Code，因此通常与 `--compile` 一起使用。两者默认关闭。

## 编译与诊断

```sh
latex-starter doctor --language zh --bibliography
cd projects/my-paper
latexmk -norc -r .latexmkrc -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -synctex=1 -outdir=build main.tex
```

PDF 位于 `build/main.pdf`。首次编译的命令输出保存在 `build/latex-starter-compile.log`，TeX 日志位于 `build/main.log`。源码、日志均在失败后保留。单独生成成功不表示环境完整或编译成功，CLI 分别报告三个状态。

VS Code 安装推荐的 LaTeX Workshop 扩展，执行 `latex-starter (XeLaTeX)` recipe。终端和编辑器采用同一组引擎、诊断、SyncTeX、输出目录参数及 `.latexmkrc`；`-norc` 跳过全局初始化配置。`-cd` 让编辑器命令从根文件目录编译。不修改用户级 VS Code 设置。

`doctor` 为每项输出 `OK/WARN/MISSING`。仅中文项目检查 CJK 字体；`fc-match` 缺失会尝试 `kpsewhich` 验证 Fandol，二者都缺失时明确标记无法自动核验。Biber 对无文献项目为可选依赖。

退出码：`0` 表示命令/创建成功（缺少编译工具仍保留成功创建），`1` 表示诊断不可用、实际编译失败或编辑器启动失败，`2` 表示配置、路径、渲染或文件系统错误，输入中断为 `130`。请同时阅读状态文本；没有请求编译、缺少编译工具时不会声称编译成功。

## 开发与验证

```sh
python -m pytest -q
LATEX_STARTER_INTEGRATION=1 python -m pytest -q
python -m pip wheel . --no-deps -w /tmp/latex-starter-wheels
```

集成测试默认跳过；启用后会在 pytest 临时目录真实编译，缺少工具时明确跳过。普通测试不需要 TeX Live。

### wheel 与实验性独立程序

分发工具放在可选的开发 extra `distribution` 中，不属于应用运行依赖，也不改变原来的 `.[dev]` 流程：

```sh
python -m pip install -e ".[dev,distribution]"
python -m build --wheel
python scripts/build_standalone.py
```

构建脚本会从源码路径收集包及模板，生成宿主平台的独立程序，并在非项目目录实际运行 help、version、list 和三个模板创建测试。Linux x86_64 输出是 `dist/experimental/linux-x86_64/latex-starter`；Windows 原生构建输出对应目录下的 `latex-starter.exe`。这是可选实验产物，Linux 构建不等于 Windows 构建；目前仅验证 Linux x86_64。独立程序包含 Python/Jinja2 和内置资源，**不包含 XeLaTeX、latexmk、Biber、字体或完整 TeX Live**。

完整分发验证步骤、平台限制和真实结果见 [分发说明](docs/distribution.md)。其他文档：[架构](docs/architecture.md)、[模板协议](docs/templates.md)、[样例审计](docs/EXISTING_SAMPLE_AUDIT.md)、[原版验证记录](docs/VALIDATION.md) 和 [路线图](docs/roadmap.md)。

0.1.0 不包含在线模板、自动依赖安装、GUI、Word 导出或 Zotero 导入。只支持随包提供的受信任本地模板。原始四份启动需求文档保留为历史输入，其中旧目标路径不适用于当前仓库；实际位置为 `~/myCode/pythonCode/latex-starter`。
