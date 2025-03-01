from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


app = FastAPI()

# Clearly load allowed origins from .env
allowed_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MatchRequest(BaseModel):
    resume: str
    job_description: str

@app.get("/")
async def root():
    return {"message": "TalentAI Resume Matcher is live!"}

@app.post("/match")
async def match_resume(request: MatchRequest):
    prompt = f"""
    Analyze the following Resume and Job Description clearly:

    Resume:
    {request.resume}

    Job Description:
    {request.job_description}

    Provide exactly:
    1. Match Percentage (0%-100%)
    2. Matched Skills (bulleted list)
    3. Missing Skills (bulleted list)
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=400,
    )

    result = response.choices[0].message.content.strip()
    return {"analysis": result}
