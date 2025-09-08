"""
Streamlit Frontend for MCP Job Matcher
Provides chatbot interface for both job seekers and employers
"""
import streamlit as st
import asyncio
import sys
import os
import tempfile
import json
from datetime import datetime

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from client.mcp_client import mcp_client, auth_service, workflow_orchestrator

# Page configuration
st.set_page_config(
    page_title="MCP Job Matcher",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
    
    .user-message {
        background-color: #f0f2f6;
        border-left-color: #667eea;
    }
    
    .bot-message {
        background-color: #e8f4fd;
        border-left-color: #1f77b4;
    }
    
    .sidebar-section {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_data' not in st.session_state:
    st.session_state.user_data = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'resume_uploaded' not in st.session_state:
    st.session_state.resume_uploaded = False

def run_async(coro):
    """Helper to run async functions in Streamlit"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

def login_page():
    """Login/Registration page"""
    st.markdown('<div class="main-header"><h1>🤖 MCP Job Matcher</h1><p>AI-Powered Job Matching Platform</p></div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        if st.button("Login", type="primary"):
            if email and password:
                result = auth_service.login_user(email, password)
                if result["success"]:
                    st.session_state.authenticated = True
                    st.session_state.user_data = result["user"]
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(result["error"])
            else:
                st.error("Please fill in all fields")
    
    with tab2:
        st.subheader("Create New Account")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_password")
        user_type = st.selectbox("I am a:", ["job_seeker", "employer"])
        
        if st.button("Register", type="primary"):
            if reg_email and reg_password:
                result = auth_service.register_user(reg_email, reg_password, user_type)
                if result["success"]:
                    st.success("Registration successful! Please login.")
                else:
                    st.error(result["error"])
            else:
                st.error("Please fill in all fields")

def job_seeker_dashboard():
    """Dashboard for job seekers"""
    st.markdown('<div class="main-header"><h1>🎯 Job Seeker Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("👤 Profile")
        st.write(f"**Email:** {st.session_state.user_data['email']}")
        st.write(f"**User ID:** {st.session_state.user_data['user_id']}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.chat_history = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Resume Upload
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📄 Upload Resume")
        uploaded_file = st.file_uploader("Choose PDF file", type="pdf")
        
        if uploaded_file and st.button("Upload Resume"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                tmp_file_path = tmp_file.name
            
            try:
                result = run_async(mcp_client.upload_resume(
                    st.session_state.user_data['user_id'], 
                    tmp_file_path
                ))
                
                if result["success"]:
                    st.success("Resume uploaded successfully!")
                    st.session_state.resume_uploaded = True
                else:
                    st.error(f"Upload failed: {result['error']}")
            except Exception as e:
                st.error(f"Error: {str(e)}")
            finally:
                os.unlink(tmp_file_path)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick Actions
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Actions")
        if st.button("Find Jobs for Me"):
            st.session_state.chat_history.append({
                "user": "Find me the best jobs that match my skills",
                "timestamp": datetime.now().strftime("%H:%M")
            })
        
        if st.button("Market Insights"):
            st.session_state.chat_history.append({
                "user": "Show me current job market trends",
                "timestamp": datetime.now().strftime("%H:%M")
            })
        
        if st.button("Skill Analysis"):
            st.session_state.chat_history.append({
                "user": "What skills should I improve to get better jobs?",
                "timestamp": datetime.now().strftime("%H:%M")
            })
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat with AI Assistant")
        
        # Chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if "user" in message:
                    st.markdown(f'<div class="chat-message user-message"><strong>You ({message["timestamp"]}):</strong><br>{message["user"]}</div>', unsafe_allow_html=True)
                if "bot" in message:
                    st.markdown(f'<div class="chat-message bot-message"><strong>AI Assistant ({message["timestamp"]}):</strong><br>{message["bot"]}</div>', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.text_input("Ask me anything about jobs, skills, or career advice...", key="chat_input")
        
        if st.button("Send") and user_input:
            # Add user message
            st.session_state.chat_history.append({
                "user": user_input,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Get bot response
            try:
                context = {"resume_text": "sample resume text"} if st.session_state.resume_uploaded else {}
                result = run_async(mcp_client.chat_query(
                    st.session_state.user_data['user_id'],
                    "job_seeker",
                    user_input,
                    context
                ))
                
                if result["success"]:
                    bot_response = result["data"]["response"]
                    st.session_state.chat_history.append({
                        "bot": bot_response,
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                else:
                    st.session_state.chat_history.append({
                        "bot": f"Sorry, I encountered an error: {result['error']}",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
            except Exception as e:
                st.session_state.chat_history.append({
                    "bot": f"Sorry, I'm having technical difficulties: {str(e)}",
                    "timestamp": datetime.now().strftime("%H:%M")
                })
            
            st.rerun()
    
    with col2:
        st.subheader("📊 Insights")
        
        # Get job insights
        try:
            job_insights = run_async(mcp_client.get_job_insights())
            if job_insights["success"]:
                data = job_insights["data"]
                
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Jobs", data.get("total_jobs", 0))
                st.markdown('</div>', unsafe_allow_html=True)
                
                if data.get("popular_skills"):
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.subheader("🔥 Hot Skills")
                    for skill in data["popular_skills"][:5]:
                        st.write(f"• {skill}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if data.get("top_companies"):
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.subheader("🏢 Top Companies")
                    for company in data["top_companies"][:3]:
                        st.write(f"• {company}")
                    st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.info("Connect to servers to see insights")

def employer_dashboard():
    """Dashboard for employers"""
    st.markdown('<div class="main-header"><h1>🏢 Employer Dashboard</h1></div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("👤 Profile")
        st.write(f"**Email:** {st.session_state.user_data['email']}")
        st.write(f"**User ID:** {st.session_state.user_data['user_id']}")
        
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.user_data = None
            st.session_state.chat_history = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Job Posting
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("📝 Post New Job")
        
        with st.form("job_form"):
            job_title = st.text_input("Job Title")
            company = st.text_input("Company Name")
            location = st.text_input("Location")
            job_type = st.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Remote"])
            salary_range = st.text_input("Salary Range (optional)")
            description = st.text_area("Job Description")
            requirements = st.text_area("Requirements (one per line)")
            
            if st.form_submit_button("Post Job"):
                if job_title and company and description:
                    job_data = {
                        "employer_id": st.session_state.user_data['user_id'],
                        "title": job_title,
                        "company": company,
                        "location": location,
                        "job_type": job_type,
                        "salary_range": salary_range if salary_range else None,
                        "description": description,
                        "requirements": [req.strip() for req in requirements.split('\n') if req.strip()]
                    }
                    
                    try:
                        result = run_async(mcp_client.post_job(job_data))
                        if result["success"]:
                            st.success("Job posted successfully!")
                        else:
                            st.error(f"Failed to post job: {result['error']}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                else:
                    st.error("Please fill in required fields")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick Actions
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Actions")
        if st.button("Find Candidates"):
            st.session_state.chat_history.append({
                "user": "Show me the best candidates for my latest job posting",
                "timestamp": datetime.now().strftime("%H:%M")
            })
        
        if st.button("Talent Insights"):
            st.session_state.chat_history.append({
                "user": "What skills are most common in the talent pool?",
                "timestamp": datetime.now().strftime("%H:%M")
            })
        
        if st.button("My Job Posts"):
            st.session_state.chat_history.append({
                "user": "Show me all my job postings and their performance",
                "timestamp": datetime.now().strftime("%H:%M")
            })
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main chat interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💬 Chat with AI Assistant")
        
        # Chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                if "user" in message:
                    st.markdown(f'<div class="chat-message user-message"><strong>You ({message["timestamp"]}):</strong><br>{message["user"]}</div>', unsafe_allow_html=True)
                if "bot" in message:
                    st.markdown(f'<div class="chat-message bot-message"><strong>AI Assistant ({message["timestamp"]}):</strong><br>{message["bot"]}</div>', unsafe_allow_html=True)
        
        # Chat input
        user_input = st.text_input("Ask me about candidates, talent insights, or hiring strategies...", key="chat_input")
        
        if st.button("Send") and user_input:
            # Add user message
            st.session_state.chat_history.append({
                "user": user_input,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            # Get bot response
            try:
                context = {"job_description": "software developer position"}
                result = run_async(mcp_client.chat_query(
                    st.session_state.user_data['user_id'],
                    "employer",
                    user_input,
                    context
                ))
                
                if result["success"]:
                    bot_response = result["data"]["response"]
                    st.session_state.chat_history.append({
                        "bot": bot_response,
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                else:
                    st.session_state.chat_history.append({
                        "bot": f"Sorry, I encountered an error: {result['error']}",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
            except Exception as e:
                st.session_state.chat_history.append({
                    "bot": f"Sorry, I'm having technical difficulties: {str(e)}",
                    "timestamp": datetime.now().strftime("%H:%M")
                })
            
            st.rerun()
    
    with col2:
        st.subheader("📊 Talent Analytics")
        
        # Get resume insights
        try:
            resume_insights = run_async(mcp_client.get_resume_insights())
            if resume_insights["success"]:
                data = resume_insights["data"]
                
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Candidates", data.get("total_resumes", 0))
                st.markdown('</div>', unsafe_allow_html=True)
                
                if data.get("top_skills"):
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.subheader("💼 Top Skills")
                    for skill in data["top_skills"][:5]:
                        st.write(f"• {skill}")
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if data.get("experience_levels"):
                    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                    st.subheader("📈 Experience Levels")
                    for level, count in data["experience_levels"].items():
                        st.write(f"• {level}: {count}")
                    st.markdown('</div>', unsafe_allow_html=True)
        except:
            st.info("Connect to servers to see analytics")

def main():
    """Main application"""
    if not st.session_state.authenticated:
        login_page()
    else:
        user_type = st.session_state.user_data['user_type']
        if user_type == "job_seeker":
            job_seeker_dashboard()
        elif user_type == "employer":
            employer_dashboard()

if __name__ == "__main__":
    main()