"""
AgentFuncHub 后端 API 测试
测试 FastAPI 服务端点
"""

import pytest
import json
from pathlib import Path
from fastapi.testclient import TestClient
import sys
import yaml

# 添加 src/server 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "server"))

from main import app, load_functions

client = TestClient(app)


@pytest.fixture(scope="module")
def setup_functions():
    """加载示例函数"""
    load_functions()


class TestRootEndpoints:
    """测试根端点"""
    
    def test_root(self):
        """测试根路由"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "AgentFuncHub"
        assert data["spec_version"] == "0.1"
        assert "functions_count" in data
        assert "search" in data
    
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "functions_loaded" in data


class TestFunctionEndpoints:
    """测试函数管理端点"""
    
    def test_list_functions(self, setup_functions):
        """测试列出所有函数"""
        response = client.get("/functions")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "functions" in data
        assert "total" in data
        assert data["spec_version"] == "0.1"
    
    def test_list_functions_with_filter(self, setup_functions):
        """测试带过滤条件的函数列表"""
        response = client.get("/functions?language=python")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 所有函数都是 python，应该返回所有
        assert data["total"] >= 0
    
    def test_list_functions_with_tag(self, setup_functions):
        """测试按标签过滤"""
        response = client.get("/functions?tag=validation")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 检查返回的函数都包含 validation 标签
        for func in data["functions"]:
            assert "validation" in func.get("tags", [])
    
    def test_get_function_success(self, setup_functions):
        """测试获取函数详情 - 成功"""
        response = client.get("/functions/validation.email.basic")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["spec_version"] == "0.1"
        assert "function" in data
        func = data["function"]
        assert func["id"] == "validation.email.basic"
        assert "signature" in func
        assert "entrypoint" in func
    
    def test_get_function_not_found(self):
        """测试获取函数详情 - 不存在"""
        response = client.get("/functions/nonexistent.function")
        assert response.status_code == 404
    
    def test_create_function(self):
        """测试创建函数 - 使用唯一 ID 避免冲突"""
        import uuid
        unique_id = f"test.create.{uuid.uuid4().hex[:8]}"
        new_function = {
            "spec_version": "0.1",
            "id": unique_id,
            "version": "1.0.0",
            "name": "Test Create Function",
            "description": "A test function for creation",
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
            "tags": ["test"]
        }
        
        response = client.post("/functions", json=new_function)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["function_id"] == unique_id
        assert "url" in data
    
    def test_create_function_duplicate(self):
        """测试创建重复函数"""
        new_function = {
            "spec_version": "0.1",
            "id": "validation.email.basic",  # 已存在的 ID
            "version": "1.0.0",
            "name": "Duplicate",
            "description": "Duplicate function",
            "language": {"name": "python"},
            "entrypoint": {"kind": "inline", "symbol": "dup", "code": "pass"},
            "signature": {"inputs": {}, "outputs": {}}
        }
        
        response = client.post("/functions", json=new_function)
        assert response.status_code == 409
    
    def test_delete_function(self):
        """测试删除函数"""
        # 先创建一个要删除的函数
        new_function = {
            "spec_version": "0.1",
            "id": "test.delete.function",
            "version": "1.0.0",
            "name": "Test Delete Function",
            "description": "To be deleted",
            "language": {"name": "python"},
            "entrypoint": {"kind": "inline", "symbol": "test", "code": "pass"},
            "signature": {"inputs": {}, "outputs": {}}
        }
        client.post("/functions", json=new_function)
        
        # 删除
        response = client.delete("/functions/test.delete.function")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_delete_function_not_found(self):
        """测试删除不存在的函数"""
        response = client.delete("/functions/nonexistent.delete")
        assert response.status_code == 404


class TestSearchEndpoints:
    """测试搜索端点"""
    
    def test_search_functions(self, setup_functions):
        """测试搜索函数"""
        search_query = {
            "query": "验证邮箱",
            "limit": 5
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert "search_method" in data
    
    def test_search_functions_with_language(self, setup_functions):
        """测试带语言过滤的搜索"""
        search_query = {
            "query": "验证",
            "language": "python",
            "limit": 10
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # 所有结果都应该是 python
        for result in data["results"]:
            assert result["spec"]["language"]["name"] == "python"
    
    def test_search_functions_empty_query(self, setup_functions):
        """测试空查询搜索"""
        search_query = {
            "query": "",
            "limit": 5
        }
        response = client.post("/search", json=search_query)
        assert response.status_code == 200


class TestValidateEndpoints:
    """测试验证端点"""
    
    def test_validate_valid_function(self):
        """测试验证有效函数"""
        function_spec = {
            "spec_version": "0.1",
            "id": "test.valid.function",
            "version": "1.0.0",
            "name": "Valid Test Function",
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
        assert data["valid"] is True
        assert data["spec_version"] == "0.1"
    
    def test_validate_invalid_function(self):
        """测试验证无效函数 - 缺少必需字段会被 Pydantic 拦截"""
        invalid_spec = {
            "spec_version": "0.1",
            # 缺少必需的 id
            "version": "1.0.0",
            "name": "Invalid",
            "description": "Missing id",
            "language": {"name": "python"},
            "entrypoint": {"kind": "inline", "symbol": "test", "code": "pass"},
            "signature": {"inputs": {}, "outputs": {}}
        }
        
        # Pydantic 会返回 422 验证错误
        response = client.post("/validate", json=invalid_spec)
        assert response.status_code == 422
    
    def test_validate_inline_without_code(self):
        """测试验证 inline 类型但缺少 code"""
        invalid_spec = {
            "spec_version": "0.1",
            "id": "test.no.code",
            "version": "1.0.0",
            "name": "No Code",
            "description": "Missing code",
            "language": {"name": "python"},
            "entrypoint": {
                "kind": "inline",
                "symbol": "test"
                # 缺少 code
            },
            "signature": {"inputs": {}, "outputs": {}}
        }
        
        response = client.post("/validate", json=invalid_spec)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False


class TestMetadataEndpoints:
    """测试元数据端点"""
    
    def test_get_tags(self, setup_functions):
        """测试获取所有标签"""
        response = client.get("/tags")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "tags" in data
        assert isinstance(data["tags"], list)
        # 应该有一些常见标签
        assert len(data["tags"]) > 0
    
    def test_get_languages(self, setup_functions):
        """测试获取所有语言"""
        response = client.get("/languages")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "languages" in data
        assert "python" in data["languages"]


class TestFunctionSpecExamples:
    """测试示例函数是否符合 FunctionSpec"""
    
    def test_all_examples_loadable(self):
        """测试所有示例函数可以加载"""
        examples_dir = Path(__file__).parent.parent / "examples"
        
        yaml_files = list(examples_dir.glob("*/function.yaml"))
        assert len(yaml_files) > 0, "No function.yaml files found"
        
        for yaml_file in yaml_files:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            # 基本验证
            assert "spec_version" in data, f"{yaml_file}: missing spec_version"
            assert "id" in data, f"{yaml_file}: missing id"
            assert "name" in data, f"{yaml_file}: missing name"
            assert "signature" in data, f"{yaml_file}: missing signature"
    
    def test_example_functions_have_required_fields(self):
        """测试示例函数包含所有必需字段"""
        examples_dir = Path(__file__).parent.parent / "examples"
        
        required_fields = [
            "spec_version", "id", "version", "name",
            "description", "language", "entrypoint", "signature"
        ]
        
        for yaml_file in examples_dir.glob("*/function.yaml"):
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            for field in required_fields:
                assert field in data, f"{yaml_file}: missing required field '{field}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
