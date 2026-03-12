#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}=== Sentiview Startup ===${NC}\n"

# Step 1: Activate virtual environment
echo -e "${BLUE}1. Activating virtual environment...${NC}"
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}\n"

# Step 2: Check/setup .env file
echo -e "${BLUE}2. Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}   .env file not found, creating from .env.example${NC}"
    cp .env.example .env
    echo -e "${GREEN}   ✓ .env created${NC}"
else
    echo -e "${GREEN}   ✓ .env file exists${NC}"
fi
echo

# Step 3: Check Docker and PostgreSQL
echo -e "${BLUE}3. Checking PostgreSQL...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}   Docker not found in PATH${NC}"
    echo -e "${YELLOW}   Please ensure Docker is running and try again${NC}"
    echo -e "${YELLOW}   Continue anyway? (y/n)${NC}"
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    # Try to start PostgreSQL container
    if docker ps | grep -q "sentiview-postgres"; then
        echo -e "${GREEN}   ✓ PostgreSQL container is running${NC}"
    else
        echo -e "${YELLOW}   PostgreSQL container not running, attempting to start...${NC}"
        if docker compose up -d 2>/dev/null; then
            echo -e "${GREEN}   ✓ PostgreSQL started${NC}"
            sleep 2
            
            # Check if schema exists
            if ! psql postgresql://postgres:postgres@localhost:5432/sentiview -c "\dt" &>/dev/null 2>&1; then
                echo -e "${YELLOW}   Creating database schema...${NC}"
                if psql postgresql://postgres:postgres@localhost:5432/sentiview -f backend/sql/schema.sql; then
                    echo -e "${GREEN}   ✓ Schema created${NC}"
                else
                    echo -e "${YELLOW}   Could not create schema (database may not be ready)${NC}"
                fi
            else
                echo -e "${GREEN}   ✓ Schema already exists${NC}"
            fi
        else
            echo -e "${YELLOW}   Could not start PostgreSQL container${NC}"
            echo -e "${YELLOW}   API will start but database operations may fail${NC}"
        fi
    fi
fi
echo

# Step 4: Start FastAPI server
echo -e "${BLUE}4. Starting FastAPI server...${NC}"
echo -e "${GREEN}✓ Server launching on http://localhost:8000${NC}\n"
echo -e "${BLUE}=== Sentiview Ready ===${NC}"
echo -e "${YELLOW}API Documentation:${NC}   http://localhost:8000/docs"
echo -e "${YELLOW}Alternative Docs:${NC}   http://localhost:8000/redoc"
echo -e "${YELLOW}Health Check:${NC}        http://localhost:8000/health\n"

# Open in browser (macOS)
if command -v open &> /dev/null; then
    sleep 1
    open "http://localhost:8000/docs"
fi

# Start the server
exec python -m uvicorn backend.app.main:app --reload --port 8000
