#!/bin/bash

############################################################################
#
#    Agno Railway Setup (first-time provisioning)
#
#    Usage: ./scripts/railway_up.sh
#    Redeploy: ./scripts/railway_redeploy.sh
#
#    Prerequisites:
#      - Railway CLI installed
#      - Logged in via `railway login`
#      - OPENAI_API_KEY set in environment
#
############################################################################

set -e

# Colors
ORANGE='\033[38;5;208m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

echo ""
echo -e "${ORANGE}"
cat << 'BANNER'
     █████╗  ██████╗ ███╗   ██╗ ██████╗
    ██╔══██╗██╔════╝ ████╗  ██║██╔═══██╗
    ███████║██║  ███╗██╔██╗ ██║██║   ██║
    ██╔══██║██║   ██║██║╚██╗██║██║   ██║
    ██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝
    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝
BANNER
echo -e "${NC}"

# Load .env.production if it exists
if [[ -f .env.production ]]; then
    set -a
    source .env.production
    set +a
    echo -e "${DIM}Loaded .env.production${NC}"
fi

# Preflight
if ! command -v railway &> /dev/null; then
    echo "Railway CLI not found. Install: https://docs.railway.app/guides/cli"
    exit 1
fi

if [[ -z "$OPENAI_API_KEY" ]]; then
    echo "OPENAI_API_KEY not set. Add to .env.production or export it."
    exit 1
fi

echo -e "${BOLD}Initializing project...${NC}"
echo ""
railway init -n "demo-os"

echo ""
echo -e "${BOLD}Deploying PgVector database...${NC}"
echo ""
railway add -s pgvector -i agnohq/pgvector:18 \
    -v "POSTGRES_USER=${DB_USER:-ai}" \
    -v "POSTGRES_PASSWORD=${DB_PASS:-ai}" \
    -v "POSTGRES_DB=${DB_DATABASE:-ai}" \
    -v "PGDATA=/var/lib/postgresql/data"

echo ""
echo ""
echo -e "${BOLD}Adding database volume...${NC}"
railway service link pgvector
railway volume add -m /var/lib/postgresql/data 2>/dev/null || echo -e "${DIM}Volume already exists or skipped${NC}"

echo ""
echo -e "${DIM}Waiting 15s for database...${NC}"
sleep 15

echo ""
echo -e "${BOLD}Creating application service...${NC}"
echo ""
OPTIONAL_VARS=()
[[ -n "$ANTHROPIC_API_KEY" ]]     && OPTIONAL_VARS+=(-v "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}")
[[ -n "$GOOGLE_API_KEY" ]]        && OPTIONAL_VARS+=(-v "GOOGLE_API_KEY=${GOOGLE_API_KEY}")
[[ -n "$EXA_API_KEY" ]]           && OPTIONAL_VARS+=(-v "EXA_API_KEY=${EXA_API_KEY}")
[[ -n "$PARALLEL_API_KEY" ]]      && OPTIONAL_VARS+=(-v "PARALLEL_API_KEY=${PARALLEL_API_KEY}")
[[ -n "$GITHUB_TOKEN" ]]          && OPTIONAL_VARS+=(-v "GITHUB_TOKEN=${GITHUB_TOKEN}")
[[ -n "$ELEVENLABS_API_KEY" ]]    && OPTIONAL_VARS+=(-v "ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}")
[[ -n "$FAL_KEY" ]]               && OPTIONAL_VARS+=(-v "FAL_KEY=${FAL_KEY}")
[[ -n "$GOOGLE_CLIENT_ID" ]]      && OPTIONAL_VARS+=(-v "GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}")
[[ -n "$GOOGLE_CLIENT_SECRET" ]]  && OPTIONAL_VARS+=(-v "GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}")
[[ -n "$GOOGLE_PROJECT_ID" ]]     && OPTIONAL_VARS+=(-v "GOOGLE_PROJECT_ID=${GOOGLE_PROJECT_ID}")
[[ -n "$GITHUB_ACCESS_TOKEN" ]]   && OPTIONAL_VARS+=(-v "GITHUB_ACCESS_TOKEN=${GITHUB_ACCESS_TOKEN}")
[[ -n "$PAL_REPO_URL" ]]          && OPTIONAL_VARS+=(-v "PAL_REPO_URL=${PAL_REPO_URL}")
[[ -n "$SLACK_TOKEN" ]]           && OPTIONAL_VARS+=(-v "SLACK_TOKEN=${SLACK_TOKEN}")
[[ -n "$SLACK_SIGNING_SECRET" ]]  && OPTIONAL_VARS+=(-v "SLACK_SIGNING_SECRET=${SLACK_SIGNING_SECRET}")
[[ -n "$AGENTOS_URL" ]]           && OPTIONAL_VARS+=(-v "AGENTOS_URL=${AGENTOS_URL}")
[[ -n "$JWT_VERIFICATION_KEY" ]]  && OPTIONAL_VARS+=(-v "JWT_VERIFICATION_KEY=${JWT_VERIFICATION_KEY}")

railway add -s demo-os \
    -v "DB_USER=${DB_USER:-ai}" \
    -v "DB_PASS=${DB_PASS:-ai}" \
    -v "DB_HOST=pgvector.railway.internal" \
    -v "DB_PORT=${DB_PORT:-5432}" \
    -v "DB_DATABASE=${DB_DATABASE:-ai}" \
    -v "DB_DRIVER=postgresql+psycopg" \
    -v "RUNTIME_ENV=prd" \
    -v "WAIT_FOR_DB=True" \
    -v "REPOS_DIR=/repos" \
    -v "OPENAI_API_KEY=${OPENAI_API_KEY}" \
    -v "PORT=8000" \
    "${OPTIONAL_VARS[@]}"

echo ""
echo -e "${BOLD}Deploying application...${NC}"
echo ""
railway up --service demo-os -d

echo ""
echo -e "${BOLD}Creating domain...${NC}"
echo ""
railway domain --service demo-os

echo ""
echo -e "${BOLD}Seeding Dash data...${NC}"
echo ""
railway run --service demo-os python -m agents.dash.scripts.load_data --drop
railway run --service demo-os python -m agents.dash.scripts.load_knowledge --recreate

echo ""
echo -e "${BOLD}Done.${NC} Domain may take ~5 minutes."
echo -e "${DIM}Logs: railway logs --service demo-os${NC}"
echo ""
