import os
import requests
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from utils import extract_text_from_pdf

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

# === New upload endpoints clearly added === #

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)
    return {"resume_text": text}

@app.post("/upload-jobdesc")
async def upload_jobdesc(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    text = extract_text_from_pdf(pdf_bytes)
    return {"jobdesc_text": text}

class PairMatchRequest(BaseModel):
    resume: str
    job_description: str

class BulkPairMatchRequest(BaseModel):
    pairs: list[PairMatchRequest]

@app.post("/bulk-match-pairs")
async def bulk_match_pairs(request: BulkPairMatchRequest):
    analyses = []
    for pair in request.pairs:
        prompt = f"""
        Analyze clearly:

        Resume:
        {pair.resume}

        Job Description:
        {pair.job_description}

        Provide exactly:
        1. Match Percentage (0%-100%)
        2. Matched Skills
        3. Missing Skills
        """
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        result = response.choices[0].message.content.strip()
        analyses.append(result)

    return {"bulk_analyses": analyses}

class BulkSingleJDRequest(BaseModel):
    job_description: str
    resumes: list[str]

@app.post("/bulk-match-one-jd")
async def bulk_match_single_jd(request: BulkSingleJDRequest):
    analyses = []
    for resume in request.resumes:
        prompt = f"""
        Analyze clearly:

        Resume:
        {resume}

        Job Description:
        {request.job_description}

        Provide exactly:
        1. Match Percentage (0%-100%)
        2. Matched Skills
        3. Missing Skills
        """
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=400,
        )
        result = response.choices[0].message.content.strip()
        analyses.append(result)

    return {"bulk_analyses": analyses}

class URLRequest(BaseModel):
    url: str

@app.post("/jobdesc-from-url")
async def jobdesc_from_url(request: URLRequest):
    try:
        response = requests.get(request.url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Clearly get text from page (simple extraction)
        texts = soup.stripped_strings
        full_text = " ".join(texts)

        # Optional: Use GPT for cleaner extraction
        prompt = f"Extract clearly the full Job Description text from this raw webpage content:\n{full_text}\n\nClearly output only the Job Description:"
        gpt_response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600,
        )

        jd_text = gpt_response.choices[0].message.content.strip()
        return {"jobdesc_text": jd_text}

    except Exception as e:
        return {"error": str(e)}