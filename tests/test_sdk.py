#!/usr/bin/env python3
"""
测试 Python SDK
"""

import sys
sys.path.insert(0, '/home/mlf/AgentFuncHub/src/sdk/python')

from agentfunchub import Client

print("🧪 测试 Python SDK\n")

# 创建客户端
client = Client(base_url="http://localhost:8000")

# 1. 搜索函数
print("1. 搜索函数 '验证邮箱'")
try:
    results = client.search("验证邮箱", limit=3)
    print(f"   ✅ 找到 {len(results)} 个函数")
    for func in results:
        print(f"      - {func.name} ({func.id})")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 2. 获取函数详情
print("\n2. 获取函数详情")
try:
    func = client.get_function("validation.email.basic")
    print(f"   ✅ {func.name}")
    print(f"      描述: {func.description[:50]}...")
    print(f"      语言: {func.language}")
    print(f"      标签: {', '.join(func.tags[:3])}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 3. 列出函数
print("\n3. 列出函数")
try:
    functions = client.list_functions(limit=5)
    print(f"   ✅ 找到 {len(functions)} 个函数")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 4. 获取标签
print("\n4. 获取标签")
try:
    tags = client.get_tags()
    print(f"   ✅ {len(tags)} 个标签: {', '.join(tags[:5])}...")
except Exception as e:
    print(f"   ❌ 失败: {e}")

# 5. 执行函数（需要后端启动）
print("\n5. 执行函数")
try:
    result = client.call("validation.email.basic", email="test@example.com")
    print(f"   ✅ 结果: {result}")
except Exception as e:
    print(f"   ⚠️  {e}")

# 6. 测试 Function 对象
print("\n6. Function 对象属性")
try:
    func = client.get_function("validation.email.basic")
    print(f"   ✅ ID: {func.id}")
    print(f"   ✅ 版本: {func.version}")
    print(f"   ✅ 确定性: {func.is_deterministic}")
    print(f"   ✅ 纯度: {func.purity}")
    print(f"   ✅ 输入参数: {list(func.inputs.keys())}")
    print(f"   ✅ 输出参数: {list(func.outputs.keys())}")
    
    # 获取示例输入
    example = func.get_example_input()
    print(f"   ✅ 示例输入: {example}")
except Exception as e:
    print(f"   ❌ 失败: {e}")

client.close()

print("\n✅ SDK 测试完成!")
