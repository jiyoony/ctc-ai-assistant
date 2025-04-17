import React, { useState } from 'react';
import './App.css';

function App() {
  const [quote, setQuote] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const getNewQuote = async () => {
    setIsLoading(true);
    setError('');
    try {
      const response = await fetch('http://localhost:8000/quote');
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
        
        <button 
          onClick={getNewQuote} 
          disabled={isLoading}
          className="quote-button"
        >
          {isLoading ? '생각 중...' : '👁️‍🗨️ 명언 보기'}
        </button>

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