#!/usr/bin/env python3
"""
AgentFuncHub 集成测试
测试 SDK 与后端的完整交互
"""

import pytest
import sys
sys.path.insert(0, '/home/mlf/AgentFuncHub/src/sdk/python')

from agentfunchub import Client, AsyncClient
from agentfunchub.exceptions import FunctionNotFoundError

BASE_URL = "http://localhost:8000"


class TestClient:
    """测试同步客户端"""
    
    @pytest.fixture
    def client(self):
        client = Client(base_url=BASE_URL)
        yield client
        client.close()
    
    def test_get_function(self, client):
        """测试获取函数详情"""
        func = client.get_function("validation.email.basic")
        assert func.id == "validation.email.basic"
        assert func.name == "Email Validator"
        assert func.language == "python"
        assert "email" in func.inputs
    
    def test_list_functions(self, client):
        """测试列出函数"""
        functions = client.list_functions(limit=5)
        assert len(functions) <= 5
        assert all(hasattr(f, 'id') for f in functions)
    
    def test_search_functions(self, client):
        """测试搜索函数"""
        results = client.search("email", limit=5)
        # 可能有结果，也可能没有（取决于搜索服务）
        assert isinstance(results, list)
    
    def test_get_tags(self, client):
        """测试获取标签"""
        tags = client.get_tags()
        assert isinstance(tags, list)
        assert len(tags) > 0
    
    def test_get_languages(self, client):
        """测试获取语言"""
        languages = client.get_languages()
        assert isinstance(languages, list)
        assert "python" in languages
    
    def test_function_not_found(self, client):
        """测试函数不存在"""
        with pytest.raises(FunctionNotFoundError):
            client.get_function("nonexistent.function.12345")


class TestFunction:
    """测试 Function 对象"""
    
    @pytest.fixture
    def client(self):
        client = Client(base_url=BASE_URL)
        yield client
        client.close()
    
    def test_function_properties(self, client):
        """测试函数属性"""
        func = client.get_function("validation.email.basic")
        
        assert func.id == "validation.email.basic"
        assert func.name == "Email Validator"
        assert func.version == "1.0.0"
        assert func.language == "python"
        assert func.is_deterministic is True
        assert func.purity == "pure"
        assert "validation" in func.tags
        assert "email" in func.tags
    
    def test_function_inputs(self, client):
        """测试输入参数"""
        func = client.get_function("validation.email.basic")
        
        assert "email" in func.inputs
        assert func.inputs["email"]["type"] == "string"
        assert func.inputs["email"]["required"] is True
    
    def test_function_outputs(self, client):
        """测试输出参数"""
        func = client.get_function("validation.email.basic")
        
        assert "is_valid" in func.outputs
        assert func.outputs["is_valid"]["type"] == "boolean"
    
    def test_get_example_input(self, client):
        """测试获取示例输入"""
        func = client.get_function("validation.email.basic")
        example = func.get_example_input()
        
        assert "email" in example
        assert isinstance(example, dict)
    
    def test_validate_input(self, client):
        """测试输入验证"""
        func = client.get_function("validation.email.basic")
        
        # 有效的输入
        errors = func.validate_input(email="test@example.com")
        assert len(errors) == 0
        
        # 缺少必需参数
        errors = func.validate_input()
        assert len(errors) > 0
        assert any("email" in e for e in errors)
        
        # 未知参数
        errors = func.validate_input(email="test@example.com", unknown_param=True)
        assert any("unknown_param" in e for e in errors)


class TestAsyncClient:
    """测试异步客户端"""
    
    @pytest.mark.asyncio
    async def test_async_get_function(self):
        """测试异步获取函数"""
        async with AsyncClient(base_url=BASE_URL) as client:
            func = await client.get_function("validation.email.basic")
            assert func.id == "validation.email.basic"
    
    @pytest.mark.asyncio
    async def test_async_list_functions(self):
        """测试异步列出函数"""
        async with AsyncClient(base_url=BASE_URL) as client:
            functions = await client.list_functions(limit=5)
            assert len(functions) <= 5
    
    @pytest.mark.asyncio
    async def test_async_search(self):
        """测试异步搜索"""
        async with AsyncClient(base_url=BASE_URL) as client:
            results = await client.search("email", limit=5)
            assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
