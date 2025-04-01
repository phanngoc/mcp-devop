#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper function to print colored messages
print_header() {
    echo -e "\n${YELLOW}=====================================================${NC}"
    echo -e "${YELLOW}  $1${NC}"
    echo -e "${YELLOW}=====================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is installed
print_header "Checking requirements"
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi
print_success "Python 3 is installed"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    print_header "Creating virtual environment"
    python3 -m venv .venv
    print_success "Virtual environment created"
fi

# Activate virtual environment
print_header "Activating virtual environment"
source .venv/bin/activate
print_success "Virtual environment activated"

# Install dependencies
print_header "Installing dependencies"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    print_error "Failed to install dependencies"
    exit 1
fi
print_success "Dependencies installed"

# Make scripts executable
print_header "Making scripts executable"
chmod +x run.py
chmod +x cursor_mcp_setup.py
chmod +x env_manager.py
print_success "Scripts are now executable"

# Configure environment
print_header "Environment Configuration"
echo "Would you like to configure environment variables now? (y/n)"
read -r configure_env

if [[ $configure_env == "y" || $configure_env == "Y" ]]; then
    # Run the interactive environment manager
    ./env_manager.py
else
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_header "Creating .env file"
        cp .env.example .env
        print_success ".env file created from .env.example. Please edit it with your AWS credentials."
    else
        print_success ".env file already exists"
    fi
    
    # Configure MCP for Cursor
    print_header "Configuring MCP for Cursor editor"
    echo "Would you like to configure MCP for Cursor editor? (y/n)"
    read -r configure_cursor

    if [[ $configure_cursor == "y" || $configure_cursor == "Y" ]]; then
        echo "Would you like to configure the basic or advanced server? (basic/advanced)"
        read -r server_type
        
        if [[ $server_type == "advanced" ]]; then
            ./run.py --cursor-setup --advanced --env-file .env
        else
            ./run.py --cursor-setup --env-file .env
        fi
    fi
fi

# Final message
print_header "Setup complete!"
echo -e "You can now run the following commands:\n"
echo "- Start basic server:    ./run.py --server"
echo "- Start advanced server: ./run.py --server --advanced"
echo "- Start UI:              ./run.py --ui"
echo "- Start both:            ./run.py --all"
echo "- Install in Claude:     ./run.py --install"
echo "- Manage environment:    ./env_manager.py"
echo -e "\nTo use the server in Cursor editor, open the Command Palette (Ctrl+Shift+P)"
echo "and select 'Claude: Connect to MCP Server'"
echo -e "\nEnjoy! 🚀" 