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
    user_data = redis_client.hgetall(f"user:{username}")
    if not user_data:
        return None
    return UserInDB(**{k.decode(): v.decode() for k, v in user_data.items()})

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
        "disabled": False
    }
    
    redis_client.hmset(f"user:{username}", user_data)
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
                {"role": "system", "content": """당신은 유머러스하고 독특한 명언을 만드는 AI입니다. 
                다음 규칙을 따라 명언을 생성해주세요:
                1. 진지한 것처럼 보이지만 실제로는 전혀 실용적이지 않은 내용이어야 합니다.
                2. 일상적인 것들을 비유나 은유로 표현하되, 완전히 말이 안되게 만들어주세요.
                3. '인생은...'으로 시작하는 패턴을 자주 사용하되, 예상치 못한 결말을 맺어주세요.
                4. 한 문장으로 간결하게 표현해주세요.
                5. 유머러스하고 재미있어야 합니다."""},
                {"role": "user", "content": "새로운 명언을 만들어주세요."}
            ],
            temperature=0.9,
            max_tokens=100,
            top_p=0.95,
            frequency_penalty=0.5,
            presence_penalty=0.5,
            stop=None
        )
        return {"quote": response.choices[0].message.content}
    except Exception as e:
        print(f"Error: {str(e)}")
        return {"error": f"명언을 생성하는 중에 오류가 발생했습니다: {str(e)}"} 