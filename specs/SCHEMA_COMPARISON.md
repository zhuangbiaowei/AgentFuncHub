# FunctionSpec 与 metadata-schema 对比分析

## 概述

项目中有两份函数规范：
1. **FunctionSpec.md** (specs/FunctionSpec.md) - 新的 YAML 格式规范
2. **metadata-schema.md** (specs/metadata-schema.md) - 旧的 JSON Schema 规范

**结论**: FunctionSpec 是 metadata-schema 的**演进版本**，应当废弃 metadata-schema，全面采用 FunctionSpec。

---

## 关键差异对比

| 特性 | FunctionSpec (新) | metadata-schema (旧) | 说明 |
|------|-------------------|---------------------|------|
| **文件格式** | YAML | JSON | YAML 更易读写 |
| **文件名** | `function.yaml` | `manifest.json` | 已统一为 function.yaml |
| **spec_version** | ✅ `"0.1"` | ❌ 无 | 新增版本控制 |
| **id 格式** | 点分命名空间 `validation.email.basic` | UUID `func-001-xxx` | 新格式更语义化 |
| **代码位置** | `entrypoint` (支持 file/inline/container/wasm) | `code.source` (仅inline) | 新格式更灵活 |
| **语义声明** | ✅ `semantics` (deterministic, side_effects, security) | ⚠️ 仅有 `security` | 新增关键字段 |
| **纯度声明** | ✅ `purity` | ❌ 无 | 新增 |
| **并发安全** | ✅ `concurrency` | ❌ 无 | 新增 |
| **资源画像** | ✅ `resource_profile` | ⚠️ `performance` (简化) | 更详细 |
| **测试框架** | ✅ `tests.framework` | ❌ 仅有 `test_cases` | 明确测试框架 |
| **溯源信息** | ✅ `provenance` | ❌ 仅有 `created_at` | 更完整 |
| **生命周期** | ✅ `lifecycle` | ❌ 无 | 新增 |
| **质量指标** | ✅ `quality` | ❌ 无 | 新增 |
| **扩展机制** | ✅ `extensions` | ❌ 无 | 新增 |

---

## 字段映射表

旧字段 (manifest.json) → 新字段 (function.yaml)

| 旧字段 | 新字段 | 变化说明 |
|--------|--------|----------|
| `function_id` | `id` | UUID → 点分命名空间 |
| `name` | `name` + `entrypoint.symbol` | 分离标识符和入口符号 |
| `display_name` | `name` | 合并 |
| `description` | `description` | 不变 |
| `language` | `language.name` | 嵌套到对象 |
| `version` | `version` | 不变 |
| `signature.inputs` (array) | `signature.inputs` (map) | 数组→字典，key为参数名 |
| `signature.outputs` (array) | `signature.outputs` (map) | 同上 |
| `code.source` | `entrypoint.code` (inline) 或 `src/` (file) | 更灵活 |
| `code.hash/line_count/complexity` | ❌ 移除 | 由运行时计算 |
| `test_cases` | `tests.cases` | 嵌套到 tests 对象 |
| `dependencies` | `dependencies.packages` | 嵌套，结构更明确 |
| `tags` | `tags` | 不变 |
| `categories` | `keywords` 或 `use_cases` | 建议用 keywords |
| `usage_scenarios` | `use_cases` | 重命名 |
| `performance` | `semantics.resource_profile` | 移动位置 |
| `security` | `semantics.security` | 嵌套到 semantics |
| `author` | `authors` (array) | 支持多作者 |
| `license` | `license` | 不变 |
| `created_at/updated_at` | `provenance.created_at/updated_at` | 移动位置 |
| `stats` | ❌ 移除 | 运行时统计，不应在spec中 |

---

## 废弃 metadata-schema 的理由

### 1. **功能缺失**
- 无语义声明 (deterministic, side_effects, purity)
- 无并发安全声明
- 无生命周期管理
- 无溯源信息

### 2. **结构局限**
- 代码必须inline，不支持文件分离
- 不支持多入口 (container/wasm)
- 输入输出用数组而非字典，不便于引用

### 3. **可扩展性差**
- 无扩展机制
- 无 spec_version 版本控制

---

## 协调方案

### 方案 A: 完全废弃 metadata-schema（推荐）

1. **删除** `specs/metadata-schema.md`
2. **更新** `specs/FunctionSpec.md` 作为唯一规范
3. **更新** 所有函数示例（已完成20/25）
4. **更新** 后端代码以支持 FunctionSpec
5. **更新** 文档引用

**优点**: 单一规范，减少混淆  
**缺点**: 需要修改已迁移的代码

### 方案 B: 保留 metadata-schema 作为子集

将 metadata-schema 重命名为 `FunctionSpec-JSON.md`，声明为：
> "FunctionSpec 的 JSON 序列化子集，用于运行时API交换"

**优点**: 向后兼容  
**缺点**: 维护两套规范，容易不一致

---

## 建议操作

### 立即执行
1. ✅ 移动 FunctionSpec.md 到 specs/（已完成）
2. 🗑️ **删除** metadata-schema.md
3. 📝 **更新** README.md 指向正确的规范文件

### 短期执行
4. **修复** 剩余 5 个函数的迁移
5. **更新** 后端服务读取 function.yaml
6. **创建** FunctionSpec 验证工具

### 长期规划
7. **完善** FunctionSpec v0.2（根据实际使用反馈）
8. **创建** 规范变更日志

---

## FunctionSpec 验证清单

一个有效的 `function.yaml` 必须满足：

### MUST（必需）
- [ ] `spec_version: "0.1"`
- [ ] `id` - 点分命名空间格式
- [ ] `version` - SemVer
- [ ] `name` - 人类可读
- [ ] `description` - ≤1000字符
- [ ] `language.name`
- [ ] `entrypoint.kind` (file/inline/container/wasm)
- [ ] `signature.inputs` (map)
- [ ] `signature.outputs` (map)
- [ ] `semantics.deterministic` (bool)
- [ ] `semantics.side_effects` (array)
- [ ] `tests.framework`
- [ ] `tests.cases` (至少1个)

### SHOULD（建议）
- [ ] `license` - SPDX标识
- [ ] `authors`
- [ ] `semantics.security`
- [ ] `examples`
- [ ] `provenance`

### MAY（可选）
- [ ] `semantics.resource_profile`
- [ ] `semantics.concurrency`
- [ ] `dependencies`
- [ ] `quality`
- [ ] `lifecycle`
- [ ] `extensions`

---

## 后端迁移指南

### 读取函数示例

```python
import yaml

def load_function(func_dir):
    '''读取 function.yaml'''
    with open(f'{func_dir}/function.yaml') as f:
        spec = yaml.safe_load(f)
    
    # 提取关键信息
    func_id = spec['id']
    name = spec['name']
    
    # 获取代码
    if spec['entrypoint']['kind'] == 'inline':
        code = spec['entrypoint']['code']
    else:
        # 从文件读取
        code_path = f"{func_dir}/{spec['entrypoint']['path']}"
        with open(code_path) as f:
            code = f.read()
    
    # 提取签名
    inputs = spec['signature']['inputs']  # dict
    outputs = spec['signature']['outputs']  # dict
    
    # 提取测试
    tests = spec['tests']['cases']
    
    return {
        'id': func_id,
        'name': name,
        'code': code,
        'inputs': inputs,
        'outputs': outputs,
        'tests': tests,
        'semantics': spec.get('semantics', {})
    }
```

---

## 结论

**采用方案 A：完全废弃 metadata-schema，统一使用 FunctionSpec。**

理由：
1. FunctionSpec 更完整、更现代
2. YAML 比 JSON 更适合配置文件
3. 语义声明对 Agent 至关重要
4. 长远来看，单一规范更容易维护

**下一步行动**：删除 `specs/metadata-schema.md`
