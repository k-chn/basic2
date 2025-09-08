"""
Aggregator MCP Server
Coordinates between Resume and Job providers, handles complex queries
"""
import json
import os
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
import asyncio

app = FastAPI(title="Aggregator MCP Server", version="1.0.0")

# MCP Server endpoints
RESUME_SERVER_URL = "http://localhost:8001"
JOB_SERVER_URL = "http://localhost:8002"

class ChatQuery(BaseModel):
    user_id: str
    user_type: str  # "job_seeker" or "employer"
    query: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    response: str
    data: Optional[Dict[str, Any]] = None
    suggestions: List[str] = []

async def call_resume_server(endpoint: str, method: str = "GET", data: Dict = None):
    """Make async call to Resume MCP Server"""
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(f"{RESUME_SERVER_URL}{endpoint}")
            else:
                response = await client.post(f"{RESUME_SERVER_URL}{endpoint}", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

async def call_job_server(endpoint: str, method: str = "GET", data: Dict = None):
    """Make async call to Job MCP Server"""
    async with httpx.AsyncClient() as client:
        try:
            if method == "GET":
                response = await client.get(f"{JOB_SERVER_URL}{endpoint}")
            else:
                response = await client.post(f"{JOB_SERVER_URL}{endpoint}", json=data)
            return response.json()
        except Exception as e:
            return {"error": str(e)}

def parse_job_seeker_query(query: str) -> Dict[str, Any]:
    """Parse job seeker queries and determine intent"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["job", "position", "role", "opportunity"]):
        if any(word in query_lower for word in ["best", "top", "recommend", "suitable"]):
            return {"intent": "find_jobs", "type": "recommendation"}
        elif any(word in query_lower for word in ["how many", "count"]):
            return {"intent": "job_stats", "type": "count"}
    
    elif any(word in query_lower for word in ["skill", "improve", "missing", "gap"]):
        return {"intent": "skill_analysis", "type": "improvement"}
    
    elif any(word in query_lower for word in ["market", "trend", "popular", "demand"]):
        return {"intent": "market_insights", "type": "trends"}
    
    elif any(word in query_lower for word in ["resume", "cv", "profile"]):
        return {"intent": "resume_feedback", "type": "analysis"}
    
    return {"intent": "general", "type": "help"}

def parse_employer_query(query: str) -> Dict[str, Any]:
    """Parse employer queries and determine intent"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["candidate", "applicant", "resume"]):
        if any(word in query_lower for word in ["best", "top", "recommend", "suitable"]):
            return {"intent": "find_candidates", "type": "recommendation"}
        elif any(word in query_lower for word in ["how many", "count"]):
            return {"intent": "candidate_stats", "type": "count"}
    
    elif any(word in query_lower for word in ["skill", "talent", "expertise"]):
        return {"intent": "skill_analysis", "type": "market"}
    
    elif any(word in query_lower for word in ["job", "position", "posting"]):
        return {"intent": "job_management", "type": "analysis"}
    
    return {"intent": "general", "type": "help"}

@app.post("/chat")
async def handle_chat_query(query: ChatQuery):
    """Handle conversational queries from users"""
    
    if query.user_type == "job_seeker":
        intent_data = parse_job_seeker_query(query.query)
        
        if intent_data["intent"] == "find_jobs":
            # Get user's resume data and find matching jobs
            resume_data = await call_resume_server(f"/match-candidates", "POST", {
                "job_description": "general software development",  # This would be user's resume in real scenario
                "top_k": 5,
                "exclude_user_id": query.user_id
            })
            
            job_matches = await call_job_server("/match-jobs", "POST", {
                "resume_text": query.context.get("resume_text", "") if query.context else "",
                "top_k": 5
            })
            
            if "matches" in job_matches:
                response_text = f"I found {len(job_matches['matches'])} great job opportunities for you:\n\n"
                for i, job in enumerate(job_matches["matches"][:3], 1):
                    response_text += f"{i}. **{job['title']}** at {job['company']}\n"
                    response_text += f"   📍 {job['location']} | Match Score: {job['similarity_score']:.2f}\n"
                    response_text += f"   {job['description_snippet']}\n\n"
                
                return ChatResponse(
                    response=response_text,
                    data=job_matches,
                    suggestions=[
                        "Tell me more about the first job",
                        "What skills should I improve?",
                        "Show me remote opportunities"
                    ]
                )
            else:
                return ChatResponse(
                    response="I couldn't find any job matches right now. Try uploading your resume first!",
                    suggestions=["Upload my resume", "View market trends", "Get career advice"]
                )
        
        elif intent_data["intent"] == "skill_analysis":
            # Get market insights about skills
            job_insights = await call_job_server("/insights")
            resume_insights = await call_resume_server("/insights")
            
            response_text = "Based on current market trends, here are the most in-demand skills:\n\n"
            if "popular_skills" in job_insights:
                for i, skill in enumerate(job_insights["popular_skills"][:5], 1):
                    response_text += f"{i}. {skill}\n"
            
            response_text += "\nConsider developing these skills to improve your job prospects!"
            
            return ChatResponse(
                response=response_text,
                data={"job_insights": job_insights, "resume_insights": resume_insights},
                suggestions=[
                    "Find jobs requiring these skills",
                    "Show me learning resources",
                    "Analyze my current skills"
                ]
            )
        
        elif intent_data["intent"] == "market_insights":
            job_insights = await call_job_server("/insights")
            
            response_text = f"📊 **Current Job Market Overview:**\n\n"
            response_text += f"• Total active positions: {job_insights.get('total_jobs', 0)}\n"
            response_text += f"• Top hiring companies: {', '.join(job_insights.get('top_companies', [])[:3])}\n"
            response_text += f"• Popular locations: {', '.join(job_insights.get('locations', [])[:3])}\n"
            
            return ChatResponse(
                response=response_text,
                data=job_insights,
                suggestions=[
                    "Show me jobs at top companies",
                    "Find remote opportunities",
                    "What skills are trending?"
                ]
            )
    
    elif query.user_type == "employer":
        intent_data = parse_employer_query(query.query)
        
        if intent_data["intent"] == "find_candidates":
            # Find matching candidates for employer's jobs
            job_context = query.context.get("job_description", "") if query.context else "software developer"
            
            candidate_matches = await call_resume_server("/match-candidates", "POST", {
                "job_description": job_context,
                "top_k": 5,
                "exclude_user_id": query.user_id
            })
            
            if "matches" in candidate_matches:
                response_text = f"I found {len(candidate_matches['matches'])} qualified candidates:\n\n"
                for i, candidate in enumerate(candidate_matches["matches"][:3], 1):
                    response_text += f"{i}. **{candidate['name']}**\n"
                    response_text += f"   🎯 Match Score: {candidate['similarity_score']:.2f}\n"
                    response_text += f"   💼 Skills: {', '.join(candidate['skills'][:4])}\n"
                    response_text += f"   📝 {candidate['experience_snippet']}\n\n"
                
                return ChatResponse(
                    response=response_text,
                    data=candidate_matches,
                    suggestions=[
                        "Show me more details about candidate 1",
                        "Filter by specific skills",
                        "View candidate portfolios"
                    ]
                )
            else:
                return ChatResponse(
                    response="No matching candidates found. Try posting a job description first!",
                    suggestions=["Post a new job", "View talent market insights", "Adjust job requirements"]
                )
        
        elif intent_data["intent"] == "skill_analysis":
            resume_insights = await call_resume_server("/insights")
            
            response_text = "📈 **Talent Pool Analysis:**\n\n"
            if "top_skills" in resume_insights:
                response_text += "Most common skills in candidate pool:\n"
                for i, skill in enumerate(resume_insights["top_skills"][:5], 1):
                    response_text += f"{i}. {skill}\n"
            
            if "experience_levels" in resume_insights:
                response_text += f"\n**Experience Distribution:**\n"
                for level, count in resume_insights["experience_levels"].items():
                    response_text += f"• {level}: {count} candidates\n"
            
            return ChatResponse(
                response=response_text,
                data=resume_insights,
                suggestions=[
                    "Find candidates with specific skills",
                    "Post job for entry-level candidates",
                    "View market salary trends"
                ]
            )
    
    # Default response
    return ChatResponse(
        response="I'm here to help! I can assist with job matching, skill analysis, and market insights. What would you like to know?",
        suggestions=[
            "Find me suitable jobs" if query.user_type == "job_seeker" else "Show me qualified candidates",
            "Analyze market trends",
            "Get skill recommendations"
        ]
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Aggregator MCP Server"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)