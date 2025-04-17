from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import redis
import os
from dotenv import load_dotenv
from openai import AzureOpenAI
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
# 환경 변수 로드
load_dotenv()

# Redis 연결
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0
)

# Azure OpenAI 설정
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-05-15",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프론트엔드 URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 보안 설정
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChatRequest(BaseModel):
    message: str

class QuoteRequest(BaseModel):
    pass

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    try:
        user_data = redis_client.hgetall(f"user:{username}")
        if not user_data:
            return None
        
        # bytes 타입을 문자열로 변환하고 딕셔너리 생성
        user_dict = {}
        for key, value in user_data.items():
            try:
                user_dict[key.decode('utf-8')] = value.decode('utf-8')
            except (UnicodeDecodeError, AttributeError):
                user_dict[key.decode('utf-8')] = str(value)
        
        # disabled 값을 boolean으로 변환
        user_dict["disabled"] = user_dict.get("disabled", "False").lower() == "true"
        
        return UserInDB(**user_dict)
    except Exception as e:
        print(f"Error in get_user: {str(e)}")
        return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    user = get_user(username)
    if user is None:
        raise credentials_exception
    return user

@app.post("/register")
async def register(username: str, password: str):
    if get_user(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    hashed_password = get_password_hash(password)
    user_data = {
        "username": username,
        "hashed_password": hashed_password,
        "disabled": "False"  # boolean을 문자열로 변환
    }
    
    # hmset 대신 hset를 사용
    for key, value in user_data.items():
        redis_client.hset(f"user:{username}", key, value)
    return {"message": "User registered successfully"}

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. You should only answer questions related to the service."},
                {"role": "user", "content": request.message}
            ],
            temperature=0.7,
            max_tokens=800,
            top_p=0.95,
            frequency_penalty=0,
            presence_penalty=0,
            stop=None
        )
        return {"response": response.choices[0].message.content}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@app.get("/quote")
async def get_quote():
    print("quote")
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """당신은 기발하고 유머러스한 철학자 AI입니다.  
                다음 지침에 따라 한 문장으로 된 '명언'을 생성하세요:

                1. 처음엔 진지해 보이지만, 읽고 나면 웃기거나 허무하거나 기발해야 합니다.
                2. 일상적인 사물이나 상황을 철학적인 은유로 표현하세요.
                3. '인생은'으로 시작할 수도 있지만, 다양한 시작 방식도 활용하세요.
                4. 문장은 하나만, 절대 설명이나 해석은 하지 마세요.
                5. 독자가 '이게 뭐야' 하면서도 살짝 고개를 끄덕일 수 있는 위트를 담아주세요.
                6. 가능한 다양한 스타일을 섞어 반복되지 않게 해주세요.
                7. 생성한 명언에 대한 간단한 해석도 제공해 주세요. 명언의 의미가 무엇인지, 왜 그 명언이 중요한지 간단히 설명하세요.
                8. 명언과 해석을 JSON 형식으로 반환해주세요.
                예시:
                {
                    "quote": "인생은 마치 냉장고 속의 요구르트 같다. 언제 곰팡이가 필지 모른다.",
                    "interpretation": "이 명언은 인생의 불확실성을 요구르트의 곰팡이로 비유한 것입니다. 하지만 실제로는 아무런 의미가 없습니다. 그냥 냉장고를 자주 확인하라는 의미일까요?"
                }"""},
                {"role": "user", "content": "새로운 명언을 만들어주세요."}
            ],
            temperature=0.9,
            max_tokens=200,
            top_p=0.95,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stop=None
        )
        # Parse the JSON response from GPT
        import json
        content = response.choices[0].message.content
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError:
            # If parsing fails, return a default error response
            return {
                "quote": "오류가 발생했습니다. 다시 시도해주세요.",
                "interpretation": "명언을 생성하는 중에 문제가 발생했습니다."
            }
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": f"명언을 생성하는 중에 오류가 발생했습니다: {str(e)}"} 