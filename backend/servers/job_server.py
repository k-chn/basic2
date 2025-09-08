"""
Job Provider MCP Server
Handles job description aggregation, processing, and insights
"""
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import uuid

app = FastAPI(title="Job Provider MCP Server", version="1.0.0")

# Initialize sentence transformer for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Data storage
JOBS_FILE = "data/jobs.json"
os.makedirs("data", exist_ok=True)

class JobPosting(BaseModel):
    id: str
    employer_id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    location: str
    salary_range: Optional[str] = None
    job_type: str = "Full-time"
    embedding: Optional[List[float]] = None

class JobInsight(BaseModel):
    total_jobs: int
    top_companies: List[str]
    popular_skills: List[str]
    job_types: Dict[str, int]
    locations: List[str]

class JobMatchRequest(BaseModel):
    resume_text: str
    top_k: int = 10
    exclude_employer_id: Optional[str] = None

class JobSubmission(BaseModel):
    employer_id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    location: str
    salary_range: Optional[str] = None
    job_type: str = "Full-time"

def load_jobs() -> List[JobPosting]:
    """Load jobs from JSON file"""
    if not os.path.exists(JOBS_FILE):
        return []
    
    try:
        with open(JOBS_FILE, 'r') as f:
            data = json.load(f)
            return [JobPosting(**job) for job in data]
    except:
        return []

def save_jobs(jobs: List[JobPosting]):
    """Save jobs to JSON file"""
    with open(JOBS_FILE, 'w') as f:
        json.dump([job.dict() for job in jobs], f, indent=2)

def extract_skills_from_job(description: str, requirements: List[str]) -> List[str]:
    """Extract skills from job description and requirements"""
    text = (description + " " + " ".join(requirements)).lower()
    
    # Common tech skills to look for
    common_skills = [
        "python", "java", "javascript", "react", "node.js", "sql", "aws", "docker",
        "kubernetes", "git", "machine learning", "data analysis", "project management",
        "communication", "leadership", "problem solving", "teamwork", "agile", "scrum"
    ]
    
    found_skills = []
    for skill in common_skills:
        if skill in text:
            found_skills.append(skill.title())
    
    return found_skills

@app.post("/post-job")
async def post_job(job_data: JobSubmission):
    """Post a new job"""
    # Generate embedding for job description + requirements
    job_text = f"{job_data.title} {job_data.description} {' '.join(job_data.requirements)}"
    embedding = model.encode(job_text).tolist()
    
    # Create job posting
    job = JobPosting(
        id=str(uuid.uuid4()),
        employer_id=job_data.employer_id,
        title=job_data.title,
        company=job_data.company,
        description=job_data.description,
        requirements=job_data.requirements,
        location=job_data.location,
        salary_range=job_data.salary_range,
        job_type=job_data.job_type,
        embedding=embedding
    )
    
    # Load existing jobs
    jobs = load_jobs()
    
    # Add new job
    jobs.append(job)
    
    # Save jobs
    save_jobs(jobs)
    
    return {"message": "Job posted successfully", "job_id": job.id}

@app.post("/match-jobs")
async def match_jobs(request: JobMatchRequest):
    """Find matching jobs for a resume"""
    jobs = load_jobs()
    
    if not jobs:
        return {"matches": [], "message": "No jobs available"}
    
    # Filter out jobs from excluded employer
    if request.exclude_employer_id:
        jobs = [j for j in jobs if j.employer_id != request.exclude_employer_id]
    
    # Generate embedding for resume
    resume_embedding = model.encode(request.resume_text)
    
    # Calculate similarities
    matches = []
    for job in jobs:
        if job.embedding:
            similarity = cosine_similarity(
                [resume_embedding], 
                [job.embedding]
            )[0][0]
            
            matches.append({
                "job_id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "similarity_score": float(similarity),
                "description_snippet": job.description[:200] + "..." if len(job.description) > 200 else job.description,
                "requirements": job.requirements[:5],  # Top 5 requirements
                "salary_range": job.salary_range
            })
    
    # Sort by similarity and return top k
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return {
        "matches": matches[:request.top_k],
        "total_jobs": len(jobs)
    }

@app.get("/insights")
async def get_job_insights():
    """Get aggregated insights about all jobs"""
    jobs = load_jobs()
    
    if not jobs:
        return JobInsight(
            total_jobs=0,
            top_companies=[],
            popular_skills=[],
            job_types={},
            locations=[]
        )
    
    # Top companies
    company_counts = {}
    for job in jobs:
        company_counts[job.company] = company_counts.get(job.company, 0) + 1
    
    top_companies = sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_companies = [company[0] for company in top_companies]
    
    # Popular skills
    all_skills = []
    for job in jobs:
        skills = extract_skills_from_job(job.description, job.requirements)
        all_skills.extend(skills)
    
    skill_counts = {}
    for skill in all_skills:
        skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    popular_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    popular_skills = [skill[0] for skill in popular_skills]
    
    # Job types
    job_types = {}
    for job in jobs:
        job_types[job.job_type] = job_types.get(job.job_type, 0) + 1
    
    # Locations
    locations = list(set([job.location for job in jobs]))[:10]
    
    return JobInsight(
        total_jobs=len(jobs),
        top_companies=top_companies,
        popular_skills=popular_skills,
        job_types=job_types,
        locations=locations
    )

@app.get("/jobs")
async def get_all_jobs(employer_id: Optional[str] = None):
    """Get all jobs, optionally filtered by employer"""
    jobs = load_jobs()
    
    if employer_id:
        jobs = [job for job in jobs if job.employer_id == employer_id]
    
    return {
        "jobs": [
            {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "location": job.location,
                "job_type": job.job_type,
                "salary_range": job.salary_range
            }
            for job in jobs
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Job Provider MCP Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)