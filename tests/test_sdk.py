#!/usr/bin/env python3
"""
测试 Python SDK
使用 FastAPI TestClient 模拟后端服务
"""

import sys
import os

# 确保使用 SQLite 模式
os.environ["USE_SQLITE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

sys.path.insert(0, '/home/mlf/AgentFuncHub/src/server')
sys.path.insert(0, '/home/mlf/AgentFuncHub/src/sdk/python')

from fastapi.testclient import TestClient
from main import app, load_functions

# 加载示例函数并创建 TestClient
load_functions()
client = TestClient(app)

print("🧪 测试 Python SDK (使用 TestClient)\n")

# 1. 搜索函数
print("1. 搜索函数 '验证邮箱'")
try:
    search_query = {"query": "验证邮箱", "limit": 3}
    response = client.post("/search", json=search_query)
    if response.status_code == 200:
        data = response.json()
        results = data.get("results", [])
        print(f"   ✅ 找到 {len(results)} 个函数")
        for func in results[:3]:
            print(f"      - {func.get('name')} ({func.get('function_id')})")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 2. 获取函数详情
print("\n2. 获取函数详情")
try:
    response = client.get("/functions/validation.email.basic")
    if response.status_code == 200:
        data = response.json()
        func = data.get("function", {})
        print(f"   ✅ {func.get('name')}")
        desc = func.get('description', '')
        print(f"      描述: {desc[:50]}...")
        print(f"      语言: {func.get('language', {}).get('name')}")
        print(f"      标签: {', '.join(func.get('tags', [])[:3])}")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 3. 列出函数
print("\n3. 列出函数")
try:
    response = client.get("/functions?limit=5")
    if response.status_code == 200:
        data = response.json()
        functions = data.get("functions", [])
        print(f"   ✅ 找到 {len(functions)} 个函数")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 4. 获取标签
print("\n4. 获取标签")
try:
    response = client.get("/tags")
    if response.status_code == 200:
        data = response.json()
        tags = data.get("tags", [])
        print(f"   ✅ {len(tags)} 个标签: {', '.join(tags[:5])}...")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 5. 获取语言
print("\n5. 获取语言")
try:
    response = client.get("/languages")
    if response.status_code == 200:
        data = response.json()
        languages = data.get("languages", [])
        print(f"   ✅ 支持的语言: {', '.join(languages)}")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 6. 验证函数规范
print("\n6. 验证函数规范")
try:
    function_spec = {
        "spec_version": "0.1",
        "id": "test.sdk.function",
        "version": "1.0.0",
        "name": "SDK Test Function",
        "description": "A test function for SDK",
        "language": {"name": "python"},
        "entrypoint": {
            "kind": "inline",
            "symbol": "test",
            "code": "def test(x): return x"
        },
        "signature": {
            "inputs": {"x": {"type": "integer", "required": True}},
            "outputs": {"result": {"type": "integer"}}
        }
    }
    response = client.post("/validate", json=function_spec)
    if response.status_code == 200:
        data = response.json()
        valid = data.get("valid")
        print(f"   ✅ 验证结果: {'有效' if valid else '无效'}")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 7. 测试函数详情字段
print("\n7. 函数详情字段检查")
try:
    response = client.get("/functions/validation.email.basic")
    if response.status_code == 200:
        data = response.json()
        func = data.get("function", {})
        print(f"   ✅ ID: {func.get('id')}")
        print(f"   ✅ 版本: {func.get('version')}")
        print(f"   ✅ 确定性: {func.get('semantics', {}).get('deterministic')}")
        print(f"   ✅ 纯度: {func.get('semantics', {}).get('purity')}")
        
        sig = func.get('signature', {})
        print(f"   ✅ 输入参数: {list(sig.get('inputs', {}).keys())}")
        print(f"   ✅ 输出参数: {list(sig.get('outputs', {}).keys())}")
        
        # 获取示例输入
        inputs = sig.get('inputs', {})
        example = {}
        for key, value in inputs.items():
            if 'example' in value:
                example[key] = value['example']
            elif 'default' in value:
                example[key] = value['default']
        print(f"   ✅ 示例输入: {example}")
    else:
        print(f"   ⚠️  状态码: {response.status_code}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

print("\n✅ SDK 测试完成!")
