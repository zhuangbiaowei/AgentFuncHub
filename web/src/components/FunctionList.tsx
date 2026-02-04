/**
 * 函数列表组件
 */

import { useState, useEffect } from 'react';
import { Card, Tag, List, Spin, Empty, Badge } from 'antd';
import { CodeOutlined, StarOutlined, DownloadOutlined } from '@ant-design/icons';
import { FunctionSpec, FunctionSearchResult } from '../types';
import { api } from '../api';

interface FunctionListProps {
  searchQuery?: string;
  onFunctionClick?: (id: string) => void;
}

export default function FunctionList({ searchQuery, onFunctionClick }: FunctionListProps) {
  const [functions, setFunctions] = useState<FunctionSpec[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadFunctions();
  }, [searchQuery]);

  const loadFunctions = async () => {
    setLoading(true);
    try {
      if (searchQuery) {
        const response = await api.searchFunctions(searchQuery, 20);
        setFunctions(response.results.map(r => r.spec));
      } else {
        const response = await api.listFunctions({ limit: 20 });
        setFunctions(response.functions);
      }
    } catch (error) {
      console.error('Failed to load functions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getLanguageColor = (lang: string) => {
    const colors: Record<string, string> = {
      python: 'blue',
      javascript: 'yellow',
      typescript: 'cyan',
      go: 'cyan',
      rust: 'orange',
    };
    return colors[lang] || 'default';
  };

  const getMaturityTag = (maturity?: string) => {
    const colors: Record<string, string> = {
      stable: 'success',
      beta: 'warning',
      experimental: 'default',
    };
    return <Tag color={colors[maturity || 'experimental']}>{maturity || 'experimental'}</Tag>;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 50 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (functions.length === 0) {
    return <Empty description="暂无函数" />;
  }

  return (
    <List
      grid={{ gutter: 16, xs: 1, sm: 2, md: 3, lg: 3, xl: 4 }}
      dataSource={functions}
      renderItem={(func) => (
        <List.Item>
          <Card
            hoverable
            onClick={() => onFunctionClick?.(func.id)}
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <CodeOutlined />
                <span>{func.name}</span>
              </div>
            }
            extra={getMaturityTag(func.quality?.maturity)}
          >
            <p style={{ 
              color: '#666', 
              height: 44, 
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical'
            }}>
              {func.description}
            </p>

            <div style={{ marginTop: 12 }}>
              <Tag color={getLanguageColor(func.language.name)}>
                {func.language.name}
              </Tag>
              
              {func.tags?.slice(0, 3).map(tag => (
                <Tag key={tag} size="small">{tag}</Tag>
              ))}
            </div>
          </Card>
        </List.Item>
      )}
    />
  );
}
