"""
Script to start all MCP servers
"""
import subprocess
import time
import sys
import os

def start_server(script_path, port, name):
    """Start a server in a separate process"""
    print(f"Starting {name} on port {port}...")
    try:
        process = subprocess.Popen([
            sys.executable, script_path
        ], cwd=os.path.dirname(os.path.abspath(__file__)) + "/..")
        print(f"✅ {name} started successfully (PID: {process.pid})")
        return process
    except Exception as e:
        print(f"❌ Failed to start {name}: {e}")
        return None

def main():
    """Start all MCP servers"""
    print("🚀 Starting MCP Job Matcher Servers...")
    print("=" * 50)
    
    servers = [
        ("backend/servers/resume_server.py", 8001, "Resume MCP Server"),
        ("backend/servers/job_server.py", 8002, "Job MCP Server"),
        ("backend/servers/aggregator_server.py", 8003, "Aggregator MCP Server")
    ]
    
    processes = []
    
    for script_path, port, name in servers:
        process = start_server(script_path, port, name)
        if process:
            processes.append((process, name))
        time.sleep(2)  # Wait between server starts
    
    print("\n" + "=" * 50)
    print("🎉 All servers started!")
    print("\nServer URLs:")
    print("• Resume Server: http://localhost:8001")
    print("• Job Server: http://localhost:8002")
    print("• Aggregator Server: http://localhost:8003")
    print("\nTo start the frontend, run:")
    print("streamlit run frontend/app.py")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping all servers...")
        for process, name in processes:
            try:
                process.terminate()
                print(f"✅ Stopped {name}")
            except:
                print(f"❌ Failed to stop {name}")
        print("👋 All servers stopped!")

if __name__ == "__main__":
    main()