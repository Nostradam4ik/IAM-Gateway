#!/usr/bin/env python3
"""
=============================================================================
VIDÉO : Synchronisation Odoo → MidPoint
=============================================================================

Version 2 : Génère un fichier XML à importer manuellement dans MidPoint

Usage:
    python3 sync_odoo_to_midpoint_demo_v2.py
"""

import os
import sys
import xmlrpc.client
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================

ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

OUTPUT_FILE = '/tmp/midpoint_users_import.xml'


def print_banner():
    print()
    print("=" * 70)
    print("   SYNCHRONISATION ODOO → MIDPOINT")
    print("   Export des employés vers fichier XML")
    print("=" * 70)
    print(f"   Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Odoo : {ODOO_URL}")
    print("=" * 70)
    print()


def step_1_connect_odoo():
    """Étape 1 : Connexion à Odoo"""
    print("─" * 70)
    print("ÉTAPE 1 : Connexion à Odoo via XML-RPC")
    print("─" * 70)
    print()
    print(f"   URL : {ODOO_URL}")
    print(f"   Base de données : {ODOO_DB}")
    print(f"   Utilisateur : {ODOO_USER}")
    print()

    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

        if not uid:
            print("   ❌ Échec de l'authentification Odoo")
            return None, None

        print(f"   ✅ Connecté à Odoo (UID: {uid})")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        return uid, models

    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return None, None


def step_2_get_employees(uid, models):
    """Étape 2 : Récupération des employés depuis Odoo"""
    print()
    print("─" * 70)
    print("ÉTAPE 2 : Récupération des employés depuis Odoo")
    print("─" * 70)
    print()

    try:
        employees = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.employee', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'work_email', 'work_phone', 'department_id', 'job_id']}
        )

        print(f"   ✅ {len(employees)} employé(s) trouvé(s) dans Odoo")
        print()

        for emp in employees[:5]:  # Afficher les 5 premiers
            name = emp.get('name', 'N/A')
            email = emp.get('work_email', 'N/A') or 'N/A'
            print(f"   • {name} ({email})")

        if len(employees) > 5:
            print(f"   ... et {len(employees) - 5} autres")

        return employees

    except Exception as e:
        print(f"   ❌ Erreur : {e}")
        return []


def step_3_generate_xml(employees):
    """Étape 3 : Génération du fichier XML"""
    print()
    print("─" * 70)
    print("ÉTAPE 3 : Génération du fichier XML pour MidPoint")
    print("─" * 70)
    print()

    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<objects xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3">\n\n'

    count = 0
    for emp in employees:
        name = emp.get('name', '')
        email = emp.get('work_email', '')
        phone = emp.get('work_phone', '') or ''

        if not name or not email:
            continue

        # Générer le login
        name_parts = name.lower().split()
        if len(name_parts) >= 2:
            login = f"{name_parts[0]}.{name_parts[-1]}"
            given_name = name_parts[0].capitalize()
            family_name = ' '.join(name_parts[1:]).title()
        else:
            login = name.lower().replace(' ', '.')
            given_name = name
            family_name = ''

        # Nettoyer le login
        login = ''.join(c for c in login if c.isalnum() or c == '.')

        # Échapper les caractères XML
        def escape_xml(s):
            return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

        xml_content += f'''    <user>
        <name>{escape_xml(login)}</name>
        <fullName>{escape_xml(name)}</fullName>
        <givenName>{escape_xml(given_name)}</givenName>
        <familyName>{escape_xml(family_name)}</familyName>
        <emailAddress>{escape_xml(email)}</emailAddress>
        <telephoneNumber>{escape_xml(phone)}</telephoneNumber>
        <activation>
            <administrativeStatus>enabled</administrativeStatus>
        </activation>
        <credentials>
            <password>
                <value>
                    <clearValue>Welcome123!</clearValue>
                </value>
            </password>
        </credentials>
    </user>

'''
        count += 1
        print(f"   ✅ {name} → {login}")

    xml_content += '</objects>\n'

    # Écrire le fichier
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(xml_content)

    print()
    print(f"   ✅ {count} utilisateur(s) exporté(s)")
    print(f"   ✅ Fichier créé : {OUTPUT_FILE}")

    return count


def step_4_instructions():
    """Étape 4 : Instructions d'import"""
    print()
    print("─" * 70)
    print("ÉTAPE 4 : Import dans MidPoint")
    print("─" * 70)
    print()
    print("   Pour importer les utilisateurs dans MidPoint :")
    print()
    print("   1. Ouvrir MidPoint : http://localhost:8080/midpoint")
    print("   2. Se connecter : administrator / 5ecr3t")
    print("   3. Menu → Import object")
    print("   4. Choisir le fichier : /tmp/midpoint_users_import.xml")
    print("   5. Cliquer sur 'Import'")
    print()
    print("   Ou via le menu :")
    print("   Configuration → Import object → Choose file → Import")
    print()


def main():
    print_banner()

    # Étape 1
    uid, models = step_1_connect_odoo()
    if not uid:
        sys.exit(1)

    input("\n   Appuyez sur Entrée pour continuer...")

    # Étape 2
    employees = step_2_get_employees(uid, models)
    if not employees:
        print("\n   ⚠️  Aucun employé trouvé")
        sys.exit(0)

    input("\n   Appuyez sur Entrée pour continuer...")

    # Étape 3
    step_3_generate_xml(employees)

    input("\n   Appuyez sur Entrée pour continuer...")

    # Étape 4
    step_4_instructions()

    print("=" * 70)
    print("   EXPORT TERMINÉ")
    print("=" * 70)
    print()


if __name__ == '__main__':
    main()
