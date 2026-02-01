"""
函数验证引擎
执行测试用例并验证函数正确性
"""

import sys
import io
import json
import traceback
from typing import Dict, List, Any, Tuple
from contextlib import redirect_stdout, redirect_stderr


class ValidationResult:
    """验证结果"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
        self.details = []
    
    def add_success(self, test_name: str, message: str = ""):
        self.passed += 1
        self.details.append({
            "test": test_name,
            "status": "passed",
            "message": message
        })
    
    def add_failure(self, test_name: str, expected: Any, actual: Any, message: str = ""):
        self.failed += 1
        self.details.append({
            "test": test_name,
            "status": "failed",
            "expected": expected,
            "actual": actual,
            "message": message
        })
    
    def add_error(self, test_name: str, error: str):
        self.failed += 1
        self.details.append({
            "test": test_name,
            "status": "error",
            "error": error
        })
    
    @property
    def success_rate(self) -> float:
        total = self.passed + self.failed
        return self.passed / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict:
        return {
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": round(self.success_rate, 2),
            "details": self.details
        }


def execute_function_safely(code: str, func_name: str, args: List, kwargs: Dict) -> Tuple[bool, Any, str]:
    """
    在安全环境中执行函数
    
    返回: (success, result, error_message)
    """
    # 创建隔离的命名空间
    namespace = {}
    
    try:
        # 执行代码定义
        exec(code, namespace)
        
        # 获取函数
        if func_name not in namespace:
            return False, None, f"Function '{func_name}' not found in code"
        
        func = namespace[func_name]
        
        # 捕获输出
        stdout_capture = io.StringIO()
        stderr_capture = io.StringIO()
        
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            result = func(*args, **kwargs)
        
        return True, result, ""
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        return False, None, error_msg


def validate_test_case(
    code: str,
    func_name: str,
    test_case: Dict[str, Any]
) -> Tuple[bool, str]:
    """
    验证单个测试用例
    
    返回: (passed, message)
    """
    test_name = test_case.get("name", "unnamed")
    test_input = test_case.get("input", {})
    expected = test_case.get("expected", {})
    
    # 准备参数
    args = []
    kwargs = {}
    
    for key, value in test_input.items():
        kwargs[key] = value
    
    try:
        # 执行函数
        success, actual, error = execute_function_safely(code, func_name, args, kwargs)
        
        if not success:
            return False, f"Execution error: {error}"
        
        # 检查是否期望异常
        if "raises" in expected:
            expected_exception = expected["raises"]
            return False, f"Expected exception {expected_exception}, but got result: {actual}"
        
        # 比较结果
        if isinstance(expected, dict):
            # 多值返回（元组解包为字典）
            if isinstance(actual, tuple):
                # 获取函数签名中的输出名称
                # 这里简化处理，假设输出顺序一致
                actual_dict = {f"output_{i}": v for i, v in enumerate(actual)}
            else:
                actual_dict = {"result": actual}
            
            # 比较每个期望字段
            for key, expected_value in expected.items():
                if key == "raises":
                    continue
                if key not in actual_dict:
                    return False, f"Missing output field: {key}"
                if actual_dict[key] != expected_value:
                    return False, f"Field '{key}': expected {expected_value}, got {actual_dict[key]}"
        else:
            # 单值返回
            if actual != expected:
                return False, f"Expected {expected}, got {actual}"
        
        return True, "Test passed"
        
    except Exception as e:
        # 检查是否是期望的异常
        if "raises" in expected:
            expected_exception = expected["raises"]
            if type(e).__name__ == expected_exception:
                return True, f"Expected exception {expected_exception} raised"
        
        return False, f"Unexpected error: {str(e)}"


def validate_function(manifest: Dict[str, Any]) -> ValidationResult:
    """
    验证函数的完整测试套件
    """
    result = ValidationResult()
    
    code = manifest.get("code", {}).get("source", "")
    func_name = manifest.get("name", "")
    test_cases = manifest.get("test_cases", [])
    
    if not code:
        result.add_error("validation", "No code provided")
        return result
    
    if not func_name:
        result.add_error("validation", "No function name provided")
        return result
    
    if not test_cases:
        result.add_error("validation", "No test cases provided")
        return result
    
    # 首先检查代码语法
    try:
        compile(code, '<string>', 'exec')
    except SyntaxError as e:
        result.add_error("syntax_check", f"Syntax error: {e}")
        return result
    
    # 执行每个测试用例
    for test_case in test_cases:
        test_name = test_case.get("name", "unnamed")
        
        passed, message = validate_test_case(code, func_name, test_case)
        
        if passed:
            result.add_success(test_name, message)
        else:
            result.add_failure(test_name, test_case.get("expected"), None, message)
    
    return result


# 用于测试
if __name__ == "__main__":
    # 测试示例
    test_manifest = {
        "name": "add_numbers",
        "code": {
            "source": "def add_numbers(a, b):\n    return a + b"
        },
        "test_cases": [
            {
                "name": "test_positive",
                "input": {"a": 1, "b": 2},
                "expected": {"result": 3}
            },
            {
                "name": "test_negative",
                "input": {"a": -1, "b": -2},
                "expected": {"result": -3}
            }
        ]
    }
    
    result = validate_function(test_manifest)
    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
