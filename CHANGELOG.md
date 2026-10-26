# Changelog

## Unreleased — 安装与分发

- 文档新增 pipx 本地安装、源码/wheel 升级与卸载、Ubuntu PATH 排查。
- 将 MIT 许可元数据更新为 SPDX 格式并显式包含 LICENSE，构建后端最低 setuptools 77。
- 新增 distribution 可选开发依赖及 Linux/Windows 原生 PyInstaller 构建脚本，默认开发流程不变。
- 新增包资源、干净 wheel、pipx、独立程序及源码目录外调用的回归测试。
- 核心生成、交互、安全检查和编译流程保持不变；独立程序仅作实验产物。

## 0.1.0 — 2026-10-26

- 新增 list、doctor、交互与参数模式 new、dry-run。
- 三个描述文件驱动模板，支持三种语言、两种结构和五项功能开关。
- 项目级 XeLaTeX/latexmk/Biber 与 LaTeX Workshop 配置。
- 路径校验、暂存与排他写入、文本转义、首次编译日志及状态报告。
- pytest 测试、可选真实编译集成测试和 Ubuntu CI。
