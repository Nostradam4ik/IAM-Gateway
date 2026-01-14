#!/bin/bash
#
# Script de Démonstration Simplifié: Synchronisation Directe Sans Gateway
# Utilise uniquement Bash, Docker et XML-RPC
#

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

step() {
    echo -e "${BLUE}[ETAPE]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[ATTENTION]${NC} $1"
}

error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

header() {
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║  DEMONSTRATION: SYNCHRONISATION DIRECTE SANS GATEWAY IAM      ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
}

header

# 1. Vérifier les services
step "Vérification des services..."
echo ""

if docker exec odoo echo "OK" >/dev/null 2>&1; then
    success "Odoo est accessible"
else
    error "Odoo n'est pas accessible"
    exit 1
fi

if docker exec openldap echo "OK" >/dev/null 2>&1; then
    success "OpenLDAP est accessible"
else
    error "OpenLDAP n'est pas accessible"
    exit 1
fi

if docker exec intranet-db echo "OK" >/dev/null 2>&1; then
    success "PostgreSQL Intranet est accessible"
else
    warning "PostgreSQL Intranet n'est pas accessible. Démarrage..."
    docker start intranet-db
    sleep 5
fi

echo ""
step "Extraction des données Odoo..."
echo ""

# 2. Créer un script Python pour extraire les données d'Odoo
cat > /tmp/extract_odoo.py << 'PYTHON_SCRIPT'
import xmlrpc.client
import json

url = "http://localhost:8069"
db = "odoo"
username = "admin"
password = "admin"

try:
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print(json.dumps({"error": "Authentication failed"}))
        exit(1)

    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

    employees = models.execute_kw(db, uid, password,
        'hr.employee', 'search_read',
        [[]],
        {'fields': ['name', 'work_email', 'department_id', 'job_id', 'work_phone', 'mobile_phone']}
    )

    print(json.dumps(employees, indent=2))

except Exception as e:
    print(json.dumps({"error": str(e)}))
    exit(1)
PYTHON_SCRIPT

# Exécuter l'extraction
ODOO_DATA=$(python3 /tmp/extract_odoo.py 2>/dev/null)

if echo "$ODOO_DATA" | grep -q "error"; then
    error "Impossible de récupérer les données d'Odoo"
    echo "$ODOO_DATA"
    exit 1
fi

# Compter les employés
EMPLOYEE_COUNT=$(echo "$ODOO_DATA" | python3 -c "import json,sys; data=json.load(sys.stdin); print(len(data))" 2>/dev/null || echo "0")
success "Récupéré ${EMPLOYEE_COUNT} employés depuis Odoo"

echo ""
step "Génération du fichier LDIF..."
echo ""

# 3. Générer le fichier LDIF
cat > /tmp/generate_ldif.py << 'PYTHON_SCRIPT'
import json
import sys

employees = json.load(sys.stdin)
ldif_entries = []

for emp in employees:
    if emp.get('work_email'):
        username = emp['work_email'].split('@')[0]
        name_parts = emp['name'].split()
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]

        entry = []
        entry.append(f"dn: uid={username},ou=people,dc=example,dc=com")
        entry.append("objectClass: inetOrgPerson")
        entry.append("objectClass: organizationalPerson")
        entry.append("objectClass: person")
        entry.append("objectClass: top")
        entry.append(f"uid: {username}")
        entry.append(f"cn: {emp['name']}")
        entry.append(f"sn: {last_name}")
        entry.append(f"givenName: {first_name}")
        entry.append(f"mail: {emp['work_email']}")

        if emp.get('department_id'):
            dept = emp['department_id'][1]
            entry.append(f"ou: {dept}")

        if emp.get('work_phone'):
            entry.append(f"telephoneNumber: {emp['work_phone']}")

        if emp.get('job_id'):
            entry.append(f"title: {emp['job_id'][1]}")

        ldif_entries.append('\n'.join(entry))

print('\n\n'.join(ldif_entries))
PYTHON_SCRIPT

echo "$ODOO_DATA" | python3 /tmp/generate_ldif.py > /tmp/odoo_sync_to_ldap.ldif

LDIF_COUNT=$(grep -c "^dn:" /tmp/odoo_sync_to_ldap.ldif || echo "0")
success "Fichier LDIF créé: /tmp/odoo_sync_to_ldap.ldif"
success "${LDIF_COUNT} entrées LDIF générées"

echo ""
step "Synchronisation vers PostgreSQL..."
echo ""

# 4. Synchroniser vers PostgreSQL
cat > /tmp/sync_postgres.py << 'PYTHON_SCRIPT'
import json
import sys
import subprocess

employees = json.load(sys.stdin)
count_success = 0

for emp in employees:
    if emp.get('work_email'):
        username = emp['work_email'].split('@')[0]
        name_parts = emp['name'].split()
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
        department = emp['department_id'][1] if emp.get('department_id') else ''
        job_title = emp['job_id'][1] if emp.get('job_id') else ''
        phone = emp.get('work_phone') or emp.get('mobile_phone') or ''

        # Échapper les apostrophes pour SQL
        first_name = first_name.replace("'", "''")
        last_name = last_name.replace("'", "''")
        department = department.replace("'", "''")
        job_title = job_title.replace("'", "''")

        sql = f"""
INSERT INTO users (username, email, first_name, last_name, department, job_title, phone, is_active)
VALUES ('{username}', '{emp['work_email']}', '{first_name}', '{last_name}', '{department}', '{job_title}', '{phone}', true)
ON CONFLICT (username)
DO UPDATE SET
    email = EXCLUDED.email,
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    department = EXCLUDED.department,
    job_title = EXCLUDED.job_title,
    phone = EXCLUDED.phone,
    updated_at = CURRENT_TIMESTAMP;
"""

        result = subprocess.run([
            'docker', 'exec', 'intranet-db',
            'psql', '-U', 'intranet', '-d', 'intranet',
            '-c', sql
        ], capture_output=True, text=True)

        if result.returncode == 0:
            count_success += 1

print(f"{count_success}")
PYTHON_SCRIPT

POSTGRES_COUNT=$(echo "$ODOO_DATA" | python3 /tmp/sync_postgres.py 2>/dev/null || echo "0")
success "${POSTGRES_COUNT} utilisateurs synchronisés vers PostgreSQL"

echo ""
echo "════════════════════════════════════════════════════════════════"
step "VÉRIFICATIONS"
echo "════════════════════════════════════════════════════════════════"
echo ""

# 5. Vérifier LDAP
echo -n "📊 OpenLDAP: "
LDAP_COUNT=$(docker exec openldap ldapsearch -x -H ldap://localhost \
  -b "ou=people,dc=example,dc=com" \
  -D "cn=admin,dc=example,dc=com" -w secret \
  "(objectClass=inetOrgPerson)" 2>/dev/null | grep -c "^dn:" || echo "N/A")
echo "${LDAP_COUNT} entrées"

# 6. Vérifier PostgreSQL
echo -n "📊 PostgreSQL: "
PG_COUNT=$(docker exec intranet-db psql -U intranet -d intranet -t \
  -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' ' || echo "N/A")
echo "${PG_COUNT} utilisateurs"

echo ""
echo "════════════════════════════════════════════════════════════════"
step "RÉSULTATS"
echo "════════════════════════════════════════════════════════════════"
echo ""

printf "%-20s | %10s\n" "Système" "Utilisateurs"
echo "───────────────────────────────────────────"
printf "%-20s | %10s\n" "Odoo (Source)" "$EMPLOYEE_COUNT"
printf "%-20s | %10s\n" "LDIF Généré" "$LDIF_COUNT"
printf "%-20s | %10s\n" "PostgreSQL Sync" "$POSTGRES_COUNT"
printf "%-20s | %10s\n" "OpenLDAP Total" "$LDAP_COUNT"
printf "%-20s | %10s\n" "PostgreSQL Total" "$PG_COUNT"

echo ""
echo "════════════════════════════════════════════════════════════════"
step "PROCHAINES ÉTAPES"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. Pour importer le fichier LDIF dans OpenLDAP:"
echo "   docker exec -i openldap ldapadd -x -H ldap://localhost \\"
echo "     -D 'cn=admin,dc=example,dc=com' -w secret \\"
echo "     < /tmp/odoo_sync_to_ldap.ldif"
echo ""
echo "2. Vérifier dans phpLDAPadmin:"
echo "   → http://localhost:8088"
echo "   → Login: cn=admin,dc=example,dc=com / secret"
echo ""
echo "3. Vérifier dans PostgreSQL:"
echo "   docker exec intranet-db psql -U intranet -d intranet \\"
echo "     -c 'SELECT username, email, department FROM users LIMIT 10;'"
echo ""
echo "════════════════════════════════════════════════════════════════"
success "SYNCHRONISATION TERMINÉE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📝 Documentation: docs/guides/README_SYNCHRONISATION_DIRECTE.md"
echo ""

# Nettoyer
rm -f /tmp/extract_odoo.py /tmp/generate_ldif.py /tmp/sync_postgres.py
