/**
 * 用户中心页面
 */

import { useState, useEffect } from 'react';
import { 
  Card, Tabs, List, Avatar, Button, Badge, Tag, 
  Empty, Spin, Typography, Table, Tooltip, message 
} from 'antd';
import { 
  UserOutlined, CodeOutlined, HistoryOutlined,
  KeyOutlined, ClockCircleOutlined, CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import { api } from '../../api';
import type { User, FunctionSpec } from '../../types';

const { Title, Text } = Typography;
const { TabPane } = Tabs;

interface Execution {
  id: string;
  function_id: string;
  function_name: string;
  status: 'pending' | 'running' | 'success' | 'error';
  created_at: string;
  duration_ms?: number;
}

export default function UserCenter() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [myFunctions, setMyFunctions] = useState<FunctionSpec[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [apiKey, setApiKey] = useState<string | null>(null);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    setLoading(true);
    try {
      const userData = await api.getCurrentUser();
      setUser(userData);

      // 加载我的函数（这里需要后端支持按用户过滤）
      const functionsRes = await api.listFunctions({ limit: 100 });
      setMyFunctions(functionsRes.functions);

      // TODO: 加载执行历史（需要后端 API）
      setExecutions([]);
    } catch (error: any) {
      message.error('加载用户数据失败');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateApiKey = async () => {
    try {
      const res = await api.createApiKey();
      setApiKey(res.api_key);
      message.success('API Key 创建成功');
    } catch (error: any) {
      message.error('创建失败: ' + error.message);
    }
  };

  const getStatusTag = (status: string) => {
    const statusMap: Record<string, { color: string; icon: any }> = {
      pending: { color: 'processing', icon: <ClockCircleOutlined /> },
      running: { color: 'processing', icon: <ClockCircleOutlined /> },
      success: { color: 'success', icon: <CheckCircleOutlined /> },
      error: { color: 'error', icon: <CloseCircleOutlined /> },
    };
    const config = statusMap[status] || statusMap.pending;
    return <Tag color={config.color} icon={config.icon}>{status}</Tag>;
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: 100 }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!user) {
    return <Empty description="请先登录" />;
  }

  const executionColumns = [
    {
      title: '函数',
      dataIndex: 'function_name',
      key: 'function_name',
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => getStatusTag(status),
    },
    {
      title: '执行时间',
      dataIndex: 'created_at',
      key: 'created_at',
    },
    {
      title: '耗时',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      render: (ms?: number) => ms ? `${ms}ms` : '-',
    },
  ];

  return (
    <div className="user-center" style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 24 }}>
          <Avatar size={80} src={user.avatar_url} icon={<UserOutlined />} />
          <div>
            <Title level={3} style={{ margin: 0 }}>{user.username}</Title>
            <Text type="secondary">{user.email}</Text>
            <div style={{ marginTop: 8 }}>
              <Text type="secondary">
                注册时间: {new Date(user.created_at).toLocaleDateString()}
              </Text>
            </div>
          </div>
        </div>
      </Card>

      <Tabs defaultActiveKey="functions" style={{ marginTop: 24 }}>
        <TabPane
          tab={
            <span>
              <CodeOutlined /> 我的函数
              <Badge count={myFunctions.length} style={{ marginLeft: 8 }} />
            </span>
          }
          key="functions"
        >
          <Card>
            {myFunctions.length > 0 ? (
              <List
                grid={{ gutter: 16, xs: 1, sm: 2, md: 3 }}
                dataSource={myFunctions}
                renderItem={(func) => (
                  <List.Item>
                    <Card
                      hoverable
                      title={func.name}
                      extra={<Tag>{func.language.name}</Tag>}
                      onClick={() => window.location.href = `/functions/${func.id}`}
                    >
                      <Paragraph ellipsis={{ rows: 2 }}>
                        {func.description}
                      </Paragraph>
                      <div>
                        {func.tags?.slice(0, 3).map((tag: string) => (
                          <Tag key={tag} size="small">{tag}</Tag>
                        ))}
                      </div>
                    </Card>
                  </List.Item>
                )}
              />
            ) : (
              <Empty description="暂无函数" />
            )}
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <HistoryOutlined /> 执行历史
            </span>
          }
          key="history"
        >
          <Card>
            {executions.length > 0 ? (
              <Table
                dataSource={executions}
                columns={executionColumns}
                rowKey="id"
              />
            ) : (
              <Empty description="暂无执行记录" />
            )}
          </Card>
        </TabPane>

        <TabPane
          tab={
            <span>
              <KeyOutlined /> API 密钥
            </span>
          }
          key="apikeys"
        >
          <Card title="API Key 管理">
            <Paragraph>
              API Key 用于在代码中访问 AgentFuncHub API。
              请妥善保管，不要泄露给他人。
            </Paragraph>

            {apiKey ? (
              <Alert
                message="API Key 已创建"
                description={
                  <div>
                    <code style={{ 
                      background: '#f0f0f0', 
                      padding: 8, 
                      borderRadius: 4,
                      display: 'block',
                      marginTop: 8,
                      wordBreak: 'break-all'
                    }}>
                      {apiKey}
                    </code>
                    <Paragraph type="warning" style={{ marginTop: 16 }}>
                      请立即复制保存！此密钥只会显示一次。
                    </Paragraph>
                  </div>
                }
                type="success"
                showIcon
              />
            ) : (
              <div>
                <Paragraph type="secondary">
                  你还没有 API Key
                </Paragraph>
                <Button
                  type="primary"
                  icon={<KeyOutlined />}
                  onClick={handleCreateApiKey}
                >
                  创建 API Key
                </Button>
              </div>
            )}

            <div style={{ marginTop: 24 }}>
              <Title level={5}>使用示例</Title>
              <pre style={{ background: '#f6f8fa', padding: 16, borderRadius: 6 }}>
                {`from agentfunchub import Client

client = Client(api_key="${apiKey || 'your-api-key'}")

# 搜索函数
results = client.search("验证邮箱")

# 执行函数
result = client.call("validation.email.basic", 
                     email="test@example.com")`}
              </pre>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  );
}
