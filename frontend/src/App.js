import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [quote, setQuote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showLogin, setShowLogin] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('token') || '');

  useEffect(() => {
    if (token) {
      setIsLoggedIn(true);
    }
  }, [token]);

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('http://localhost:8000/token', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();
      
      if (response.ok) {
        setToken(data.access_token);
        localStorage.setItem('token', data.access_token);
        setIsLoggedIn(true);
        setShowLogin(false);
        setError('');
      } else {
        setError('로그인에 실패했습니다. 아이디와 비밀번호를 확인해주세요.');
      }
    } catch (error) {
      console.error('Error:', error);
      setError('서버와의 연결에 문제가 발생했습니다.');
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`http://localhost:8000/register?username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`, {
        method: 'POST',
      });

      if (response.ok) {
        setError('회원가입이 완료되었습니다. 로그인해주세요.');
        setShowLogin(true);
      } else {
        const data = await response.json();
        if (typeof data.detail === 'string') {
          setError(data.detail);
        } else if (Array.isArray(data.detail)) {
          setError(data.detail.map(err => err.msg).join(', '));
        } else {
          setError('회원가입에 실패했습니다. 다시 시도해주세요.');
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setError('서버와의 연결에 문제가 발생했습니다.');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken('');
    setIsLoggedIn(false);
    setShowLogin(true);
    setQuote('');
  };

  const getNewQuote = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/quote', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        setQuote(data.quote);
      }
    } catch (error) {
      console.error('Error:', error);
      setError('서버와의 연결에 문제가 발생했습니다. 잠시 후 다시 시도해주세요.');
    }
    setIsLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>오늘의 아무말 명언</h1>
        <h2>GPT가 전해주는, 전혀 실용적이지 않은 인생의 진리</h2>
        
        {!isLoggedIn ? (
          <div className="auth-container">
            {showLogin ? (
              <form onSubmit={handleLogin} className="auth-form">
                <h3>로그인</h3>
                <input
                  type="text"
                  placeholder="아이디"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
                <input
                  type="password"
                  placeholder="비밀번호"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button type="submit">로그인</button>
                <button type="button" onClick={() => setShowLogin(false)}>
                  회원가입
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegister} className="auth-form">
                <h3>회원가입</h3>
                <input
                  type="text"
                  placeholder="아이디"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
                <input
                  type="password"
                  placeholder="비밀번호"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button type="submit">회원가입</button>
                <button type="button" onClick={() => setShowLogin(true)}>
                  로그인으로 돌아가기
                </button>
              </form>
            )}
          </div>
        ) : (
          <>
            <div className="user-info">
              <span>환영합니다, {username}님!</span>
              <button onClick={handleLogout} className="logout-button">
                로그아웃
              </button>
            </div>
            <button 
              onClick={getNewQuote} 
              disabled={isLoading}
              className="quote-button"
            >
              {isLoading ? '생각 중...' : '👁️‍🗨️ 명언 보기'}
            </button>
          </>
        )}

        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {quote && !error && (
          <div className="quote-box">
            <p className="quote-text">{quote}</p>
          </div>
        )}
      </header>
    </div>
  );
}

export default App; 