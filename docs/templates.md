# 模板协议（schema 1）

内置模板位于 `src/latex_starter/templates/<id>/`，每个目录包含 template.json 和 files/。模板描述必须声明以下字段，不接受未知字段：

```json
{
  "schema_version": 1,
  "id": "my-template",
  "name": "示例模板",
  "description": "用途说明",
  "supported_languages": ["zh", "en", "mixed"],
  "supported_structures": ["single", "split"],
  "default_language": "zh",
  "default_structure": "split",
  "default_engine": "xelatex",
  "features": {
    "bibliography": true,
    "figures_tables_examples": true,
    "code_listing_example": true,
    "table_of_contents": true,
    "appendix": true
  },
  "defaults": {
    "bibliography": false,
    "figures_tables_examples": false,
    "code_listing_example": false,
    "table_of_contents": false,
    "appendix": false
  },
  "files": [
    {"source": "files/main.tex.j2", "target": "main.tex"},
    {"source": "files/section.tex.j2", "target": "sections/example.tex", "when": {"structure": "split"}}
  ]
}
```

id 必须与目录名一致，使用小写字母起始及小写字母、数字、连字符。features 是能力声明，defaults 是启用状态，两者必须完整声明五个布尔值；不允许默认启用不支持的功能。语言、结构默认值必须属于对应支持列表。schema 1 只支持 xelatex。

source 相对当前模板目录，target 相对生成项目目录。清单拒绝绝对路径、Windows 盘符、反斜线、空组件、`.`、`..`、符号链接逃逸、重复目标和文件/目录冲突。when 只允许 language/structure 枚举及上述五项布尔值，各条件按 AND 合并。`.latex-starter.json` 是程序保留目标。

`_shared/files.json` 登记所有模板共有的项目配置；其 source 相对 `_shared/`。仅清单文件落盘；没有登记的模板片段可以被 include，但不会被复制。`.j2` 文件使用 Jinja 渲染，其余文件逐字节复制。新增模板通常只需要新增描述和 files/，CLI 自动发现；不需要修改向导分支。若直接复用共享 document 片段，参照三个内置模板的 main 与章节命名。

变量包含 title、author、institution、language、structure、template、各功能开关、chinese（zh/mixed 为真）等。所有普通用户文本输出到 TeX 必须使用 `<< title | tex >>` 一类写法；JSON 字段使用 json 过滤器。不要将用户文本当作原始 LaTeX。

启用文献才生成示例 references.bib 和引用命令。split 模式才生成章节文件；single 模式把同一章节片段内联。每个模板可自由定义布局，不依赖真实论文或用户文献。添加模板后运行整个测试套件与适用的真实编译测试，并检查 wheel 中包含新增资源。
