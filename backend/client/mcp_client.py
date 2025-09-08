"""
MCP Client
Handles communication with MCP servers and provides unified interface
"""
import httpx
import asyncio
from typing import Dict, Any, Optional, List
import json

class MCPClient:
    def __init__(self):
        self.resume_server_url = "http://localhost:8001"
        self.job_server_url = "http://localhost:8002"
        self.aggregator_url = "http://localhost:8003"
        
    async def _make_request(self, url: str, method: str = "GET", data: Dict = None, files: Dict = None):
        """Make async HTTP request"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    if files:
                        response = await client.post(url, data=data, files=files)
                    else:
                        response = await client.post(url, json=data)
                
                if response.status_code == 200:
                    return {"success": True, "data": response.json()}
                else:
                    return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            except Exception as e:
                return {"success": False, "error": str(e)}
    
    # Resume Server Methods
    async def upload_resume(self, user_id: str, file_path: str):
        """Upload resume to Resume MCP Server"""
        with open(file_path, 'rb') as f:
            files = {"file": f}
            data = {"user_id": user_id}
            return await self._make_request(
                f"{self.resume_server_url}/upload-resume",
                method="POST",
                data=data,
                files=files
            )
    
    async def find_matching_candidates(self, job_description: str, top_k: int = 10, exclude_user_id: str = None):
        """Find candidates matching a job description"""
        data = {
            "job_description": job_description,
            "top_k": top_k,
            "exclude_user_id": exclude_user_id
        }
        return await self._make_request(
            f"{self.resume_server_url}/match-candidates",
            method="POST",
            data=data
        )
    
    async def get_resume_insights(self):
        """Get aggregated resume insights"""
        return await self._make_request(f"{self.resume_server_url}/insights")
    
    # Job Server Methods
    async def post_job(self, job_data: Dict[str, Any]):
        """Post a new job to Job MCP Server"""
        return await self._make_request(
            f"{self.job_server_url}/post-job",
            method="POST",
            data=job_data
        )
    
    async def find_matching_jobs(self, resume_text: str, top_k: int = 10, exclude_employer_id: str = None):
        """Find jobs matching a resume"""
        data = {
            "resume_text": resume_text,
            "top_k": top_k,
            "exclude_employer_id": exclude_employer_id
        }
        return await self._make_request(
            f"{self.job_server_url}/match-jobs",
            method="POST",
            data=data
        )
    
    async def get_job_insights(self):
        """Get aggregated job insights"""
        return await self._make_request(f"{self.job_server_url}/insights")
    
    async def get_all_jobs(self, employer_id: str = None):
        """Get all jobs, optionally filtered by employer"""
        url = f"{self.job_server_url}/jobs"
        if employer_id:
            url += f"?employer_id={employer_id}"
        return await self._make_request(url)
    
    # Aggregator Methods
    async def chat_query(self, user_id: str, user_type: str, query: str, context: Dict = None):
        """Send chat query to Aggregator MCP Server"""
        data = {
            "user_id": user_id,
            "user_type": user_type,
            "query": query,
            "context": context or {}
        }
        return await self._make_request(
            f"{self.aggregator_url}/chat",
            method="POST",
            data=data
        )
    
    # Health Checks
    async def check_all_servers(self):
        """Check health of all MCP servers"""
        servers = {
            "resume_server": f"{self.resume_server_url}/health",
            "job_server": f"{self.job_server_url}/health",
            "aggregator": f"{self.aggregator_url}/health"
        }
        
        results = {}
        for name, url in servers.items():
            result = await self._make_request(url)
            results[name] = result
        
        return results

# Mock Authentication (Descope-style)
class MockAuth:
    def __init__(self):
        self.users = {}
        self.sessions = {}
    
    def register_user(self, email: str, password: str, user_type: str):
        """Register a new user"""
        if email in self.users:
            return {"success": False, "error": "User already exists"}
        
        user_id = f"user_{len(self.users) + 1}"
        self.users[email] = {
            "user_id": user_id,
            "email": email,
            "password": password,  # In real app, this would be hashed
            "user_type": user_type,
            "created_at": "2024-01-01"
        }
        
        return {"success": True, "user_id": user_id}
    
    def login_user(self, email: str, password: str):
        """Login user and create session"""
        if email not in self.users:
            return {"success": False, "error": "User not found"}
        
        user = self.users[email]
        if user["password"] != password:
            return {"success": False, "error": "Invalid password"}
        
        session_token = f"session_{user['user_id']}_{len(self.sessions)}"
        self.sessions[session_token] = {
            "user_id": user["user_id"],
            "email": email,
            "user_type": user["user_type"]
        }
        
        return {
            "success": True,
            "session_token": session_token,
            "user": {
                "user_id": user["user_id"],
                "email": email,
                "user_type": user["user_type"]
            }
        }
    
    def validate_session(self, session_token: str):
        """Validate session token"""
        if session_token in self.sessions:
            return {"success": True, "user": self.sessions[session_token]}
        return {"success": False, "error": "Invalid session"}

# Mock Workflow Orchestration (Cequence-style)
class MockWorkflowOrchestrator:
    def __init__(self):
        self.workflows = {}
        self.execution_history = []
    
    def create_workflow(self, name: str, steps: List[Dict]):
        """Create a new workflow"""
        workflow_id = f"workflow_{len(self.workflows) + 1}"
        self.workflows[workflow_id] = {
            "name": name,
            "steps": steps,
            "created_at": "2024-01-01"
        }
        return {"workflow_id": workflow_id}
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict):
        """Execute a workflow"""
        if workflow_id not in self.workflows:
            return {"success": False, "error": "Workflow not found"}
        
        workflow = self.workflows[workflow_id]
        execution_id = f"exec_{len(self.execution_history) + 1}"
        
        # Mock execution
        results = []
        for step in workflow["steps"]:
            step_result = {
                "step_name": step["name"],
                "status": "completed",
                "output": f"Mock output for {step['name']}"
            }
            results.append(step_result)
        
        execution_record = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "input_data": input_data,
            "results": results,
            "status": "completed",
            "executed_at": "2024-01-01"
        }
        
        self.execution_history.append(execution_record)
        
        return {
            "success": True,
            "execution_id": execution_id,
            "results": results
        }

# Initialize global instances
mcp_client = MCPClient()
auth_service = MockAuth()
workflow_orchestrator = MockWorkflowOrchestrator()