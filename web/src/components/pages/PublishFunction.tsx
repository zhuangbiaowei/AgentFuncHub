/**
 * 函数发布页面
 */

import { useState } from 'react';
import { 
  Card, Form, Input, Select, Button, Steps, 
  Alert, Tabs, Space, Typography, message, Radio
} from 'antd';
import { 
  UploadOutlined, CheckCircleOutlined, 
  CodeOutlined, FileTextOutlined, SafetyOutlined 
} from '@ant-design/icons';
import TextArea from 'antd/es/input/TextArea';
import { api } from '../../api';

const { Title, Paragraph, Text } = Typography;
const { Step } = Steps;
const { Option } = Select;

export default function PublishFunction() {
  const [currentStep, setCurrentStep] = useState(0);
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [publishedId, setPublishedId] = useState<string | null>(null);
  const [entrypointKind, setEntrypointKind] = useState('inline');

  const handleSubmit = async (values: any) => {
    setLoading(true);
    try {
      // 构建 FunctionSpec
      const spec = {
        spec_version: '0.1',
        id: values.id,
        version: values.version || '1.0.0',
        name: values.name,
        description: values.description,
        license: values.license || 'MIT',
        language: {
          name: values.language,
          runtime: values.runtime,
        },
        entrypoint: {
          kind: entrypointKind,
          symbol: values.symbol,
          code: entrypointKind === 'inline' ? values.code : undefined,
        },
        signature: {
          inputs: parseParameters(values.inputs),
          outputs: parseParameters(values.outputs),
        },
        semantics: {
          deterministic: values.deterministic,
          side_effects: values.sideEffects || ['none'],
          purity: values.purity || 'pure',
        },
        tags: values.tags?.split(',').map((t: string) => t.trim()) || [],
        quality: {
          maturity: values.maturity || 'experimental',
          coverage: 0.0,
        },
        tests: {
          framework: 'builtin',
          cases: parseTestCases(values.testCases),
        },
      };

      const response = await api.createFunction(spec);
      setPublishedId(response.function_id);
      setCurrentStep(2);
      message.success('函数发布成功！');
    } catch (error: any) {
      message.error('发布失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const parseParameters = (params: string) => {
    try {
      return JSON.parse(params);
    } catch {
      return {};
    }
  };

  const parseTestCases = (cases: string) => {
    try {
      return JSON.parse(cases);
    } catch {
      return [];
    }
  };

  const steps = [
    { title: '基本信息', icon: <FileTextOutlined /> },
    { title: '代码定义', icon: <CodeOutlined /> },
    { title: '完成', icon: <CheckCircleOutlined /> },
  ];

  return (
    <div className="publish-function" style={{ maxWidth: 1000, margin: '0 auto' }}>
      <Title level={2}>发布函数</Title>
      <Paragraph>
        使用 FunctionSpec v0.1 格式发布你的函数到 AgentFuncHub 社区
      </Paragraph>

      <Steps current={currentStep} style={{ marginBottom: 40 }}>
        {steps.map(step => (
          <Step key={step.title} title={step.title} icon={step.icon} />
        ))}
      </Steps>

      {currentStep === 0 && (
        <Card title="基本信息">
          <Form
            form={form}
            layout="vertical"
            onFinish={() => setCurrentStep(1)}
          >
            <Form.Item
              name="id"
              label="函数 ID"
              rules={[
                { required: true, message: '请输入函数 ID' },
                { pattern: /^[a-z0-9.]+$/, message: '只能使用小写字母、数字和点' },
              ]}
              extra="格式: domain.category.name，例如: validation.email.basic"
            >
              <Input placeholder="validation.email.basic" />
            </Form.Item>

            <Form.Item
              name="name"
              label="函数名称"
              rules={[{ required: true, message: '请输入函数名称' }]}
            >
              <Input placeholder="Email Validator" />
            </Form.Item>

            <Form.Item
              name="description"
              label="描述"
              rules={[{ required: true, message: '请输入描述' }]}
            >
              <TextArea rows={3} placeholder="简要描述函数的功能" />
            </Form.Item>

            <Form.Item
              name="language"
              label="编程语言"
              rules={[{ required: true }]}
              initialValue="python"
            >
              <Select>
                <Option value="python">Python</Option>
                <Option value="javascript">JavaScript</Option>
                <Option value="typescript">TypeScript</Option>
                <Option value="go">Go</Option>
                <Option value="rust">Rust</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="tags"
              label="标签"
              extra="用逗号分隔多个标签"
            >
              <Input placeholder="validation, email, security" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit">
                下一步
              </Button>
            </Form.Item>
          </Form>
        </Card>
      )}

      {currentStep === 1 && (
        <Card title="代码定义">
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Form.Item
              name="entrypointKind"
              label="入口类型"
              initialValue="inline"
            >
              <Radio.Group 
                value={entrypointKind}
                onChange={(e) => setEntrypointKind(e.target.value)}
              >
                <Radio.Button value="inline">内联代码</Radio.Button>
                <Radio.Button value="file">文件</Radio.Button>
                <Radio.Button value="container">容器</Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              name="symbol"
              label="函数名"
              rules={[{ required: true }]}
              initialValue="main"
            >
              <Input placeholder="validate_email" />
            </Form.Item>

            {entrypointKind === 'inline' && (
              <Form.Item
                name="code"
                label="代码"
                rules={[{ required: true }]}
              >
                <TextArea
                  rows={10}
                  placeholder={`def validate_email(email: str) -> dict:
    import re
    pattern = r'^[\\w.-]+@[\\w.-]+\\.\\w+$'
    is_valid = bool(re.match(pattern, email))
    return {'is_valid': is_valid}`}
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>
            )}

            <Form.Item
              name="inputs"
              label="输入参数 (JSON)"
              extra='格式: {"paramName": {"type": "string", "required": true}}'
            >
              <TextArea
                rows={4}
                placeholder='{"email": {"type": "string", "required": true, "description": "Email address"}}'
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item
              name="outputs"
              label="输出参数 (JSON)"
            >
              <TextArea
                rows={3}
                placeholder='{"is_valid": {"type": "boolean"}}'
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item
              name="semantics"
              label="语义特性"
            >
              <Select mode="multiple" placeholder="选择语义特性">
                <Option value="deterministic">确定性</Option>
                <Option value="pure">纯函数</Option>
                <Option value="no_side_effects">无副作用</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="testCases"
              label="测试用例 (JSON)"
              extra='格式: [{"name": "test", "input": {...}, "expect": {...}}]'
            >
              <TextArea
                rows={4}
                placeholder={`[\n  {\n    "name": "valid email",\n    "input": {"email": "test@example.com"},\n    "expect": {"is_valid": true}\n  }\n]`}
                style={{ fontFamily: 'monospace' }}
              />
            </Form.Item>

            <Form.Item>
              <Space>
                <Button onClick={() => setCurrentStep(0)}>
                  上一步
                </Button>
                <Button type="primary" htmlType="submit" loading={loading}>
                  发布函数
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Card>
      )}

      {currentStep === 2 && publishedId && (
        <Card>
          <div style={{ textAlign: 'center', padding: 40 }}>
            <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a' }} />
            <Title level={3}>发布成功！</Title>
            <Paragraph>
              函数 ID: <Text code>{publishedId}</Text>
            </Paragraph>
            <Space>
              <Button type="primary" href={`/functions/${publishedId}`}>
                查看函数
              </Button>
              <Button onClick={() => {
                setCurrentStep(0);
                setPublishedId(null);
                form.resetFields();
              }}>
                发布另一个
              </Button>
            </Space>
          </div>
        </Card>
      )}
    </div>
  );
}
