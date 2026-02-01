"""
测试 AgentFuncHub SDK
"""

import pytest
import json
from pathlib import Path

# 测试数据目录
EXAMPLES_DIR = Path(__file__).parent.parent / "examples"


def load_manifest(example_name: str) -> dict:
    """加载示例函数的 manifest"""
    manifest_path = EXAMPLES_DIR / example_name / "manifest.json"
    with open(manifest_path) as f:
        return json.load(f)


class TestManifestSchema:
    """测试元数据 Schema"""
    
    def test_email_validator_manifest(self):
        """测试邮箱验证器的 manifest"""
        manifest = load_manifest("validate_email")
        
        # 检查必需字段
        assert "function_id" in manifest
        assert "name" in manifest
        assert "description" in manifest
        assert "language" in manifest
        assert manifest["language"] == "python"
        
        # 检查签名
        assert "signature" in manifest
        assert "inputs" in manifest["signature"]
        assert "outputs" in manifest["signature"]
        
        # 检查测试用例
        assert "test_cases" in manifest
        assert len(manifest["test_cases"]) > 0
        
        # 检查每个测试用例
        for test in manifest["test_cases"]:
            assert "name" in test
            assert "input" in test
            assert "expected" in test
    
    def test_slug_generator_manifest(self):
        """测试 slug 生成器的 manifest"""
        manifest = load_manifest("generate_slug")
        
        assert manifest["name"] == "generate_slug"
        assert "unicode" in manifest["tags"] or "chinese" in str(manifest["test_cases"])
    
    def test_security_fields(self):
        """测试安全字段"""
        manifest = load_manifest("validate_email")
        
        assert "security" in manifest
        assert "risk_level" in manifest["security"]
        assert manifest["security"]["risk_level"] in ["low", "medium", "high"]


class TestSDK:
    """测试 Python SDK"""
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        from src.sdk.python.agentfunchub import Client
        
        # 注意：这里需要设置环境变量或传入 api_key
        # client = Client(api_key="test_key")
        pass
    
    def test_function_repr(self):
        """测试 Function 类的字符串表示"""
        from src.sdk.python.agentfunchub import Function, Client
        
        client = Client(api_key="test")
        manifest = {"name": "test_func"}
        func = Function("uuid-123", manifest, client)
        
        assert "test_func" in repr(func)


class TestCodeValidation:
    """测试代码验证逻辑"""
    
    def test_validate_email_code(self):
        """实际测试邮箱验证代码"""
        manifest = load_manifest("validate_email")
        code = manifest["code"]["source"]
        
        # 执行代码定义函数
        exec(code, globals())
        
        # 测试用例 1: 有效邮箱
        is_valid, msg = validate_email("test@example.com")
        assert is_valid is True
        
        # 测试用例 2: 无效格式
        is_valid, msg = validate_email("invalid-email")
        assert is_valid is False
        
        # 测试用例 3: 空邮箱应该抛出异常
        try:
            validate_email("")
            assert False, "应该抛出 ValueError"
        except ValueError:
            pass
    
    def test_generate_slug_code(self):
        """测试 slug 生成代码"""
        manifest = load_manifest("generate_slug")
        code = manifest["code"]["source"]
        
        exec(code, globals())
        
        # 测试基本功能
        assert generate_slug("Hello World") == "hello-world"
        
        # 测试中文保留
        assert generate_slug("你好世界", allow_unicode=True) == "你好世界"
        
        # 测试长度限制
        result = generate_slug("this is a very long title", max_length=10)
        assert len(result) <= 10


def test_manifest_completeness():
    """测试所有示例 manifest 的完整性"""
    
    required_fields = [
        "function_id",
        "name", 
        "description",
        "language",
        "version",
        "signature",
        "code",
        "test_cases",
        "author",
        "created_at"
    ]
    
    examples = ["validate_email", "generate_slug"]
    
    for example in examples:
        manifest = load_manifest(example)
        
        for field in required_fields:
            assert field in manifest, f"{example} 缺少字段: {field}"
        
        # 检查测试用例数量
        assert len(manifest["test_cases"]) >= 1, f"{example} 需要至少一个测试用例"
        
        # 检查代码不为空
        assert manifest["code"]["source"], f"{example} 代码不能为空"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
