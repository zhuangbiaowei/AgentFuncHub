"""
AgentFuncHub API 客户端
"""

import os
from typing import Optional, List, Dict, Any, Union
import httpx
from .exceptions import (
    AgentFuncHubError,
    AuthenticationError,
    FunctionNotFoundError,
    ExecutionError,
    ValidationError,
    RateLimitError,
)
from .function import Function


DEFAULT_BASE_URL = "http://localhost:8000"


class Client:
    """
    AgentFuncHub API 客户端
    
    Args:
        api_key: API 密钥，用于认证
        base_url: API 基础 URL
        timeout: 请求超时时间（秒）
    
    示例:
        >>> client = Client()
        >>> 
        >>> # 使用 API Key
        >>> client = Client(api_key="your-api-key")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        self.api_key = api_key or os.getenv("AGENTFUNCHUB_API_KEY")
        self.base_url = (base_url or os.getenv("AGENTFUNCHUB_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        
        # 创建 HTTP 客户端
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """关闭客户端"""
        self._client.close()
    
    def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送 HTTP 请求"""
        try:
            response = self._client.request(method, path, **kwargs)
            
            # 处理错误
            if response.status_code == 401:
                raise AuthenticationError("Invalid or missing API key")
            elif response.status_code == 404:
                raise FunctionNotFoundError(f"Resource not found: {path}")
            elif response.status_code == 429:
                raise RateLimitError("Rate limit exceeded")
            elif response.status_code == 422:
                data = response.json()
                raise ValidationError(data.get("detail", "Validation failed"))
            elif response.status_code >= 400:
                data = response.json()
                raise AgentFuncHubError(data.get("detail", f"HTTP {response.status_code}"))
            
            return response.json()
        except httpx.TimeoutException:
            raise AgentFuncHubError(f"Request timeout after {self.timeout}s")
        except httpx.ConnectError:
            raise AgentFuncHubError(f"Cannot connect to {self.base_url}")
    
    # === 函数 API ===
    
    def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10
    ) -> List[Function]:
        """
        搜索函数
        
        Args:
            query: 搜索查询（自然语言或关键词）
            language: 过滤编程语言
            limit: 最大返回数量
        
        Returns:
            函数列表
        
        示例:
            >>> results = client.search("验证邮箱", language="python")
            >>> for func in results:
            ...     print(f"{func.name}: {func.description}")
        """
        data = {
            "query": query,
            "limit": limit
        }
        if language:
            data["language"] = language
        
        response = self._request("POST", "/search", json=data)
        
        return [Function(self, r["spec"], r["similarity_score"]) for r in response.get("results", [])]
    
    def get_function(self, function_id: str) -> Function:
        """
        获取函数详情
        
        Args:
            function_id: 函数 ID
        
        Returns:
            函数对象
        
        示例:
            >>> func = client.get_function("validation.email.basic")
            >>> print(func.name)
        """
        response = self._request("GET", f"/functions/{function_id}")
        return Function(self, response["function"])
    
    def list_functions(
        self,
        language: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Function]:
        """
        列出函数
        
        Args:
            language: 按语言过滤
            tag: 按标签过滤
            limit: 返回数量
            offset: 分页偏移
        
        Returns:
            函数列表
        """
        params = {"limit": limit, "offset": offset}
        if language:
            params["language"] = language
        if tag:
            params["tag"] = tag
        
        response = self._request("GET", "/functions", params=params)
        return [Function(self, f) for f in response.get("functions", [])]
    
    def call(
        self,
        function_id: str,
        **kwargs
    ) -> Any:
        """
        调用函数（便捷方法）
        
        Args:
            function_id: 函数 ID
            **kwargs: 函数参数
        
        Returns:
            函数执行结果
        
        示例:
            >>> result = client.call("validation.email.basic", email="test@example.com")
            >>> print(result["is_valid"])
        """
        func = self.get_function(function_id)
        return func.execute(**kwargs)
    
    # === 执行 API ===
    
    def execute(
        self,
        function_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        执行函数
        
        Args:
            function_id: 函数 ID
            input_data: 输入参数
        
        Returns:
            执行结果
        """
        response = self._request(
            "POST",
            f"/execute/functions/{function_id}",
            json=input_data
        )
        
        if "error" in response:
            raise ExecutionError(
                response["error"],
                error_type=response.get("error_type"),
                details=response.get("details")
            )
        
        return response
    
    # === 元数据 API ===
    
    def get_tags(self) -> List[str]:
        """获取所有标签"""
        response = self._request("GET", "/tags")
        return response.get("tags", [])
    
    def get_languages(self) -> List[str]:
        """获取所有编程语言"""
        response = self._request("GET", "/languages")
        return response.get("languages", [])
    
    # === 用户 API ===
    
    def get_current_user(self) -> Dict[str, Any]:
        """获取当前用户信息"""
        return self._request("GET", "/auth/me")
    
    def create_api_key(self) -> str:
        """创建新的 API Key"""
        response = self._request("POST", "/auth/api-keys")
        return response["api_key"]
