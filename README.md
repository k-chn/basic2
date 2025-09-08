
# basic2
=======
# 🤖 MCP Job Matcher

An AI-powered job matching platform built with **Model Context Protocol (MCP)** architecture, featuring intelligent resume-job matching, conversational AI interface, and comprehensive talent analytics.

## 🏗️ System Architecture

### Core Components

1. **MCP Servers** (Backend Services)
   - **Resume Provider Server** (Port 8001): Handles resume processing, candidate matching
   - **Job Provider Server** (Port 8002): Manages job postings, job matching
   - **Aggregator Server** (Port 8003): Orchestrates complex queries, provides conversational AI

2. **MCP Client** (Communication Layer)
   - Unified interface for server communication
   - Mock authentication (Descope-style)
   - Workflow orchestration (Cequence-style)

3. **Frontend** (Streamlit Interface)
   - Dual chatbot interface for job seekers and employers
   - Real-time AI conversations
   - File upload and data visualization

## ✨ Features

### For Job Seekers 🎯
- **PDF Resume Upload**: Automatic text extraction and parsing
- **AI Job Matching**: Semantic similarity-based job recommendations
- **Conversational Interface**: Ask questions like "What jobs fit my skills?"
- **Skill Analysis**: Get insights on market-demanded skills
- **Career Guidance**: Personalized career advice and improvement suggestions

### For Employers 🏢
- **Job Posting**: Easy job description submission
- **Candidate Matching**: Find qualified candidates using AI
- **Talent Analytics**: Insights into skill distribution and market trends
- **Conversational Queries**: Ask "Show me top 10 candidates for this role"
- **Hiring Intelligence**: Data-driven hiring decisions

### Technical Features 🔧
- **Semantic Matching**: Uses SentenceTransformers for intelligent matching
- **PDF Processing**: Automatic resume text extraction
- **Real-time Chat**: Streamlit-based conversational interface
- **Modular Architecture**: Separate MCP servers for scalability
- **Mock Integrations**: Simulated Descope (auth) and Cequence (workflows)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. **Clone and Setup**
```bash
git clone <repository-url>
cd mcp-job-matcher
pip install -r requirements.txt
```

2. **Start MCP Servers**
```bash
python scripts/start_servers.py
```

3. **Launch Frontend**
```bash
streamlit run frontend/app.py
```

4. **Access Application**
- Open browser to `http://localhost:8501`
- Register as either "job_seeker" or "employer"
- Start chatting with the AI assistant!

## 📂 Project Structure

```
mcp-job-matcher/
├── backend/
│   ├── servers/
│   │   ├── resume_server.py      # Resume processing & matching
│   │   ├── job_server.py         # Job management & matching
│   │   └── aggregator_server.py  # Query orchestration
│   └── client/
│       └── mcp_client.py         # Unified client interface
├── frontend/
│   └── app.py                    # Streamlit chatbot interface
├── data/
│   ├── sample_resumes.json       # Sample resume data
│   └── sample_jobs.json          # Sample job postings
├── scripts/
│   └── start_servers.py          # Server startup script
└── requirements.txt              # Python dependencies
```

## 🔧 API Endpoints

### Resume Server (Port 8001)
- `POST /upload-resume` - Upload and process PDF resume
- `POST /match-candidates` - Find matching candidates for job
- `GET /insights` - Get resume analytics

### Job Server (Port 8002)
- `POST /post-job` - Submit new job posting
- `POST /match-jobs` - Find matching jobs for resume
- `GET /insights` - Get job market analytics

### Aggregator Server (Port 8003)
- `POST /chat` - Handle conversational queries
- `GET /health` - Health check for all servers

## 💬 Example Conversations

### Job Seeker Queries
- "Find me the best software engineering jobs"
- "What skills should I learn to get better opportunities?"
- "Show me current market trends in tech"
- "How does my resume compare to market demands?"

### Employer Queries
- "Show me top 5 candidates for my Python developer role"
- "What skills are most common in the talent pool?"
- "Find candidates with machine learning experience"
- "Analyze the experience levels of available candidates"

## 🔐 Authentication & Security

- **Mock Authentication**: Simulates Descope-style user management
- **Role-based Access**: Separate interfaces for job seekers vs employers
- **Session Management**: Secure session handling
- **Data Privacy**: User data isolation and protection

## 🔄 Workflow Orchestration

- **Mock Cequence Integration**: Simulates workflow management
- **Multi-step Queries**: Complex query processing across multiple servers
- **Error Handling**: Robust error management and recovery
- **Rate Limiting**: Prevents abuse and ensures fair usage

## 📊 Analytics & Insights

### Job Market Analytics
- Total active job postings
- Most in-demand skills
- Top hiring companies
- Salary trends and ranges

### Talent Pool Analytics
- Total candidate profiles
- Skill distribution
- Experience level breakdown
- Education backgrounds

## 🛠️ Technology Stack

- **Backend**: FastAPI, Python
- **AI/ML**: SentenceTransformers, scikit-learn
- **Frontend**: Streamlit
- **PDF Processing**: PyPDF2
- **Data Storage**: JSON (easily replaceable with databases)
- **Architecture**: Model Context Protocol (MCP)

## 🔮 Future Enhancements

- **Real Integrations**: Connect with actual Descope and Cequence services
- **Database Integration**: Replace JSON with PostgreSQL/MongoDB
- **Advanced ML**: Implement more sophisticated matching algorithms
- **Real-time Updates**: WebSocket-based real-time notifications
- **Mobile App**: React Native mobile interface
- **Analytics Dashboard**: Advanced reporting and visualization




---
