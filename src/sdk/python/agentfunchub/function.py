"""
Function 对象
表示 AgentFuncHub 中的一个函数
"""

from typing import Dict, Any, Optional, List
import json


class Function:
    """
    AgentFuncHub 函数
    
    提供对函数的访问和执行能力
    """
    
    def __init__(
        self,
        client,
        spec: Dict[str, Any],
        similarity_score: Optional[float] = None
    ):
        self._client = client
        self._spec = spec
        self._similarity_score = similarity_score
    
    def __repr__(self) -> str:
        return f"Function(id='{self.id}', name='{self.name}')"
    
    # === 属性 ===
    
    @property
    def id(self) -> str:
        """函数 ID"""
        return self._spec["id"]
    
    @property
    def name(self) -> str:
        """函数名称"""
        return self._spec.get("name", "")
    
    @property
    def description(self) -> str:
        """函数描述"""
        return self._spec.get("description", "")
    
    @property
    def version(self) -> str:
        """函数版本"""
        return self._spec.get("version", "1.0.0")
    
    @property
    def language(self) -> str:
        """编程语言"""
        return self._spec.get("language", {}).get("name", "")
    
    @property
    def runtime(self) -> Optional[str]:
        """运行时要求"""
        return self._spec.get("language", {}).get("runtime")
    
    @property
    def tags(self) -> List[str]:
        """标签列表"""
        return self._spec.get("tags", [])
    
    @property
    def spec(self) -> Dict[str, Any]:
        """完整规范"""
        return self._spec
    
    @property
    def similarity_score(self) -> Optional[float]:
        """搜索相似度分数"""
        return self._similarity_score
    
    # === 签名信息 ===
    
    @property
    def inputs(self) -> Dict[str, Dict[str, Any]]:
        """输入参数定义"""
        return self._spec.get("signature", {}).get("inputs", {})
    
    @property
    def outputs(self) -> Dict[str, Dict[str, Any]]:
        """输出参数定义"""
        return self._spec.get("signature", {}).get("outputs", {})
    
    @property
    def entrypoint(self) -> Dict[str, Any]:
        """入口点信息"""
        return self._spec.get("entrypoint", {})
    
    @property
    def code(self) -> Optional[str]:
        """函数代码（inline 类型）"""
        return self.entrypoint.get("code")
    
    @property
    def symbol(self) -> str:
        """函数符号名"""
        return self.entrypoint.get("symbol", "")
    
    # === 语义信息 ===
    
    @property
    def is_deterministic(self) -> bool:
        """是否确定性函数"""
        return self._spec.get("semantics", {}).get("deterministic", True)
    
    @property
    def purity(self) -> str:
        """函数纯度"""
        return self._spec.get("semantics", {}).get("purity", "pure")
    
    @property
    def side_effects(self) -> List[str]:
        """副作用列表"""
        return self._spec.get("semantics", {}).get("side_effects", ["none"])
    
    # === 质量信息 ===
    
    @property
    def maturity(self) -> str:
        """成熟度"""
        return self._spec.get("quality", {}).get("maturity", "experimental")
    
    @property
    def coverage(self) -> float:
        """测试覆盖率"""
        return self._spec.get("quality", {}).get("coverage", 0.0)
    
    # === 方法 ===
    
    def execute(self, **kwargs) -> Any:
        """
        执行函数
        
        Args:
            **kwargs: 函数参数
        
        Returns:
            函数执行结果
        
        示例:
            >>> result = func.execute(email="test@example.com")
            >>> print(result["is_valid"])
        """
        result = self._client.execute(self.id, kwargs)
        return result.get("result")
    
    def validate_input(self, **kwargs) -> List[str]:
        """
        验证输入参数
        
        Args:
            **kwargs: 待验证的参数
        
        Returns:
            错误信息列表（空表示验证通过）
        """
        errors = []
        
        for name, param in self.inputs.items():
            # 检查必需参数
            if param.get("required", True) and name not in kwargs:
                errors.append(f"Missing required parameter: {name}")
                continue
            
            if name not in kwargs:
                continue
            
            value = kwargs[name]
            param_type = param.get("type")
            
            # 类型检查
            if param_type == "string" and not isinstance(value, str):
                errors.append(f"Parameter '{name}' should be a string")
            elif param_type == "integer" and not isinstance(value, int):
                errors.append(f"Parameter '{name}' should be an integer")
            elif param_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Parameter '{name}' should be a number")
            elif param_type == "boolean" and not isinstance(value, bool):
                errors.append(f"Parameter '{name}' should be a boolean")
            elif param_type == "array" and not isinstance(value, list):
                errors.append(f"Parameter '{name}' should be an array")
            elif param_type == "object" and not isinstance(value, dict):
                errors.append(f"Parameter '{name}' should be an object")
            
            # 枚举检查
            enum_values = param.get("enum")
            if enum_values and value not in enum_values:
                errors.append(f"Parameter '{name}' should be one of: {enum_values}")
        
        # 检查未知参数
        for name in kwargs:
            if name not in self.inputs:
                errors.append(f"Unknown parameter: {name}")
        
        return errors
    
    def get_example_input(self) -> Dict[str, Any]:
        """
        获取示例输入
        
        Returns:
            示例参数字典
        """
        example = {}
        for name, param in self.inputs.items():
            if "example" in param:
                example[name] = param["example"]
            elif "default" in param:
                example[name] = param["default"]
            else:
                # 根据类型生成默认值
                param_type = param.get("type", "string")
                if param_type == "string":
                    example[name] = ""
                elif param_type == "integer":
                    example[name] = 0
                elif param_type == "number":
                    example[name] = 0.0
                elif param_type == "boolean":
                    example[name] = False
                elif param_type == "array":
                    example[name] = []
                elif param_type == "object":
                    example[name] = {}
        return example
    
    def to_code(self) -> str:
        """
        获取可执行的代码
        
        Returns:
            Python 代码字符串
        """
        if self.code:
            return self.code
        
        # 生成占位代码
        return f"""# Function: {self.name}
# ID: {self.id}
# Description: {self.description}

def {self.symbol}(**kwargs):
    \"\"\"
    {self.description}
    \"\"\"
    # TODO: Implement this function
    raise NotImplementedError("This function needs to be implemented")
"""
    
    def print_info(self):
        """打印函数信息"""
        print(f"Function: {self.name}")
        print(f"ID: {self.id}")
        print(f"Version: {self.version}")
        print(f"Description: {self.description}")
        print(f"Language: {self.language}")
        print(f"Tags: {', '.join(self.tags)}")
        print(f"\nInputs:")
        for name, param in self.inputs.items():
            required = " (required)" if param.get("required") else ""
            print(f"  - {name}: {param.get('type')}{required} - {param.get('description', '')}")
        print(f"\nOutputs:")
        for name, param in self.outputs.items():
            print(f"  - {name}: {param.get('type')} - {param.get('description', '')}")
