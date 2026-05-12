#!/bin/bash

############################################################################
#
#    Agno Railway Redeploy
#
#    Usage: ./scripts/railway_redeploy.sh
#
#    Redeploys the demo-os app service to an existing Railway project.
#    Run ./scripts/railway_up.sh first for initial provisioning.
#
############################################################################

set -e

# Colors
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

# Preflight
if ! command -v railway &> /dev/null; then
    echo "Railway CLI not found. Install: https://docs.railway.app/guides/cli"
    exit 1
fi

if ! railway status &> /dev/null; then
    echo "Not linked to a Railway project. Run ./scripts/railway_up.sh first."
    exit 1
fi

echo ""
echo -e "${BOLD}Redeploying demo-os...${NC}"
echo ""
railway up --service demo-os -d

echo ""
echo -e "${BOLD}Seeding Dash data...${NC}"
echo ""
railway run --service demo-os python -m agents.dash.scripts.load_data --drop
railway run --service demo-os python -m agents.dash.scripts.load_knowledge --recreate

echo ""
echo -e "${BOLD}Done.${NC}"
echo -e "${DIM}Logs: railway logs --service demo-os${NC}"
echo ""
