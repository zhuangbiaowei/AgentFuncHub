# AgentFuncHub API 规范 (v0.1)

## 基础信息

- **Base URL**: `https://api.agentfunchub.io/v1`
- **协议**: HTTPS
- **数据格式**: JSON
- **认证**: Bearer Token

## 认证

```bash
Authorization: Bearer <token>
```

## 核心 API

### 1. 函数管理

#### 发布函数

```http
POST /functions
Content-Type: application/json
Authorization: Bearer <token>

{
  "manifest": { ... },
  "code": "...",
  "test_results": { ... }
}
```

**响应:**
```json
{
  "success": true,
  "function_id": "uuid",
  "url": "https://api.agentfunchub.io/v1/functions/uuid",
  "validation": {
    "passed": true,
    "test_count": 5,
    "passed_count": 5
  }
}
```

#### 获取函数详情

```http
GET /functions/{function_id}
Authorization: Bearer <token>
```

**响应:**
```json
{
  "function_id": "uuid",
  "manifest": { ... },
  "code": "...",
  "stats": { ... }
}
```

#### 更新函数

```http
PATCH /functions/{function_id}
Content-Type: application/json
Authorization: Bearer <token>

{
  "manifest": { ... },
  "code": "..."
}
```

#### 删除函数

```http
DELETE /functions/{function_id}
Authorization: Bearer <token>
```

---

### 2. 语义搜索

#### 搜索函数

```http
POST /search
Content-Type: application/json
Authorization: Bearer <token>

{
  "query": "验证邮箱地址格式",
  "language": "python",
  "filters": {
    "categories": ["validation"],
    "min_rating": 4.0,
    "max_complexity": 5.0
  },
  "limit": 10,
  "offset": 0
}
```

**响应:**
```json
{
  "total": 156,
  "results": [
    {
      "function_id": "uuid",
      "name": "validate_email",
      "description": "验证邮箱格式并检查域名",
      "similarity_score": 0.92,
      "manifest": { ... }
    }
  ]
}
```

#### 相似函数推荐

```http
GET /functions/{function_id}/similar?limit=5
Authorization: Bearer <token>
```

---

### 3. 函数调用

#### 远程调用

```http
POST /functions/{function_id}/call
Content-Type: application/json
Authorization: Bearer <token>

{
  "args": ["arg1", "arg2"],
  "kwargs": { "key": "value" },
  "timeout": 30,
  "sandbox_config": {
    "memory_limit": "128MB",
    "cpu_limit": "1s"
  }
}
```

**响应:**
```json
{
  "success": true,
  "result": { ... },
  "execution_time_ms": 45,
  "logs": []
}
```

---

### 4. 验证服务

#### 验证函数

```http
POST /validate
Content-Type: application/json
Authorization: Bearer <token>

{
  "manifest": { ... },
  "code": "..."
}
```

**响应:**
```json
{
  "valid": true,
  "checks": {
    "syntax": { "passed": true },
    "tests": { "passed": 5, "failed": 0 },
    "security": { "risk_level": "low" },
    "metadata": { "passed": true }
  },
  "errors": [],
  "warnings": []
}
```

---

### 5. 统计分析

#### 获取函数统计

```http
GET /functions/{function_id}/stats
Authorization: Bearer <token>
```

**响应:**
```json
{
  "downloads": 1234,
  "calls": 5678,
  "success_rate": 0.98,
  "avg_execution_time_ms": 12,
  "ratings": {
    "avg": 4.5,
    "count": 89
  }
}
```

#### 获取趋势

```http
GET /trending?category=validation&period=week
Authorization: Bearer <token>
```

---

## 错误处理

### 错误响应格式

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Function validation failed",
    "details": {
      "test_failures": [...]
    },
    "request_id": "req_abc123"
  }
}
```

### 错误码列表

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 400 | INVALID_REQUEST | 请求格式错误 |
| 400 | VALIDATION_FAILED | 函数验证失败 |
| 401 | UNAUTHORIZED | 未授权 |
| 403 | FORBIDDEN | 禁止访问 |
| 404 | FUNCTION_NOT_FOUND | 函数不存在 |
| 429 | RATE_LIMITED | 请求频率超限 |
| 500 | INTERNAL_ERROR | 服务器内部错误 |

---

## 速率限制

- **认证请求**: 100/min
- **函数调用**: 1000/min
- **搜索**: 60/min

响应头:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1706784000
```

---

## SDK 示例

### Python SDK

```python
from agentfunchub import Client

client = Client(api_key="your_api_key")

# 搜索函数
results = client.search("验证邮箱", language="python")

# 调用函数
result = client.call(results[0].id, email="test@example.com")

# 发布函数
func = client.publish(
    name="my_function",
    code="def my_function(): ...",
    manifest={...}
)
```

### JavaScript SDK

```javascript
import { Client } from '@agentfunchub/sdk';

const client = new Client({ apiKey: 'your_api_key' });

// 搜索
const results = await client.search('validate email', { language: 'javascript' });

// 调用
const result = await client.call(results[0].id, { email: 'test@example.com' });
```

---

## WebSocket API (实时功能)

### 连接

```javascript
const ws = new WebSocket('wss://api.agentfunchub.io/v1/ws?token=<token>');
```

### 订阅函数更新

```json
{
  "type": "subscribe",
  "channel": "function:{function_id}"
}
```

### 实时调用日志

```json
{
  "type": "subscribe",
  "channel": "execution:{function_id}"
}
```
