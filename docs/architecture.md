# 架构

数据流：argparse / wizard → make_config → catalog 校验 → renderer 内存渲染 → filesystem 暂存与排他落盘 → environment 诊断 → 可选 compiler → 可选 VS Code。

| 模块 | 职责 |
| --- | --- |
| cli.py | 参数路由、摘要、确认、阶段与状态报告 |
| wizard.py | 仅收集缺失答案，不写文件 |
| config.py | ProjectConfig、默认值合并、项目名和文本校验 |
| catalog.py | schema 1、模板发现、有限条件、源与目标路径校验 |
| renderer.py | 沙箱 Jinja2、StrictUndefined、逐字符 LaTeX 转义、元数据 |
| filesystem.py | 目标保护、同父目录暂存、排他创建与失败回滚 |
| environment.py | 有时限的命令探测、精确字体匹配、Fandol 回退检查 |
| compiler.py | 统一 BUILD_FLAGS、已知编译命令、退出码/PDF/日志判定、编辑器启动 |

模板资源放在 Python 包内部，确保安装 wheel 后也能发现。`_shared/files.json` 显式登记通用文件；每个模板目录登记正文文件，并使用共享 Jinja 片段。共享编译参数从 compiler 传给 renderer，避免 VS Code 与终端参数漂移。使用 `<< >>` 插入变量，避免与 LaTeX 花括号冲突；控制语句仍用 Jinja 的 `{% %}`。依据：[Jinja 官方 API](https://jinja.palletsprojects.com/en/stable/api/)，本机 Jinja 3.0.3 已实测相关接口。

清单条件只允许 feature 布尔值及 language/structure 枚举，既不 eval 也不执行钩子。模板来源仅限随包资源；沙箱并非支持不受信任模板的承诺。用户文本不重新解释为 Jinja 或 LaTeX。

落盘前所有渲染在内存完成，随后暂存完整文件，使用 `xb` 排他创建最终文件。失败只回滚本次创建的文件和空目录，不递归删除用户目录，不覆盖并发出现的同名文件。不提供对恶意并发修改目录的跨进程事务保证。首次编译失败不回滚已创建项目。

外部调用都用参数列表和超时，无 shell=True。latexmk 作为上游构建驱动会按其正常行为调用 XeLaTeX/Biber；生成的 XeLaTeX 配置使用 -no-shell-escape。执行时跳过全局 latexmk 初始化文件，只加载生成项目的 .latexmkrc。

构建成功要求退出码为 0 且 build/main.pdf 非空。生成、诊断与编译分别报告；环境预检查无法完全证明所有 TeX 宏包可用，实际编译才验证这一点。
