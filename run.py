#!/usr/bin/env python3
import os
import argparse
import subprocess
import sys
import time
import json
import re
from pathlib import Path
from dotenv import load_dotenv, dotenv_values

# Load environment variables from .env file if present
load_dotenv()

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60 + "\n")

def load_env_file(env_file_path):
    """Load environment variables from a file with better handling"""
    env_vars = {}
    
    if not env_file_path or not os.path.exists(env_file_path):
        print(f"WARNING: Environment file {env_file_path} not found")
        return env_vars
    
    # First try to use dotenv_values
    try:
        env_vars = dotenv_values(env_file_path)
        if env_vars:
            return env_vars
    except Exception:
        pass  # Fall back to manual parsing
    
    # Manual parsing as fallback
    try:
        with open(env_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle various formats: KEY=VALUE, KEY="VALUE", KEY='VALUE'
                match = re.match(r'^([A-Za-z0-9_]+)=["\']?([^"\']*)["\']?$', line)
                if match:
                    key, value = match.groups()
                    env_vars[key] = value
                elif '=' in line:
                    # Simple KEY=VALUE format
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"WARNING: Error reading environment file: {str(e)}")
    
    return env_vars

def run_server(advanced=False):
    """Run the MCP server"""
    server_type = "Advanced" if advanced else "Basic"
    script_name = "advanced_server.py" if advanced else "server.py"
    
    print_header(f"Starting {server_type} MCP Server")
    print(f"Running {script_name}...")
    
    try:
        # Import the module and run it directly
        import server
        server.mcp.run()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error running server: {str(e)}")
        sys.exit(1)

def run_ui(advanced=False):
    """Run the Streamlit UI"""
    ui_type = "Advanced" if advanced else "Basic"
    script_name = "advanced_app.py" if advanced else "app.py"
    
    print_header(f"Starting {ui_type} Streamlit UI")
    print(f"Running {script_name}...")
    
    try:
        args = ["streamlit", "run", script_name]
        subprocess.run(args)
    except KeyboardInterrupt:
        print("\nUI stopped by user")
    except Exception as e:
        print(f"Error running UI: {str(e)}")
        sys.exit(1)

def install_mcp_server(advanced=False):
    """Install MCP server in Claude Desktop"""
    server_type = "Advanced" if advanced else "Basic"
    script_name = "advanced_server.py" if advanced else "server.py"
    
    print_header(f"Installing {server_type} MCP Server in Claude Desktop")
    
    try:
        result = subprocess.run(
            ["mcp", "install", script_name], 
            capture_output=True, 
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
            sys.exit(1)
        
        print(f"{server_type} MCP Server installed successfully!")
    except Exception as e:
        print(f"Error installing MCP server: {str(e)}")
        sys.exit(1)

def setup_cursor_mcp(advanced=False, env_file=None):
    """Set up MCP server configuration in Cursor editor"""
    # Find the cursor directory
    cursor_dir = Path.home() / ".cursor"
    if not cursor_dir.exists():
        print(f"ERROR: Cursor directory not found at {cursor_dir}")
        return False
    
    # Path to mcp.json file
    mcp_json_path = cursor_dir / "mcp.json"
    
    # Create default mcp.json if it doesn't exist
    if not mcp_json_path.exists():
        default_config = {
            "mcpServers": {}
        }
        with open(mcp_json_path, 'w') as f:
            json.dump(default_config, f, indent=2)
    
    # Read the current configuration
    try:
        with open(mcp_json_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in {mcp_json_path}")
        return False
    
    # Make sure mcpServers key exists
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Load environment variables from the specified file with enhanced handling
    env_vars = load_env_file(env_file) if env_file else {}
    
    # Get AWS credentials from environment if not already in env_vars
    if "AWS_ACCESS_KEY_ID" not in env_vars and os.environ.get("AWS_ACCESS_KEY_ID"):
        env_vars["AWS_ACCESS_KEY_ID"] = os.environ.get("AWS_ACCESS_KEY_ID")
    
    if "AWS_SECRET_ACCESS_KEY" not in env_vars and os.environ.get("AWS_SECRET_ACCESS_KEY"):
        env_vars["AWS_SECRET_ACCESS_KEY"] = os.environ.get("AWS_SECRET_ACCESS_KEY")
    
    if "AWS_DEFAULT_REGION" not in env_vars and os.environ.get("AWS_DEFAULT_REGION"):
        env_vars["AWS_DEFAULT_REGION"] = os.environ.get("AWS_DEFAULT_REGION")
    else:
        env_vars["AWS_DEFAULT_REGION"] = "us-east-1"  # Default region
    
    # Get current directory as workspace folder
    workspace_folder = os.path.abspath(os.getcwd())
    
    # Create server configuration
    server_type = "advanced" if advanced else "basic"
    server_key = f"aws-{server_type}-server"
    server_name = "Advanced AWS Integration Server" if advanced else "AWS Integration Server"
    script_name = "advanced_server.py" if advanced else "server.py"
    
    # Update configuration
    script_path = os.path.join(workspace_folder, script_name)
    config["mcpServers"][server_key] = {
        "name": server_name,
        "command": "python",
        "args": [script_path],
        "env": env_vars
    }
    
    # Write updated configuration back to file
    with open(mcp_json_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Successfully configured the {server_name} in Cursor editor.")
    print(f"Server key: {server_key}")
    print(f"Script path: {script_path}")
    print(f"Environment variables loaded: {', '.join(env_vars.keys())}")
    
    # Show AWS credentials status
    if "AWS_ACCESS_KEY_ID" in env_vars and "AWS_SECRET_ACCESS_KEY" in env_vars:
        print("✅ AWS credentials successfully loaded.")
    else:
        print("⚠️ AWS credentials not found. Make sure to add them to your .env file.")
    
    print("\nTo use this server in Cursor, go to the Command Palette (Ctrl+Shift+P) and select 'Claude: Connect to MCP Server'")
    
    return True

def main():
    parser = argparse.ArgumentParser(description="Run AWS MCP Server components")
    
    # Add server type argument
    parser.add_argument(
        "--advanced", 
        action="store_true", 
        help="Use advanced server with more AWS services"
    )
    
    # Add component selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--server", 
        action="store_true", 
        help="Run the MCP server"
    )
    group.add_argument(
        "--ui", 
        action="store_true", 
        help="Run the Streamlit UI"
    )
    group.add_argument(
        "--install", 
        action="store_true", 
        help="Install the MCP server in Claude Desktop"
    )
    group.add_argument(
        "--all", 
        action="store_true", 
        help="Run both server and UI"
    )
    group.add_argument(
        "--cursor-setup", 
        action="store_true", 
        help="Configure MCP server for Cursor editor"
    )
    
    # Optional argument for environment file
    parser.add_argument(
        "--env-file", 
        type=str,
        help="Path to .env file with environment variables (for cursor setup)"
    )
    
    args = parser.parse_args()
    
    if args.server:
        run_server(advanced=args.advanced)
    elif args.ui:
        run_ui(advanced=args.advanced)
    elif args.install:
        install_mcp_server(advanced=args.advanced)
    elif args.cursor_setup:
        setup_cursor_mcp(advanced=args.advanced, env_file=args.env_file)
    elif args.all:
        # Run server in a subprocess
        server_script = "advanced_server.py" if args.advanced else "server.py"
        print_header(f"Starting {'Advanced' if args.advanced else 'Basic'} Server and UI")
        
        try:
            server_process = subprocess.Popen([sys.executable, server_script])
            
            # Wait a moment for server to start
            print("Starting server... waiting 2 seconds")
            time.sleep(2)
            
            # Run UI
            ui_script = "advanced_app.py" if args.advanced else "app.py"
            subprocess.run(["streamlit", "run", ui_script])
            
            # Cleanup
            server_process.terminate()
            print("Server process terminated")
        except KeyboardInterrupt:
            print("\nStopped by user")
            if 'server_process' in locals():
                server_process.terminate()
                print("Server process terminated")
        except Exception as e:
            print(f"Error: {str(e)}")
            if 'server_process' in locals():
                server_process.terminate()

if __name__ == "__main__":
    main() 