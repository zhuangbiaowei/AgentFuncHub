#!/usr/bin/env python3
"""
AgentFuncHub 集成测试
使用 FastAPI TestClient 测试 SDK 与后端的完整交互
无需运行实际后端服务
"""

import pytest
import sys
import os
from pathlib import Path

# 确保使用 SQLite 模式
os.environ["USE_SQLITE"] = "true"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"

sys.path.insert(0, '/home/mlf/AgentFuncHub/src/server')
sys.path.insert(0, '/home/mlf/AgentFuncHub/src/sdk/python')

from fastapi.testclient import TestClient
from main import app, load_functions

# 加载示例函数
load_functions()

# 创建 TestClient
client = TestClient(app)


class TestAPIEndpoints:
    """测试 API 端点"""
    
    def test_root_endpoint(self):
        """测试根端点"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AgentFuncHub"
        assert "functions_count" in data
    
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_list_functions(self):
        """测试列出函数"""
        response = client.get("/functions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "functions" in data
        assert "total" in data
    
    def test_get_function_success(self):
        """测试获取函数详情 - 成功"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "function" in data
        func = data["function"]
        assert func["id"] == "validation.email.basic"
    
    def test_get_function_not_found(self):
        """测试获取函数详情 - 不存在"""
        response = client.get("/functions/nonexistent.function.12345")
        assert response.status_code == 404
    
    def test_search_functions(self):
        """测试搜索函数"""
        search_query = {
            "query": "email",
            "limit": 5
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
    
    def test_get_tags(self):
        """测试获取标签"""
        response = client.get("/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tags" in data
        assert isinstance(data["tags"], list)
    
    def test_get_languages(self):
        """测试获取语言"""
        response = client.get("/languages")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "languages" in data
        assert "python" in data["languages"]
    
    def test_validate_function(self):
        """测试验证函数"""
        function_spec = {
            "spec_version": "0.1",
            "id": "test.validate.function",
            "version": "1.0.0",
            "name": "Test Validate Function",
            "description": "A valid test function",
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
        assert response.status_code == 200
        data = response.json()
        assert "valid" in data


class TestSDKIntegration:
    """测试 SDK 集成"""
    
    def test_function_spec_structure(self):
        """测试函数规范结构"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        func = data["function"]
        
        # 检查必需字段
        assert "spec_version" in func
        assert "id" in func
        assert "name" in func
        assert "description" in func
        assert "language" in func
        assert "entrypoint" in func
        assert "signature" in func
    
    def test_function_language(self):
        """测试函数语言信息"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        func = data["function"]
        
        assert "language" in func
        assert func["language"]["name"] == "python"
    
    def test_function_signature(self):
        """测试函数签名"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        func = data["function"]
        
        assert "signature" in func
        assert "inputs" in func["signature"]
        assert "outputs" in func["signature"]
    
    def test_function_tags(self):
        """测试函数标签"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        func = data["function"]
        
        assert "tags" in func
        assert isinstance(func["tags"], list)
        assert "validation" in func["tags"]
        assert "email" in func["tags"]
    
    def test_semantics_info(self):
        """测试语义信息"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        func = data["function"]
        
        if "semantics" in func:
            semantics = func["semantics"]
            assert "deterministic" in semantics
            assert "side_effects" in semantics
            assert "purity" in semantics
    
    def test_pagination(self):
        """测试分页功能"""
        # 测试限制数量
        response = client.get("/functions?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["functions"]) <= 5
        
        # 测试偏移
        response = client.get("/functions?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["offset"] == 5
    
    def test_filter_by_language(self):
        """测试按语言过滤"""
        response = client.get("/functions?language=python")
        assert response.status_code == 200
        data = response.json()
        
        for func in data["functions"]:
            assert func["language"]["name"] == "python"
    
    def test_filter_by_tag(self):
        """测试按标签过滤"""
        response = client.get("/functions?tag=validation")
        assert response.status_code == 200
        data = response.json()
        
        for func in data["functions"]:
            assert "validation" in func.get("tags", [])


class TestCreateAndDelete:
    """测试创建和删除函数"""
    
    def test_create_and_delete_function(self):
        """测试创建和删除函数的完整流程"""
        import uuid
        unique_id = f"test.integration.{uuid.uuid4().hex[:8]}"
        
        # 创建函数
        new_function = {
            "spec_version": "0.1",
            "id": unique_id,
            "version": "1.0.0",
            "name": "Integration Test Function",
            "description": "Created by integration test",
            "language": {"name": "python", "runtime": "python>=3.8"},
            "entrypoint": {
                "kind": "inline",
                "symbol": "test_func",
                "code": "def test_func(x): return x * 2"
            },
            "signature": {
                "inputs": {
                    "x": {"type": "integer", "required": True, "description": "Input"}
                },
                "outputs": {
                    "result": {"type": "integer", "description": "Output"}
                }
            },
            "tags": ["test", "integration"]
        }
        
        create_response = client.post("/functions", json=new_function)
        assert create_response.status_code == 200
        create_data = create_response.json()
        assert create_data["success"] is True
        assert create_data["function_id"] == unique_id
        
        # 验证函数存在
        get_response = client.get(f"/functions/{unique_id}")
        assert get_response.status_code == 200
        
        # 删除函数
        delete_response = client.delete(f"/functions/{unique_id}")
        assert delete_response.status_code == 200
        delete_data = delete_response.json()
        assert delete_data["success"] is True
        
        # 验证函数已删除
        get_response = client.get(f"/functions/{unique_id}")
        assert get_response.status_code == 404
    
    def test_create_duplicate_function(self):
        """测试创建重复函数"""
        # 尝试创建已存在的函数
        duplicate_function = {
            "spec_version": "0.1",
            "id": "validation.email.basic",
            "version": "1.0.0",
            "name": "Duplicate",
            "description": "Duplicate function",
            "language": {"name": "python"},
            "entrypoint": {"kind": "inline", "symbol": "dup", "code": "pass"},
            "signature": {"inputs": {}, "outputs": {}}
        }
        
        response = client.post("/functions", json=duplicate_function)
        assert response.status_code == 409


class TestSearchFunctionality:
    """测试搜索功能"""
    
    def test_search_with_query(self):
        """测试带查询的搜索"""
        search_query = {
            "query": "验证",
            "limit": 10
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert data["query"] == "验证"
    
    def test_search_with_language_filter(self):
        """测试带语言过滤的搜索"""
        search_query = {
            "query": "email",
            "language": "python",
            "limit": 5
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # 所有结果都应该是 python
        for result in data["results"]:
            assert result["spec"]["language"]["name"] == "python"
    
    def test_search_empty_query(self):
        """测试空查询搜索"""
        search_query = {
            "query": "",
            "limit": 5
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
    
    def test_search_results_structure(self):
        """测试搜索结果结构"""
        search_query = {
            "query": "email",
            "limit": 3
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        
        for result in data["results"]:
            assert "function_id" in result
            assert "name" in result
            assert "description" in result
            assert "similarity_score" in result
            assert "spec" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
