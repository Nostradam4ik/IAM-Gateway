#!/bin/bash
#
# Import MidPoint Configuration (Resources and Roles)
#
# This script imports the XML configuration files into MidPoint
# using the REST API.
#
# Usage: ./import-midpoint-config.sh
#

set -e

# Configuration
MIDPOINT_URL="${MIDPOINT_URL:-http://localhost:8080/midpoint}"
MIDPOINT_USER="${MIDPOINT_USER:-administrator}"
MIDPOINT_PASSWORD="${MIDPOINT_PASSWORD:-Holimolly1}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Base directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
RESOURCES_DIR="$PROJECT_DIR/infrastructure/midpoint/resources"
ROLES_DIR="$PROJECT_DIR/infrastructure/midpoint/roles"

echo "=============================================="
echo "  MidPoint Configuration Import"
echo "=============================================="
echo ""
echo "MidPoint URL: $MIDPOINT_URL"
echo "User: $MIDPOINT_USER"
echo ""

# Test connection
echo -n "Testing MidPoint connection... "
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -u "$MIDPOINT_USER:$MIDPOINT_PASSWORD" \
    "$MIDPOINT_URL/ws/rest/self")

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}FAILED${NC} (HTTP $HTTP_CODE)"
    echo "Please check MidPoint is running and credentials are correct."
    exit 1
fi
echo -e "${GREEN}OK${NC}"
echo ""

# Function to import XML file
import_xml() {
    local file="$1"
    local type="$2"
    local endpoint="$3"

    if [ ! -f "$file" ]; then
        echo -e "  ${YELLOW}SKIP${NC} - File not found: $file"
        return
    fi

    filename=$(basename "$file")
    echo -n "  Importing $filename... "

    # POST the XML to MidPoint
    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -u "$MIDPOINT_USER:$MIDPOINT_PASSWORD" \
        -H "Content-Type: application/xml" \
        -X POST \
        -d @"$file" \
        "$MIDPOINT_URL/ws/rest/$endpoint")

    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "204" ]; then
        echo -e "${GREEN}OK${NC}"
        return 0
    elif [ "$HTTP_CODE" = "409" ]; then
        echo -e "${YELLOW}EXISTS${NC} (already imported)"
        return 0
    else
        echo -e "${RED}FAILED${NC} (HTTP $HTTP_CODE)"
        echo "    Response: $BODY"
        return 1
    fi
}

# Import Resources
echo "Importing Resources..."
echo "-------------------------------------------"
import_xml "$RESOURCES_DIR/openldap-resource.xml" "resource" "resources"
import_xml "$RESOURCES_DIR/odoo-resource.xml" "resource" "resources"
echo ""

# Import Roles
echo "Importing Roles..."
echo "-------------------------------------------"
import_xml "$ROLES_DIR/role-ldap-user.xml" "role" "roles"
import_xml "$ROLES_DIR/role-odoo-user.xml" "role" "roles"
import_xml "$ROLES_DIR/role-employee.xml" "role" "roles"
echo ""

# Test Resources
echo "Testing Resource Connections..."
echo "-------------------------------------------"

echo -n "  Testing OpenLDAP... "
LDAP_TEST=$(curl -s -u "$MIDPOINT_USER:$MIDPOINT_PASSWORD" \
    "$MIDPOINT_URL/ws/rest/resources/00000000-0000-0000-0000-000000000001/test" 2>/dev/null)
if echo "$LDAP_TEST" | grep -q "success"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}CHECK MANUALLY${NC}"
fi

echo -n "  Testing Odoo... "
ODOO_TEST=$(curl -s -u "$MIDPOINT_USER:$MIDPOINT_PASSWORD" \
    "$MIDPOINT_URL/ws/rest/resources/00000000-0000-0000-0000-000000000002/test" 2>/dev/null)
if echo "$ODOO_TEST" | grep -q "success"; then
    echo -e "${GREEN}OK${NC}"
else
    echo -e "${YELLOW}CHECK MANUALLY${NC}"
fi

echo ""
echo "=============================================="
echo -e "  ${GREEN}Import Complete!${NC}"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Open MidPoint: $MIDPOINT_URL"
echo "  2. Go to Resources and test connections"
echo "  3. Go to Roles to verify they were imported"
echo "  4. Create a test user and assign the 'employee' role"
echo ""
