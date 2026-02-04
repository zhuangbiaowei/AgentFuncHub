"""
异步客户端
"""

from typing import Optional, List, Dict, Any
import httpx
from .client import DEFAULT_BASE_URL
from .exceptions import (
    AgentFuncHubError,
    AuthenticationError,
    FunctionNotFoundError,
    ExecutionError,
    ValidationError,
    RateLimitError,
)
from .function import Function


class AsyncClient:
    """
    AgentFuncHub 异步 API 客户端
    
    示例:
        >>> async with AsyncClient() as client:
        ...     results = await client.search("验证邮箱")
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        import os
        self.api_key = api_key or os.getenv("AGENTFUNCHUB_API_KEY")
        self.base_url = (base_url or os.getenv("AGENTFUNCHUB_URL") or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=headers,
            timeout=timeout
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """关闭客户端"""
        await self._client.aclose()
    
    async def _request(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """发送异步 HTTP 请求"""
        try:
            response = await self._client.request(method, path, **kwargs)
            
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
    
    async def search(
        self,
        query: str,
        language: Optional[str] = None,
        limit: int = 10
    ) -> List[Function]:
        """搜索函数"""
        data = {"query": query, "limit": limit}
        if language:
            data["language"] = language
        
        response = await self._request("POST", "/search", json=data)
        return [Function(self, r["spec"], r["similarity_score"]) for r in response.get("results", [])]
    
    async def get_function(self, function_id: str) -> Function:
        """获取函数详情"""
        response = await self._request("GET", f"/functions/{function_id}")
        return Function(self, response["function"])
    
    async def list_functions(
        self,
        language: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Function]:
        """列出函数"""
        params = {"limit": limit, "offset": offset}
        if language:
            params["language"] = language
        if tag:
            params["tag"] = tag
        
        response = await self._request("GET", "/functions", params=params)
        return [Function(self, f) for f in response.get("functions", [])]
    
    async def call(self, function_id: str, **kwargs) -> Any:
        """调用函数"""
        func = await self.get_function(function_id)
        return await func.execute(**kwargs)
    
    async def execute(
        self,
        function_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行函数"""
        response = await self._request(
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
    
    async def get_tags(self) -> List[str]:
        """获取所有标签"""
        response = await self._request("GET", "/tags")
        return response.get("tags", [])
    
    async def get_languages(self) -> List[str]:
        """获取所有编程语言"""
        response = await self._request("GET", "/languages")
        return response.get("languages", [])
