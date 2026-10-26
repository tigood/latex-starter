# 现有样例只读审计

审计日期：2026-10-26（Asia/Shanghai）。参考项目为用户指定的原始 latex-test，严格只读；实际开发目录按本次用户请求采用 `~/myCode/pythonCode/latex-starter`，取代启动文档中的旧目标路径。

- 目标目录起初仅包含四份启动 Markdown 及环境托管的只读控制目录，没有待覆盖的已有代码。四份启动文档保留。
- 参考项目包含 main.tex、三个 sections 文件、references、.vscode/settings.json、build 和一个 Word 文档。没有 .latexmkrc。
- 技术配置：article（12pt、A4）、fontspec、xeCJK；中文正文字体 Noto Serif CJK SC，衬线以外及等宽字体分别为 Noto Sans CJK SC、Noto Sans Mono CJK SC。使用相对路径组织章节与文献资源，并使用 biblatex/Biber。
- VS Code 原设置指定 latexmk (xelatex) recipe、成功后清理及 SyncTeX；没有在项目中显式定义 recipe/tools 或输出目录，所以不能单凭它宣称终端与编辑器完全一致。本工具生成独立完整的项目配置，在临时项目上重新验证。
- 文献库检测到 5 项附件字段与 5 处绝对路径标记。只记录依赖存在性；不复制字段、文献正文或附件路径。原 Word、PDF、论文正文、构建结果均未复制。
- Ubuntu 22.04.5 LTS，Python 3.10.12；XeTeX 0.999993（TeX Live 2022/dev/Debian）、latexmk 4.76、Biber 2.17、VS Code CLI 1.143.0；fc-match 可用，Noto 字体匹配成功，kpsewhich 可找到 Fandol 回退与 biblatex。
- 本机 Jinja2 3.0.3、pytest 6.2.5 已存在。开发安装使用隔离虚拟环境，不升级系统工具。

复用仅限工具链选择、相对路径习惯和字体配置经验。所有生成正文均为新写的短占位段落，示例文献是独立编写的公开书目信息，没有导入用户的真实文献库。

保护验证：实现开始前在 /tmp 保存原项目全部常规文件的 SHA-256 清单，结束时再次比较（结果见 VALIDATION.md）。不在参考目录运行编译、测试、清理或任何写入。
