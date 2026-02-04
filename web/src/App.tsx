/**
 * 主应用组件 (带路由)
 */

import { useState, useEffect } from 'react';
import { Layout, Menu, Input, Button, Avatar, Dropdown, Badge } from 'antd';
import {
  SearchOutlined,
  HomeOutlined,
  UserOutlined,
  LogoutOutlined,
  GithubOutlined,
  CodeOutlined,
  PlusOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { BrowserRouter as Router, Routes, Route, Link, useLocation, useNavigate } from 'react-router-dom';
import { User } from './types';
import { api } from './api';
import FunctionList from './components/FunctionList';
import FunctionDetail from './components/FunctionDetail';
import PublishFunction from './components/pages/PublishFunction';
import UserCenter from './components/pages/UserCenter';
import './App.css';

const { Header, Content, Footer } = Layout;
const { Search } = Input;

// 主应用内容
function AppContent() {
  const location = useLocation();
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [selectedFunction, setSelectedFunction] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

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
    navigate(`/?search=${encodeURIComponent(value)}`);
  };

  const handleFunctionClick = (id: string) => {
    navigate(`/functions/${id}`);
  };

  const handleLogin = () => {
    window.location.href = 'http://localhost:8000/auth/github/login';
  };

  const handleLogout = () => {
    api.setToken(null);
    setUser(null);
    navigate('/');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: <Link to="/user">个人中心</Link>,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: <Link to="/">首页</Link> },
    { key: '/publish', icon: <PlusOutlined />, label: <Link to="/publish">发布函数</Link> },
  ];

  const currentKey = location.pathname === '/' ? '/' : location.pathname;

  return (
    <Layout className="app-layout">
      <Header className="app-header">
        <div className="header-left">
          <div className="logo" onClick={() => navigate('/')}>
            <CodeOutlined />
            <span>AgentFuncHub</span>
          </div>
          <Menu
            theme="dark"
            mode="horizontal"
            selectedKeys={[currentKey]}
            items={menuItems}
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
              登录
            </Button>
          )}
        </div>
      </Header>

      <Content className="app-content">
        <Routes>
          <Route 
            path="/" 
            element={
              <HomeView 
                searchQuery={searchQuery}
                onFunctionClick={handleFunctionClick}
              />
            } 
          />
          <Route 
            path="/functions/:id" 
            element={<FunctionDetailView onBack={() => navigate('/')} />} 
          />
          <Route path="/publish" element={<PublishFunction />} />
          <Route path="/user" element={<UserCenter />} />
        </Routes>
      </Content>

      <Footer className="app-footer">
        AgentFuncHub ©2026 - FunctionSpec v0.1
      </Footer>
    </Layout>
  );
}

// 首页视图
function HomeView({ 
  searchQuery, 
  onFunctionClick 
}: { 
  searchQuery: string;
  onFunctionClick: (id: string) => void;
}) {
  const location = useLocation();
  const urlParams = new URLSearchParams(location.search);
  const searchFromUrl = urlParams.get('search') || '';

  return (
    <div className="home-view">
      {!searchFromUrl && (
        <div className="hero">
          <h1>面向 Agent 的函数级代码共享社区</h1>
          <p>发现和分享可复用的 AI Agent 函数</p>
        </div>
      )}
      
      <div style={{ marginBottom: 24 }}>
        {searchFromUrl ? (
          <h2>搜索结果: "{searchFromUrl}"</h2>
        ) : (
          <h2>热门函数</h2>
        )}
      </div>
      
      <FunctionList 
        searchQuery={searchFromUrl}
        onFunctionClick={onFunctionClick} 
      />
    </div>
  );
}

// 函数详情视图
function FunctionDetailView({ onBack }: { onBack: () => void }) {
  const location = useLocation();
  const id = location.pathname.split('/').pop();
  
  if (!id) return null;
  
  return <FunctionDetail functionId={id} onBack={onBack} />;
}

// 主应用
function App() {
  return (
    <Router>
      <AppContent />
    </Router>
  );
}

export default App;
