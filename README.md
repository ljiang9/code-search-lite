# code-search-lite

零依赖的轻量级代码库搜索 CLI。遍历目录下的源码文件（自动跳过 `.git`、`node_modules`、`__pycache__` 等），支持三种检索方式，并在函数级定位命中位置、展示上下文。

## 功能

- **标识符搜索**：按词边界精确匹配（`\bfoo\b`），不会误伤子串。
- **正则搜索**：传入任意 Python 正则表达式。
- **近似文本搜索**：用 `difflib.SequenceMatcher` 做行级模糊匹配，容忍拼写偏差。
- **函数级定位**：对每条命中向上回溯，找到所属的最近 `def/class/function/func` 块。
- **上下文展示**：每条命中前后各打印 N 行源码。

## 快速开始

```bash
python -m code_search /path/to/project --ident "calculate_total"
python -m code_search /path/to/project --regex "def\s+\w+" --func
python -m code_search /path/to/project --fuzzy "sum all items" --sim 0.6
```

## 无 API Key 如何运行

本工具**完全离线、零网络调用**，不需要任何 API Key。直接运行即可。

## 运行测试

```bash
python -m unittest discover -s tests -v
```

## License

MIT © ljiang9
