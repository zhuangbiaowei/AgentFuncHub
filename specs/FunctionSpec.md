# FunctionSpec v0.1

## 1. 目标与非目标

### 目标

* **函数为最小共享单元**：可被 Agent 直接检索与调用
* **可验证**：必须有机器可执行的测试或验证方法
* **可组合**：明确 I/O、约束、side effects，使编排可行
* **可治理**：可签名、可版本化、可废弃、可追溯

### 非目标

* 不定义“包管理/依赖分发”的完整生态（可由运行时/平台扩展）
* 不强制绑定某种语言或沙箱实现
* 不解决所有安全问题（只提供声明与可验证接口）

---

## 2. 资源模型：一个函数能力的最小发布单元

建议一个目录即一个函数能力单元：

```
text.normalize.basic/
  function.yaml          # FunctionSpec 主文件（必需）
  src/                   # 代码（可选：也可 inline）
    normalize.rb
  tests/                 # 测试资源（可选：也可 inline）
    cases.yaml
  README.md              # 人类说明（可选）
  LICENSE                # 可选（也可在 spec 里声明）
```

---

## 3. 文档格式与兼容性

* 文件名推荐：`function.yaml`
* 编码：UTF-8
* 版本字段：`spec_version: "0.1"`
* 未识别字段：允许存在，但必须在 `extensions` 命名空间或顶层以 `x_` 前缀出现（便于前向兼容）

---

## 4. 顶层结构（概览）

```yaml
spec_version: "0.1"

id: "text.normalize.basic"
version: "1.0.0"
name: "Normalize Text"
description: "Normalize whitespace and punctuation for mixed Chinese/English text."

license: "Apache-2.0"
authors:
  - name: "..."
    contact: "..."

language:
  name: "ruby"
  runtime: "ruby>=3.1"

entrypoint:
  kind: "file"
  path: "src/normalize.rb"
  symbol: "normalize_text"   # 可选：函数名/导出符号
# 或 kind: "inline" 直接内联源码

signature:
  inputs: { ... }
  outputs: { ... }

semantics:
  deterministic: true
  side_effects: ["none"]
  concurrency: { ... }
  security: { ... }

dependencies:
  system: [ ... ]
  packages: [ ... ]

examples: [ ... ]
tests: { ... }

tags: [ ... ]
quality: { ... }
lifecycle: { ... }
provenance: { ... }

extensions: { ... }
```

---

# 5. 字段定义（v0.1）

下面按 **MUST / SHOULD / MAY** 标注。

## 5.1 身份与版本

### `spec_version` (MUST)

* 类型：string
* 固定为 `"0.1"`

### `id` (MUST)

* 类型：string
* 规范：**全局唯一**的能力标识符（建议反域名或分层命名）
* 推荐格式：`<domain>.<category>.<name>[.<variant>]`
* 示例：`text.normalize.basic` / `crypto.hash.sha256`

### `version` (MUST)

* 类型：string
* 语义：**FunctionSpec 记录的能力版本**（不是 spec_version）
* 推荐：SemVer（`MAJOR.MINOR.PATCH`）

### `name` (MUST)

* 类型：string（人类可读名称）

### `description` (MUST)

* 类型：string（≤ 1,000 字符建议）
* 语义：一句话说明“做什么 + 不做什么”

### `keywords` (MAY)

* 类型：string[]
* 用于检索召回（多语言可）

---

## 5.2 授权与作者

### `license` (SHOULD)

* 类型：string
* 推荐 SPDX 标识（例如 `Apache-2.0`、`MIT`）

### `authors` (MAY)

* 类型：list of:

  * `name` (MUST)
  * `contact` (MAY)
  * `organization` (MAY)

---

## 5.3 语言与运行环境

### `language` (MUST)

* 类型：object
* 字段：

  * `name` (MUST): `ruby|python|js|ts|go|java|rust|cpp|...`
  * `runtime` (MAY): 例如 `python>=3.10`
  * `dialect` (MAY): 如 `node`, `deno`
  * `encoding` (MAY): 默认 `utf-8`

---

## 5.4 入口与代码载体

### `entrypoint` (MUST)

* 类型：object
* 字段：

  * `kind` (MUST): `"file" | "inline" | "container" | "wasm"`
  * `path` (SHOULD if kind=file): 相对路径
  * `symbol` (MAY): 导出函数名/符号
  * `code` (SHOULD if kind=inline): 源码字符串
  * `image` (SHOULD if kind=container): OCI 镜像引用
  * `module` (SHOULD if kind=wasm): wasm 文件路径

**v0.1 建议支持 file/inline；container/wasm 允许但可不实现。**

---

## 5.5 签名：输入输出（核心）

### `signature` (MUST)

* 类型：object
* 字段：

  * `inputs` (MUST): map
  * `outputs` (MUST): map
  * `errors` (MAY): 可枚举错误
  * `io_schema` (MAY): `jsonschema|openapi|custom`（v0.1 可选）

每个输入/输出字段定义结构：

```yaml
<field_name>:
  type: "string|integer|number|boolean|object|array|bytes|file|path|any"
  required: true|false
  description: "..."
  constraints:
    min: ...
    max: ...
    pattern: "regex"
    enum: [ ... ]
  default: ...
  example: ...
```

约束：

* `type` 必须存在
* `required` 在 inputs 里默认 `false`，在 outputs 里默认 `true`（可显式覆盖）
* `any` 类型应谨慎使用（会降低可组合性）

---

## 5.6 语义属性（Agent 安全/编排关键）

### `semantics` (MUST)

字段：

#### `deterministic` (MUST)

* bool：同输入是否保证同输出（忽略时间、随机、网络等因素）

#### `side_effects` (MUST)

* string[]，枚举：

  * `none`
  * `fs_read`, `fs_write`
  * `network`, `process_spawn`
  * `db_read`, `db_write`
  * `env_read`
  * `stdout`, `stderr`
  * `ipc`
  * `gpu`

> 这是 Agent 是否敢用的关键字段之一。

#### `purity` (MAY)

* `"pure" | "impure"`（pure 等价于 `deterministic=true` 且 side_effects=[none]）

#### `resource_profile` (MAY)

```yaml
resource_profile:
  cpu: "low|medium|high"
  memory: "low|medium|high"
  latency_ms_p50: 5
  latency_ms_p99: 50
```

#### `concurrency` (MAY)

```yaml
concurrency:
  thread_safe: true
  reentrant: true
  parallelism: "safe|unsafe|unknown"
```

#### `security` (SHOULD)

```yaml
security:
  sandbox_required: true
  secrets_required: []         # 例如 ["OPENAI_API_KEY"]
  data_sensitivity: "low|medium|high"
  known_risks:
    - "May execute regex with catastrophic backtracking on adversarial input."
```

---

## 5.7 依赖声明

### `dependencies` (MAY)

```yaml
dependencies:
  system:
    - name: "curl"
      version: ">=7.0"
  packages:
    - name: "nokogiri"
      version: "~>1.16"
      registry: "rubygems"
```

---

## 5.8 示例与用例

### `examples` (SHOULD)

list，每条：

```yaml
- name: "normalize logs"
  input:
    text: "Hello   世界!!!"
  output:
    text: "Hello 世界"
  notes: "..."
```

### `use_cases` (MAY)

* string[]：业务/任务场景标签

---

## 5.9 测试与验证（必须可机验证）

### `tests` (MUST)

v0.1 允许两种方式：

#### A) 内联 case（最简单、强推荐）

```yaml
tests:
  framework: "builtin"
  cases:
    - name: "basic"
      input: { text: "Hello   世界!!!" }
      expect: { text: "Hello 世界" }
    - name: "empty"
      input: { text: "" }
      expect: { text: "" }
```

#### B) 引用外部测试文件

```yaml
tests:
  framework: "builtin"
  path: "tests/cases.yaml"
```

> v0.1 建议先只实现 builtin：即 runner 负责按 signature 调用 entrypoint，并比较 expect。

### `tests.oracle` (MAY)

用于非确定性或复杂输出：

```yaml
tests:
  oracle:
    kind: "predicate"
    description: "Output must contain only ASCII and CJK, no repeated spaces."
```

---

## 5.10 质量、生命周期与溯源

### `quality` (MAY)

```yaml
quality:
  maturity: "experimental|beta|stable"
  coverage: 0.85
  lint: ["rubocop"]
```

### `lifecycle` (MAY)

```yaml
lifecycle:
  status: "active|deprecated|archived"
  deprecated_since: "2026-02-01"
  replacement: "text.normalize.v2"
```

### `provenance` (SHOULD)

```yaml
provenance:
  created_at: "2026-02-01"
  updated_at: "2026-02-01"
  source:
    kind: "manual|generated|ported"
    notes: "ported from internal utils"
  checksum:
    algo: "sha256"
    value: "..."
```

---

## 5.11 扩展机制

### `extensions` (MAY)

* 任意对象，供未来标准化
* 建议所有自定义扩展都放这里，或使用 `x_*` 顶层字段

---

# 6. 规范约束（v0.1 的“硬规则”）

1. **MUST 有 tests**（要么内联 cases，要么引用测试文件）
2. **MUST 明确 deterministic + side_effects**
3. `signature.inputs/outputs` 中每个字段 MUST 有 `type`
4. 若 `side_effects` 包含 `network/db_write/process_spawn/fs_write`，`security.sandbox_required` SHOULD 为 true
5. 若 `deterministic=false`，tests SHOULD 提供 oracle（predicate）或统计型验证

---

# 7. 完整示例：Ruby 文本规范化函数

```yaml
spec_version: "0.1"
id: "text.normalize.basic"
version: "1.0.0"
name: "Normalize Text"
description: "Normalize whitespace and punctuation for mixed Chinese/English text; preserves CJK characters."

license: "Apache-2.0"
authors:
  - name: "Biaowei Zhuang"

language:
  name: "ruby"
  runtime: "ruby>=3.1"

entrypoint:
  kind: "file"
  path: "src/normalize.rb"
  symbol: "normalize_text"

signature:
  inputs:
    text:
      type: "string"
      required: true
      description: "Input text."
      example: "Hello   世界!!!"
  outputs:
    text:
      type: "string"
      description: "Normalized text."
  errors:
    - code: "E_INVALID_ENCODING"
      description: "Input is not valid UTF-8."

semantics:
  deterministic: true
  side_effects: ["none"]
  concurrency:
    thread_safe: true
    reentrant: true
    parallelism: "safe"
  security:
    sandbox_required: false
    data_sensitivity: "low"

examples:
  - name: "basic"
    input: { text: "Hello   世界!!!" }
    output: { text: "Hello 世界!!!" }

tests:
  framework: "builtin"
  cases:
    - name: "collapse spaces"
      input: { text: "Hello   世界" }
      expect: { text: "Hello 世界" }
    - name: "trim"
      input: { text: "  Hello 世界  " }
      expect: { text: "Hello 世界" }
    - name: "keep cjk"
      input: { text: "中文 空格   English" }
      expect: { text: "中文 空格 English" }

tags: ["text", "normalize", "preprocess", "agent-tool"]

quality:
  maturity: "beta"

provenance:
  created_at: "2026-02-01"
  updated_at: "2026-02-01"
  source:
    kind: "manual"
```
