# AgentFuncHub API 使用指南

## 快速开始

### 启动服务

```bash
# 安装依赖
pip install -r requirements.txt

# 初始化数据库（加载示例函数）
python scripts/init_db.py

# 启动服务
python src/server/main.py
```

服务将在 `http://localhost:8000` 启动。

访问文档：`http://localhost:8000/docs`

---

## API 示例

### 1. 创建函数

```bash
curl -X POST http://localhost:8000/functions \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello_world",
    "display_name": "Hello World",
    "description": "A simple hello world function",
    "language": "python",
    "version": "1.0.0",
    "signature": {
      "inputs": [
        {"name": "name", "type": "str", "description": "Name to greet", "required": true}
      ],
      "outputs": [
        {"type": "str", "description": "Greeting message"}
      ]
    },
    "code": {
      "source": "def hello_world(name): return f'\"Hello, {name}!\"'",
      "hash": "sha256:placeholder",
      "line_count": 1,
      "complexity": 1.0
    },
    "test_cases": [
      {
        "name": "test_basic",
        "description": "Basic test",
        "input": {"name": "World"},
        "expected": {"result": "Hello, World!"},
        "tags": ["basic"]
      }
    ],
    "tags": ["hello", "example"],
    "categories": ["example"],
    "author": {"name": "TestUser", "type": "human"}
  }'
```

### 2. 搜索函数

```bash
# 搜索邮箱验证相关函数
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "验证邮箱 email validation",
    "language": "python",
    "limit": 5
  }'
```

响应示例：
```json
{
  "success": true,
  "query": "验证邮箱 email validation",
  "total": 1,
  "results": [
    {
      "function_id": "func-001-email-validator",
      "name": "validate_email",
      "description": "验证邮箱格式并检查域名有效性",
      "similarity_score": 0.75,
      "manifest": { ... }
    }
  ]
}
```

### 3. 获取函数详情

```bash
curl http://localhost:8000/functions/{function_id}
```

### 4. 列出所有函数

```bash
# 所有函数
curl "http://localhost:8000/functions?limit=10"

# 按语言过滤
curl "http://localhost:8000/functions?language=python"

# 按分类过滤
curl "http://localhost:8000/functions?category=validation"
```

### 5. 验证函数

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_function",
    "description": "Test function",
    "language": "python",
    "signature": { ... },
    "code": { ... },
    "test_cases": [ ... ],
    "author": { ... }
  }'
```

---

## 使用 Python SDK

```python
from agentfunchub import Client

# 创建客户端
client = Client(api_key="your_key", base_url="http://localhost:8000")

# 搜索函数
results = client.search("验证邮箱", language="python")

# 获取第一个结果
func = results[0]
print(f"Found: {func.name} - {func.description}")

# 查看函数签名
print(f"Inputs: {func.signature['inputs']}")
print(f"Outputs: {func.signature['outputs']}")
```

---

## 示例函数使用

### 邮箱验证

```python
# 获取函数
func = client.get("func-001-email-validator")

# 调用（需要远程执行支持）
# 或者直接使用代码
exec(func.manifest['code']['source'])
result = validate_email("test@example.com")
print(result)  # (True, 'Valid email format')
```

### 手机号验证

```python
func = client.get("func-003-phone-validator")
exec(func.manifest['code']['source'])

is_valid, carrier, formatted = validate_phone_cn("13812345678")
print(f"Valid: {is_valid}, Carrier: {carrier}, Formatted: {formatted}")
# Valid: True, Carrier: mobile, Formatted: 138-1234-5678
```

### 日期解析

```python
func = client.get("func-006-date-parser")
exec(func.manifest['code']['source'])

success, date, fmt = parse_date_flexible("3天前", base_date="2024-03-15")
print(f"Date: {date}, Format: {fmt}")
# Date: 2024-03-12, Format: natural_relative_past
```

---

## 错误处理

### 常见错误码

| 状态码 | 错误 | 说明 |
|--------|------|------|
| 400 | INVALID_REQUEST | 请求格式错误 |
| 404 | FUNCTION_NOT_FOUND | 函数不存在 |
| 409 | FUNCTION_EXISTS | 函数已存在 |
| 422 | VALIDATION_ERROR | 数据验证失败 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

### 错误响应格式

```json
{
  "detail": "Function not found"
}
```

---

## 限制

- **请求频率**: 100/min
- **函数大小**: 最大 100KB 代码
- **测试用例**: 最少 1 个，最多 50 个
- **搜索返回**: 最多 50 个结果

---

## 开发提示

1. **使用 Swagger UI** - 访问 `/docs` 进行交互式测试
2. **查看日志** - 服务启动时会显示请求日志
3. **本地存储** - 数据保存在 `data/functions.json`
4. **热重载** - 修改代码后服务会自动重载（开发模式）
