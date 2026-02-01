# FunctionSpec 验证工具

用于验证 `function.yaml` 是否符合 FunctionSpec v0.1 规范。

## 安装依赖

```bash
pip install pyyaml
```

## 使用方法

### 验证单个函数

```bash
python scripts/validate_spec.py examples/validate_email
```

### 验证所有函数

```bash
python scripts/validate_spec.py --all
```

### JSON 输出（用于CI/CD）

```bash
python scripts/validate_spec.py examples/validate_email --json
```

### 严格模式（警告视为错误）

```bash
python scripts/validate_spec.py examples/validate_email --strict
```

## 验证规则

### MUST（必需）- 不通过则无效

- `spec_version`: 必须是 "0.1"
- `id`: 点分命名空间格式（如 `validation.email.basic`）
- `version`: 语义化版本（如 `1.0.0`）
- `name`: 人类可读的函数名
- `description`: ≤1000字符的描述
- `language.name`: 编程语言
- `entrypoint.kind`: inline/file/container/wasm
- `signature.inputs/outputs`: 输入输出签名（map格式）
- `semantics.deterministic`: 是否确定性
- `semantics.side_effects`: 副作用列表
- `tests.framework`: 测试框架
- `tests.cases`: 至少1个测试用例

### SHOULD（建议）- 警告但不失败

- `license`: SPDX标识（如 MIT, Apache-2.0）
- `authors`: 作者信息列表
- `entrypoint.symbol`: 入口函数符号
- `semantics.security`: 安全声明
- `examples`: 使用示例
- `provenance`: 溯源信息

### MAY（可选）- 信息提示

- `semantics.resource_profile`: 资源画像
- `semantics.concurrency`: 并发安全
- `dependencies`: 依赖声明
- `quality`: 质量指标
- `lifecycle`: 生命周期
- `extensions`: 扩展字段

## 类型映射

FunctionSpec 标准类型 vs Python 类型：

| FunctionSpec | Python |
|--------------|--------|
| `string` | `str` |
| `integer` | `int` |
| `number` | `float` |
| `boolean` | `bool` |
| `object` | `dict` |
| `array` | `list` |
| `bytes` | `bytes` |
| `file` | - |
| `path` | `pathlib.Path` |
| `any` | `Any` |

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: Validate Functions

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install pyyaml
      - run: python scripts/validate_spec.py --all --strict
```

### 本地预提交钩子

```bash
#!/bin/bash
# .git/hooks/pre-commit

python scripts/validate_spec.py --all --strict
if [ $? -ne 0 ]; then
    echo "Function validation failed!"
    exit 1
fi
```

## 退出码

- `0`: 验证通过
- `1`: 验证失败（有 ERROR 或严格模式下的 WARNING）

## 示例输出

```
============================================================
📋 Validating: examples/validate_email/function.yaml
============================================================
✅ All checks passed!

============================================================
📋 Validating: examples/my_function/function.yaml
============================================================

❌ ERRORS (1):
   [semantics.deterministic] Missing required: semantics.deterministic
   💡 Add: semantics: { deterministic: true }

⚠️  WARNINGS (2):
   [license] Missing recommended field: license
   💡 Add: license: "MIT" (or Apache-2.0, etc.)
   [provenance] Missing recommended field: provenance
   💡 Add creation/update timestamps

------------------------------------------------------------
Summary: 1 errors, 2 warnings, 0 infos
Status: ❌ INVALID
```
