"""
Resume Provider MCP Server
Handles resume data aggregation, processing, and insights
"""
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import PyPDF2
from sentence_transformers import SentenceTransformer
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import uuid

app = FastAPI(title="Resume Provider MCP Server", version="1.0.0")

# Initialize sentence transformer for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Data storage
RESUMES_FILE = "data/resumes.json"
os.makedirs("data", exist_ok=True)

class Resume(BaseModel):
    id: str
    user_id: str
    name: str
    email: str
    skills: List[str]
    experience: str
    education: str
    raw_text: str
    embedding: Optional[List[float]] = None

class ResumeInsight(BaseModel):
    total_resumes: int
    top_skills: List[str]
    experience_levels: Dict[str, int]
    education_backgrounds: List[str]

class MatchRequest(BaseModel):
    job_description: str
    top_k: int = 10
    exclude_user_id: Optional[str] = None

def load_resumes() -> List[Resume]:
    """Load resumes from JSON file"""
    if not os.path.exists(RESUMES_FILE):
        return []
    
    try:
        with open(RESUMES_FILE, 'r') as f:
            data = json.load(f)
            return [Resume(**resume) for resume in data]
    except:
        return []

def save_resumes(resumes: List[Resume]):
    """Save resumes to JSON file"""
    with open(RESUMES_FILE, 'w') as f:
        json.dump([resume.dict() for resume in resumes], f, indent=2)

def extract_text_from_pdf(pdf_file) -> str:
    """Extract text from uploaded PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing PDF: {str(e)}")

def parse_resume_text(text: str) -> Dict[str, Any]:
    """Basic resume parsing from text"""
    lines = text.split('\n')
    
    # Simple parsing logic (can be enhanced)
    name = lines[0] if lines else "Unknown"
    email = ""
    skills = []
    experience = ""
    education = ""
    
    current_section = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect email
        if "@" in line and "." in line:
            email = line
            
        # Detect sections
        if any(keyword in line.lower() for keyword in ['skill', 'technical']):
            current_section = "skills"
        elif any(keyword in line.lower() for keyword in ['experience', 'work', 'employment']):
            current_section = "experience"
        elif any(keyword in line.lower() for keyword in ['education', 'degree', 'university']):
            current_section = "education"
        else:
            # Add content to current section
            if current_section == "skills":
                # Extract skills (simple comma-separated or bullet points)
                if "," in line:
                    skills.extend([s.strip() for s in line.split(",")])
                elif line.startswith("•") or line.startswith("-"):
                    skills.append(line[1:].strip())
            elif current_section == "experience":
                experience += line + " "
            elif current_section == "education":
                education += line + " "
    
    return {
        "name": name,
        "email": email,
        "skills": list(set(skills)) if skills else ["General"],
        "experience": experience.strip(),
        "education": education.strip()
    }

@app.post("/upload-resume")
async def upload_resume(
    user_id: str,
    file: UploadFile = File(...)
):
    """Upload and process a resume"""
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Extract text from PDF
    raw_text = extract_text_from_pdf(file.file)
    
    # Parse resume
    parsed_data = parse_resume_text(raw_text)
    
    # Generate embedding
    embedding = model.encode(raw_text).tolist()
    
    # Create resume object
    resume = Resume(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=parsed_data["name"],
        email=parsed_data["email"],
        skills=parsed_data["skills"],
        experience=parsed_data["experience"],
        education=parsed_data["education"],
        raw_text=raw_text,
        embedding=embedding
    )
    
    # Load existing resumes
    resumes = load_resumes()
    
    # Remove existing resume for this user
    resumes = [r for r in resumes if r.user_id != user_id]
    
    # Add new resume
    resumes.append(resume)
    
    # Save resumes
    save_resumes(resumes)
    
    return {"message": "Resume uploaded successfully", "resume_id": resume.id}

@app.post("/match-candidates")
async def match_candidates(request: MatchRequest):
    """Find matching candidates for a job description"""
    resumes = load_resumes()
    
    if not resumes:
        return {"matches": [], "message": "No resumes available"}
    
    # Filter out excluded user
    if request.exclude_user_id:
        resumes = [r for r in resumes if r.user_id != request.exclude_user_id]
    
    # Generate embedding for job description
    job_embedding = model.encode(request.job_description)
    
    # Calculate similarities
    matches = []
    for resume in resumes:
        if resume.embedding:
            similarity = cosine_similarity(
                [job_embedding], 
                [resume.embedding]
            )[0][0]
            
            matches.append({
                "resume_id": resume.id,
                "name": resume.name,
                "skills": resume.skills,
                "similarity_score": float(similarity),
                "experience_snippet": resume.experience[:200] + "..." if len(resume.experience) > 200 else resume.experience
            })
    
    # Sort by similarity and return top k
    matches.sort(key=lambda x: x["similarity_score"], reverse=True)
    
    return {
        "matches": matches[:request.top_k],
        "total_candidates": len(resumes)
    }

@app.get("/insights")
async def get_resume_insights():
    """Get aggregated insights about all resumes"""
    resumes = load_resumes()
    
    if not resumes:
        return ResumeInsight(
            total_resumes=0,
            top_skills=[],
            experience_levels={},
            education_backgrounds=[]
        )
    
    # Aggregate skills
    all_skills = []
    for resume in resumes:
        all_skills.extend(resume.skills)
    
    skill_counts = {}
    for skill in all_skills:
        skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_skills = [skill[0] for skill in top_skills]
    
    # Experience levels (simple categorization)
    experience_levels = {"Entry": 0, "Mid": 0, "Senior": 0}
    for resume in resumes:
        exp_text = resume.experience.lower()
        if any(word in exp_text for word in ["senior", "lead", "manager", "director"]):
            experience_levels["Senior"] += 1
        elif any(word in exp_text for word in ["years", "experience"]) and not any(word in exp_text for word in ["entry", "junior", "intern"]):
            experience_levels["Mid"] += 1
        else:
            experience_levels["Entry"] += 1
    
    # Education backgrounds
    education_backgrounds = list(set([resume.education[:50] + "..." if len(resume.education) > 50 else resume.education for resume in resumes if resume.education]))
    
    return ResumeInsight(
        total_resumes=len(resumes),
        top_skills=top_skills,
        experience_levels=experience_levels,
        education_backgrounds=education_backgrounds[:10]
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Resume Provider MCP Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)