# AgentFuncHub Python SDK

> 让 Python 开发者轻松使用 AgentFuncHub 的函数库

## 安装

```bash
pip install agentfunchub
```

## 快速开始

```python
from agentfunchub import Client

# 初始化客户端
client = Client()

# 搜索函数
results = client.search("验证邮箱")
for func in results:
    print(f"{func.name}: {func.description}")

# 执行函数
result = client.call("validation.email.basic", email="test@example.com")
print(result)  # {'is_valid': True, 'message': 'Valid email format'}
```

## 使用 API Key

```python
import os
from agentfunchub import Client

# 方式1: 直接传入
client = Client(api_key="your-api-key")

# 方式2: 环境变量
os.environ["AGENTFUNCHUB_API_KEY"] = "your-api-key"
client = Client()

# 方式3: 环境变量文件
# 创建 .env 文件
# AGENTFUNCHUB_API_KEY=your-api-key
```

## 自定义服务端点

```python
from agentfunchub import Client

# 使用自定义服务器
client = Client(base_url="https://api.agentfunchub.io")

# 或者环境变量
import os
os.environ["AGENTFUNCHUB_URL"] = "https://api.agentfunchub.io"
client = Client()
```

## 完整示例

### 搜索和执行

```python
from agentfunchub import Client

client = Client()

# 搜索函数
functions = client.search("格式化日期", language="python")

if functions:
    # 获取第一个函数
    func = functions[0]
    
    # 查看函数信息
    func.print_info()
    
    # 执行函数
    result = func.execute(date_string="2024-01-15")
    print(f"Result: {result}")
```

### 列出所有函数

```python
# 列出所有 Python 函数
functions = client.list_functions(language="python", limit=20)

# 按标签过滤
functions = client.list_functions(tag="validation")
```

### 获取函数详情

```python
# 通过 ID 获取函数
func = client.get_function("validation.email.basic")

# 访问函数属性
print(f"Name: {func.name}")
print(f"Description: {func.description}")
print(f"Language: {func.language}")
print(f"Tags: {func.tags}")

# 查看输入输出签名
print(f"Inputs: {func.inputs}")
print(f"Outputs: {func.outputs}")

# 获取示例输入
example = func.get_example_input()
print(f"Example: {example}")
```

### 本地验证输入

```python
func = client.get_function("validation.email.basic")

# 验证输入参数
errors = func.validate_input(email="test@example.com")
if errors:
    print("Validation errors:", errors)
else:
    result = func.execute(email="test@example.com")
```

## 异步支持

```python
import asyncio
from agentfunchub import AsyncClient

async def main():
    async with AsyncClient() as client:
        # 搜索函数
        results = await client.search("验证")
        
        # 并行执行多个函数
        tasks = [
            client.call("validation.email.basic", email="test@example.com"),
            client.call("validation.phone.cn", phone="13800138000"),
        ]
        results = await asyncio.gather(*tasks)
        print(results)

asyncio.run(main())
```

## 错误处理

```python
from agentfunchub import Client
from agentfunchub.exceptions import (
    FunctionNotFoundError,
    ExecutionError,
    AuthenticationError,
    ValidationError
)

client = Client()

try:
    result = client.call("nonexistent.function")
except FunctionNotFoundError:
    print("Function not found")
except ExecutionError as e:
    print(f"Execution failed: {e}")
    print(f"Error type: {e.error_type}")
except AuthenticationError:
    print("Authentication failed")
except ValidationError as e:
    print(f"Invalid input: {e}")
```

## API 参考

### Client

- `search(query, language=None, limit=10)` - 搜索函数
- `get_function(function_id)` - 获取函数详情
- `list_functions(language=None, tag=None, limit=10, offset=0)` - 列出函数
- `call(function_id, **kwargs)` - 调用函数
- `execute(function_id, input_data)` - 执行函数
- `get_tags()` - 获取所有标签
- `get_languages()` - 获取所有语言

### Function

- `execute(**kwargs)` - 执行函数
- `validate_input(**kwargs)` - 验证输入
- `get_example_input()` - 获取示例输入
- `to_code()` - 获取代码
- `print_info()` - 打印函数信息

### 属性

- `id` - 函数 ID
- `name` - 函数名称
- `description` - 描述
- `language` - 编程语言
- `tags` - 标签列表
- `inputs` - 输入参数定义
- `outputs` - 输出参数定义
- `code` - 函数代码
- `is_deterministic` - 是否确定性
- `maturity` - 成熟度
