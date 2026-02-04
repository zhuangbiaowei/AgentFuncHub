/**
 * 函数详情组件
 */

import { useState, useEffect } from 'react';
import { 
  Card, Button, Tag, Descriptions, Tabs, Input, 
  Space, Typography, Alert, Spin, Divider, message 
} from 'antd';
import { 
  ArrowLeftOutlined, PlayOutlined, CopyOutlined,
  CodeOutlined, FileTextOutlined, SafetyOutlined 
} from '@ant-design/icons';
import { FunctionSpec, ExecutionResult } from '../types';
import { api } from '../api';

const { Title, Paragraph, Text } = Typography;
const { TextArea } = Input;

interface FunctionDetailProps {
  functionId: string;
  onBack?: () => void;
}

export default function FunctionDetail({ functionId, onBack }: FunctionDetailProps) {
  const [func, setFunc] = useState<FunctionSpec | null>(null);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<ExecutionResult | null>(null);
  const [testInput, setTestInput] = useState('');

  useEffect(() => {
    loadFunction();
  }, [functionId]);

  const loadFunction = async () => {
    setLoading(true);
    try {
      const response = await api.getFunction(functionId);
      setFunc(response.function);
      
      // 设置默认测试输入
      if (response.function.signature?.inputs) {
        const defaultInput: Record<string, any> = {};
        Object.entries(response.function.signature.inputs).forEach(([key, param]) => {
          defaultInput[key] = param.example || param.default || '';
        });
        setTestInput(JSON.stringify(defaultInput, null, 2));
      }
    } catch (error) {
      message.error('加载函数失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExecute = async () => {
    if (!func) return;
    
    setExecuting(true);
    setExecutionResult(null);
    
    try {
      let input;
      try {
        input = JSON.parse(testInput);
      } catch {
        message.error('输入格式错误，请输入有效的 JSON');
        return;
      }
      
      const result = await api.executeFunction(functionId, input);
      setExecutionResult(result);
    } catch (error) {
      message.error('执行失败: ' + (error as Error).message);
    } finally {
      setExecuting(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('已复制到剪贴板');
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!func) {
    return <Alert message="函数不存在" type="error" />;
  }

  const items = [
    {
      key: 'overview',
      label: (
        <span>
          <FileTextOutlined /> 概览
        </span>
      ),
      children: (
        <div>
          <Descriptions bordered column={2}>
            <Descriptions.Item label="ID">{func.id}</Descriptions.Item>
            <Descriptions.Item label="版本">{func.version}</Descriptions.Item>
            <Descriptions.Item label="语言">
              <Tag color="blue">{func.language.name}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="许可证">{func.license || 'MIT'}</Descriptions.Item>
            <Descriptions.Item label="成熟度">
              {func.quality?.maturity || 'experimental'}
            </Descriptions.Item>
            <Descriptions.Item label="覆盖率">
              {func.quality?.coverage 
                ? `${(func.quality.coverage * 100).toFixed(0)}%` 
                : 'N/A'}
            </Descriptions.Item>
          </Descriptions>

          <Divider />

          <Title level={4}>标签</Title>
          <Space>
            {func.tags?.map(tag => (
              <Tag key={tag}>{tag}</Tag>
            ))}
          </Space>

          <Divider />

          <Title level={4}>语义特性</Title>
          {func.semantics && (
            <Descriptions size="small">
              <Descriptions.Item label="确定性">
                {func.semantics.deterministic ? '是' : '否'}
              </Descriptions.Item>
              <Descriptions.Item label="纯度">
                {func.semantics.purity}
              </Descriptions.Item>
              <Descriptions.Item label="副作用">
                {func.semantics.side_effects?.join(', ') || '无'}
              </Descriptions.Item>
            </Descriptions>
          )}
        </div>
      ),
    },
    {
      key: 'signature',
      label: (
        <span>
          <CodeOutlined /> 签名
        </span>
      ),
      children: (
        <div>
          <Title level={4}>输入参数</Title>
          {Object.entries(func.signature.inputs).map(([name, param]) => (
            <Card key={name} size="small" style={{ marginBottom: 8 }}>
              <div>
                <Text strong>{name}</Text>
                <Tag size="small">{param.type}</Tag>
                {param.required && <Tag color="red" size="small">必需</Tag>}
              </div>
              <Paragraph>{param.description}</Paragraph>
              {param.example && (
                <div>
                  <Text type="secondary">示例: {JSON.stringify(param.example)}</Text>
                </div>
              )}
            </Card>
          ))}

          <Divider />

          <Title level={4}>输出</Title>
          {Object.entries(func.signature.outputs).map(([name, param]) => (
            <Card key={name} size="small" style={{ marginBottom: 8 }}>
              <div>
                <Text strong>{name}</Text>
                <Tag size="small">{param.type}</Tag>
              </div>
              <Paragraph>{param.description}</Paragraph>
            </Card>
          ))}
        </div>
      ),
    },
    {
      key: 'code',
      label: (
        <span>
          <CodeOutlined /> 代码
        </span>
      ),
      children: (
        <div>
          <div style={{ marginBottom: 16 }}>
            <Button
              icon={<CopyOutlined />}
              onClick={() => copyToClipboard(func.entrypoint.code || '')}
            >
              复制代码
            </Button>
          </div>
          <pre style={{ 
            background: '#f6f8fa', 
            padding: 16, 
            borderRadius: 6,
            overflow: 'auto'
          }}>
            <code>{func.entrypoint.code}</code>
          </pre>
        </div>
      ),
    },
    {
      key: 'test',
      label: (
        <span>
          <PlayOutlined /> 测试
        </span>
      ),
      children: (
        <div>
          <Paragraph>输入参数 (JSON 格式):</Paragraph>
          <TextArea
            rows={6}
            value={testInput}
            onChange={(e) => setTestInput(e.target.value)}
            placeholder='{"param": "value"}'
          />
          
          <Button
            type="primary"
            icon={<PlayOutlined />}
            onClick={handleExecute}
            loading={executing}
            style={{ marginTop: 16, marginBottom: 16 }}
          >
            执行函数
          </Button>

          {executionResult && (
            <div>
              <Divider>执行结果</Divider>
              {'error' in executionResult ? (
                <Alert message={executionResult.error} type="error" />
              ) : (
                <pre style={{ 
                  background: '#f6ffed', 
                  padding: 16, 
                  borderRadius: 6,
                  border: '1px solid #b7eb8f'
                }}>
                  {JSON.stringify(executionResult.result, null, 2)}
                </pre>
              )}
              {executionResult.duration_ms && (
                <Text type="secondary">
                  执行时间: {executionResult.duration_ms}ms
                </Text>
              )}
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="function-detail">
      <Button 
        icon={<ArrowLeftOutlined />} 
        onClick={onBack}
        style={{ marginBottom: 16 }}
      >
        返回
      </Button>

      <Card>
        <Title level={2}>{func.name}</Title>
        <Paragraph>{func.description}</Paragraph>

        <Tabs items={items} />
      </Card>
    </div>
  );
}
