#!/bin/bash

############################################################################
#
#    Sync .env.production to Railway
#
#    Usage: ./scripts/railway_env.sh
#
#    Reads all variables from .env.production and sets them on the Railway service.
#    Handles multiline values (PEM keys, etc.) correctly.
#    Safe to run repeatedly — overwrites existing values.
#
############################################################################

set -e

BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'
SERVICE="demo-os"

if ! command -v railway &> /dev/null; then
    echo "Railway CLI not found. Install: https://docs.railway.app/guides/cli"
    exit 1
fi

ENV_FILE=".env.production"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "No $ENV_FILE file found. Copy example.env to $ENV_FILE and fill in your production values."
    exit 1
fi

echo -e "${BOLD}Syncing ${ENV_FILE} → Railway service '${SERVICE}'...${NC}"
echo ""

count=0
current_key=""
current_value=""

flush_var() {
    if [[ -n "$current_key" ]]; then
        railway variables --set "${current_key}=${current_value}" --service "$SERVICE" 2>/dev/null
        echo -e "  ${DIM}${current_key}${NC}"
        ((count++))
    fi
    current_key=""
    current_value=""
}

while IFS= read -r line || [[ -n "$line" ]]; do
    # Skip empty lines and comments
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue

    # Check if this is a new KEY=VALUE line
    if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*) ]]; then
        flush_var
        current_key="${BASH_REMATCH[1]}"
        current_value="${BASH_REMATCH[2]}"
        # Strip surrounding quotes
        current_value="${current_value%\"}"
        current_value="${current_value#\"}"
        current_value="${current_value%\'}"
        current_value="${current_value#\'}"
    else
        # Continuation of a multiline value
        if [[ -n "$current_key" ]]; then
            current_value="${current_value}
${line}"
        fi
    fi
done < "$ENV_FILE"

flush_var

echo ""
echo -e "${BOLD}Done.${NC} Synced ${count} variables to '${SERVICE}'."
echo -e "${DIM}Redeploy: ./scripts/railway_redeploy.sh${NC}"
echo ""
