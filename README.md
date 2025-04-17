# 오늘의 아무말 명언

GPT-4를 활용한 유머러스한 명언 생성 서비스입니다. 진지한 것처럼 보이지만 실제로는 전혀 실용적이지 않은 명언들을 생성합니다.

## 기능

- 한 번의 클릭으로 새로운 명언 생성
- 유머러스하고 독특한 명언 생성
- 반응형 디자인
- 애니메이션 효과

## 기술 스택

- Backend: FastAPI, Azure OpenAI GPT-4
- Frontend: React
- Styling: CSS

## 설치 및 실행

1. Python 가상환경 생성 및 활성화:
```bash
python -m venv venv
source venv/bin/activate
```

2. Python 패키지 설치:
```bash
pip install -r requirements.txt
```

3. `.env` 파일 설정:
```
AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint
AZURE_OPENAI_KEY=your-azure-openai-key
```

4. 백엔드 서버 실행:
```bash
uvicorn app.main:app --reload
```

5. 프론트엔드 실행:
```bash
cd frontend
npm install
npm start
```

## 사용 방법

1. 웹 브라우저에서 `http://localhost:3000` 접속
2. "👁️‍🗨️ 명언 보기" 버튼 클릭
3. 새로운 명언이 생성될 때까지 잠시 기다림
4. 원하는 만큼 반복해서 새로운 명언 생성 가능

## 예시 명언

- "인생은 라면이다. 때로는 스프가 부족하고, 때로는 면이 부족하다."
- "행복은 마치 양말과 같다. 한 짝을 잃어버리면 다른 짝도 쓸모가 없다."
- "시간은 마치 휴지통과 같다. 가득 차면 비워야 하지만, 비우면 또 채워진다." 