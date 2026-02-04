/**
 * 主应用组件
 */

import { useState, useEffect } from 'react';
import { Layout, Menu, Input, Button, Avatar, Dropdown } from 'antd';
import {
  SearchOutlined,
  HomeOutlined,
  UserOutlined,
  LogoutOutlined,
  GithubOutlined,
  CodeOutlined,
} from '@ant-design/icons';
import { User } from './types';
import { api } from './api';
import FunctionList from './components/FunctionList';
import FunctionDetail from './components/FunctionDetail';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Search } = Input;

type View = 'home' | 'search' | 'detail' | 'profile';

function App() {
  const [view, setView] = useState<View>('home');
  const [user, setUser] = useState<User | null>(null);
  const [selectedFunction, setSelectedFunction] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  // 检查登录状态
  useEffect(() => {
    const token = api.getToken();
    if (token) {
      api.getCurrentUser()
        .then(setUser)
        .catch(() => {
          api.setToken(null);
        });
    }
  }, []);

  // 处理 GitHub OAuth 回调
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('access_token');
    if (token) {
      api.setToken(token);
      window.history.replaceState({}, '', window.location.pathname);
      api.getCurrentUser().then(setUser);
    }
  }, []);

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    setView('search');
  };

  const handleFunctionClick = (id: string) => {
    setSelectedFunction(id);
    setView('detail');
  };

  const handleLogin = () => {
    // 打开 GitHub OAuth 登录
    window.location.href = 'http://localhost:8000/auth/github/login';
  };

  const handleLogout = () => {
    api.setToken(null);
    setUser(null);
    setView('home');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人中心',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="header-left">
          <div className="logo" onClick={() => setView('home')}>
            <CodeOutlined />
            <span>AgentFuncHub</span>
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[view]}
            items={[
              { key: 'home', icon: <HomeOutlined />, label: '首页' },
              { key: 'search', icon: <SearchOutlined />, label: '搜索' },
            ]}
            onClick={({ key }) => setView(key as View)}
          />
        </div>

        <div className="header-center">
          <Search
            placeholder="搜索函数..."
            allowClear
            enterButton
            size="middle"
            onSearch={handleSearch}
            style={{ width: 400 }}
          />
        </div>

        <div className="header-right">
          {user ? (
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div className="user-info">
                <Avatar src={user.avatar_url} icon={<UserOutlined />} />
                <span>{user.username}</span>
              </div>
            </Dropdown>
          ) : (
            <Button
              type="primary"
              icon={<GithubOutlined />}
              onClick={handleLogin}
            >
              GitHub 登录
            </Button>
          )}
        </div>
      </Header>

      <Content className="app-content">
        {view === 'home' && (
          <div className="home-view">
            <div className="hero">
              <h1>面向 Agent 的函数级代码共享社区</h1>
              <p>发现和分享可复用的 AI Agent 函数</p>
              <Search
                placeholder="搜索函数，例如：验证邮箱、格式化日期..."
                enterButton="搜索"
                size="large"
                onSearch={handleSearch}
                style={{ width: 600, maxWidth: '90%' }}
              />
            </div>
            <FunctionList onFunctionClick={handleFunctionClick} />
          </div>
        )}

        {view === 'search' && (
          <div className="search-view">
            <h2>搜索结果: "{searchQuery}"</h2>
            <FunctionList
              searchQuery={searchQuery}
              onFunctionClick={handleFunctionClick}
            />
          </div>
        )}

        {view === 'detail' && selectedFunction && (
          <FunctionDetail
            functionId={selectedFunction}
            onBack={() => setView('home')}
          />
        )}
      </Content>

      <Footer className="app-footer">
        AgentFuncHub ©2026 - FunctionSpec v0.1
      </Footer>
    </Layout>
  );
}

export default App;
