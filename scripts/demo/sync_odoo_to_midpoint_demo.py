#!/usr/bin/env python3
"""
SYNCHRONISATION ODOO → MIDPOINT (Simple)
"""

import xmlrpc.client
from datetime import datetime

# Configuration
ODOO_URL = 'http://localhost:8069'
ODOO_DB = 'odoo'
ODOO_USER = 'admin'
ODOO_PASSWORD = 'admin'

print()
print("=" * 60)
print("  SYNCHRONISATION ODOO → MIDPOINT")
print("=" * 60)
print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60)

# Étape 1 : Connexion Odoo
print("\n[1/3] Connexion à Odoo...")
common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
print(f"  ✅ Connecté (UID: {uid})")

# Étape 2 : Récupération employés
print("\n[2/3] Récupération des employés...")
models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
employees = models.execute_kw(
    ODOO_DB, uid, ODOO_PASSWORD,
    'hr.employee', 'search_read', [[]],
    {'fields': ['name', 'work_email', 'department_id']}
)
print(f"  ✅ {len(employees)} employés trouvés")

# Étape 3 : Génération XML
print("\n[3/3] Génération du fichier XML...")

xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
xml += '<objects xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3">\n'

for emp in employees:
    name = emp.get('name', '')
    email = emp.get('work_email', '') or ''
    if not name:
        continue

    parts = name.lower().split()
    login = f"{parts[0]}.{parts[-1]}" if len(parts) >= 2 else name.lower().replace(' ', '.')
    login = ''.join(c for c in login if c.isalnum() or c == '.')

    xml += f'''  <user>
    <name>{login}</name>
    <fullName>{name}</fullName>
    <givenName>{parts[0].capitalize() if parts else name}</givenName>
    <familyName>{' '.join(parts[1:]).title() if len(parts) > 1 else ''}</familyName>
    <emailAddress>{email}</emailAddress>
    <activation><administrativeStatus>enabled</administrativeStatus></activation>
  </user>
'''
    print(f"  • {name} → {login}")

xml += '</objects>\n'

# Sauvegarder
output_file = '/tmp/midpoint_users_import.xml'
with open(output_file, 'w') as f:
    f.write(xml)

print(f"\n  ✅ Fichier créé: {output_file}")

print("\n" + "=" * 60)
print("  TERMINÉ - Importez maintenant dans MidPoint:")
print("  1. Menu → Import object")
print("  2. Choisir: /tmp/midpoint_users_import.xml")
print("  3. Cliquer Import")
print("=" * 60 + "\n")
