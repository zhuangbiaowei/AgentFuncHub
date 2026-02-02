"""
向量搜索服务 - FunctionSpec 格式支持
使用 sentence-transformers 进行语义搜索
"""

from typing import List, Dict, Tuple
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

class VectorSearchService:
    """向量搜索服务"""
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        """
        初始化向量搜索服务
        
        Args:
            model_name: 使用的嵌入模型名称
        """
        self.model_name = model_name
        self.model = None
        self.function_ids: List[str] = []
        self.vectors: List[np.ndarray] = []
        self.texts: List[str] = []
        
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            print(f"✅ Loaded embedding model: {model_name}")
        except ImportError:
            print("⚠️ sentence-transformers not installed, using keyword fallback")
        except Exception as e:
            print(f"⚠️ Failed to load model: {e}, using keyword fallback")
    
    def _create_text_representation(self, func_data: Dict) -> str:
        """
        从 FunctionSpec 创建文本表示
        """
        parts = []
        
        # 名称和描述
        parts.append(func_data.get('name', ''))
        parts.append(func_data.get('description', ''))
        
        # 标签
        parts.extend(func_data.get('tags', []))
        
        # 签名信息
        signature = func_data.get('signature', {})
        
        # 输入参数
        for param_name, param_info in signature.get('inputs', {}).items():
            parts.append(param_name)
            if isinstance(param_info, dict):
                parts.append(param_info.get('description', ''))
        
        # 输出参数
        for param_name, param_info in signature.get('outputs', {}).items():
            parts.append(param_name)
            if isinstance(param_info, dict):
                parts.append(param_info.get('description', ''))
        
        # ID（用于搜索匹配）
        parts.append(func_data.get('id', ''))
        
        return ' '.join(filter(None, parts))
    
    def add_function(self, function_id: str, func_data: Dict) -> bool:
        """
        添加函数到索引
        
        Returns:
            bool: 是否成功添加
        """
        if self.model is None:
            return False
        
        try:
            text = self._create_text_representation(func_data)
            vector = self.model.encode(text)
            
            self.function_ids.append(function_id)
            self.vectors.append(vector)
            self.texts.append(text)
            
            return True
        except Exception as e:
            print(f"❌ Failed to add function {function_id}: {e}")
            return False
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        搜索相关函数
        
        Returns:
            List of (function_id, similarity_score) tuples
        """
        if self.model is None or not self.vectors:
            return []
        
        try:
            # 编码查询
            query_vector = self.model.encode(query)
            query_vector = query_vector.reshape(1, -1)
            
            # 计算相似度
            vectors_array = np.array(self.vectors)
            similarities = cosine_similarity(query_vector, vectors_array)[0]
            
            # 获取 top-k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            for idx in top_indices:
                if similarities[idx] > 0.1:  # 最小相似度阈值
                    results.append((
                        self.function_ids[idx],
                        float(similarities[idx])
                    ))
            
            return results
            
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return []
    
    def search_hybrid(self, query: str, keyword_matches: List[str], top_k: int = 10) -> List[Tuple[str, float]]:
        """
        混合搜索：结合向量相似度和关键词匹配
        
        Args:
            query: 查询文本
            keyword_matches: 关键词匹配的函数ID列表
            top_k: 返回结果数量
            
        Returns:
            List of (function_id, combined_score) tuples
        """
        vector_results = self.search(query, top_k * 2)
        
        # 合并结果
        scores = {}
        
        # 向量分数（权重 0.7）
        for func_id, score in vector_results:
            scores[func_id] = scores.get(func_id, 0) + score * 0.7
        
        # 关键词分数（权重 0.3）
        for func_id in keyword_matches:
            scores[func_id] = scores.get(func_id, 0) + 0.3
        
        # 排序并返回 top-k
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def get_stats(self) -> Dict:
        """获取索引统计信息"""
        return {
            "indexed_functions": len(self.function_ids),
            "model": self.model_name if self.model else "fallback",
            "vector_dimension": len(self.vectors[0]) if self.vectors else 0
        }


# 简单的关键词匹配（fallback）
def keyword_search(query: str, func_data: Dict) -> float:
    """
    基于关键词的简单搜索（适配 FunctionSpec 格式）
    """
    query_words = set(query.lower().split())
    
    # 构建函数文本
    texts = [
        func_data.get('name', ''),
        func_data.get('description', ''),
        ' '.join(func_data.get('tags', [])),
        func_data.get('id', '')
    ]
    
    # 添加签名信息
    signature = func_data.get('signature', {})
    for param_name in signature.get('inputs', {}).keys():
        texts.append(param_name)
    for param_name in signature.get('outputs', {}).keys():
        texts.append(param_name)
    
    func_text = ' '.join(texts).lower()
    func_words = set(func_text.split())
    
    # 同义词扩展
    synonyms = {
        'email': ['mail', 'mailbox', '邮箱'],
        'phone': ['mobile', 'cellphone', 'telephone', '电话', '手机'],
        'validate': ['check', 'verify', 'validation', '验证'],
        'date': ['time', 'datetime', 'calendar', '日期', '时间'],
        'password': ['pwd', 'passwd', '密码'],
        'json': ['json', 'json格式'],
        'encode': ['encoding', 'decode', '编码'],
        'csv': ['comma', 'delimiter', '表格'],
        'list': ['array', 'sequence', '列表'],
        'number': ['digit', 'integer', 'float', '数字'],
        'text': ['string', '字符', '文本'],
    }
    
    expanded_query = set(query_words)
    for word in query_words:
        if word in synonyms:
            expanded_query.update(synonyms[word])
    
    # 计算 Jaccard 相似度
    intersection = len(expanded_query & func_words)
    union = len(expanded_query | func_words)
    
    return intersection / union if union > 0 else 0.0


# 全局搜索服务实例
_search_service = None

def get_search_service() -> VectorSearchService:
    """获取或创建搜索服务实例"""
    global _search_service
    if _search_service is None:
        _search_service = VectorSearchService()
    return _search_service
