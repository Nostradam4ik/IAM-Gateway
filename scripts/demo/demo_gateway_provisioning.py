#!/usr/bin/env python3
"""
===================================================================
    DÉMONSTRATION IAM GATEWAY - PROVISIONNEMENT MULTI-CONNECTEURS
===================================================================

Ce script démontre les capacités de l'IAM Gateway pour:
1. Lister les employés Odoo
2. Synchroniser vers MidPoint
3. Assigner des rôles
4. Vérifier le provisionnement vers LDAP, Odoo et PostgreSQL

Prérequis:
- Gateway IAM running on port 8000
- Frontend running on port 3000
- MidPoint running on port 8080

Credentials Gateway: admin / admin123
"""

import requests
import json
import time
from datetime import datetime

# Configuration
GATEWAY_URL = "http://localhost:8000"
MIDPOINT_URL = "http://localhost:8080"
GATEWAY_USER = "admin"
GATEWAY_PASS = "admin123"

# Couleurs pour l'affichage
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ {text}{Colors.END}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.END}")

def get_token():
    """Obtenir un token JWT depuis la Gateway"""
    print_info("Authentification à la Gateway IAM...")
    response = requests.post(
        f"{GATEWAY_URL}/api/v1/admin/token",
        data={"username": GATEWAY_USER, "password": GATEWAY_PASS}
    )
    if response.status_code == 200:
        token = response.json()["access_token"]
        print_success("Token obtenu avec succès")
        return token
    else:
        print_error(f"Erreur d'authentification: {response.status_code}")
        return None

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def demo_list_odoo_employees(token):
    """Démonstration: Lister les employés Odoo"""
    print_header("1. LISTE DES EMPLOYÉS ODOO")

    response = requests.get(
        f"{GATEWAY_URL}/api/v1/live/odoo/employees",
        headers=get_headers(token)
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Nombre d'employés Odoo: {data['count']}")
        print_info("\nExemples d'employés:")
        for emp in data['employees'][:5]:
            print(f"   - {emp['name']} ({emp.get('email', 'N/A')}) - {emp.get('department', 'N/A')}")
        return data['employees']
    else:
        print_error(f"Erreur: {response.status_code}")
        return []

def demo_list_midpoint_users(token):
    """Démonstration: Lister les utilisateurs MidPoint"""
    print_header("2. LISTE DES UTILISATEURS MIDPOINT")

    response = requests.get(
        f"{GATEWAY_URL}/api/v1/midpoint/users",
        headers=get_headers(token)
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Nombre d'utilisateurs MidPoint: {data.get('total', len(data.get('users', [])))}")
        users = data.get('users', [])
        print_info("\nExemples d'utilisateurs:")
        for user in users[:5]:
            print(f"   - {user.get('name', 'N/A')} ({user.get('emailAddress', 'N/A')})")
        return users
    else:
        print_error(f"Erreur: {response.status_code}")
        return []

def demo_list_roles(token):
    """Démonstration: Lister les rôles disponibles"""
    print_header("3. RÔLES DISPONIBLES DANS MIDPOINT")

    response = requests.get(
        f"{GATEWAY_URL}/api/v1/midpoint/roles",
        headers=get_headers(token)
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Nombre de rôles: {data.get('total', 0)}")

        # Catégoriser les rôles
        roles = data.get('roles', [])
        dept_roles = [r for r in roles if 'Department' in r.get('name', '')]
        odoo_roles = [r for r in roles if 'Odoo' in r.get('name', '') or 'odoo' in r.get('name', '')]
        app_roles = [r for r in roles if 'App' in r.get('name', '')]
        ldap_roles = [r for r in roles if 'LDAP' in r.get('name', '') or 'Employee' in r.get('name', '')]

        print_info("\nRôles par catégorie:")
        print(f"\n   {Colors.BOLD}Départements:{Colors.END}")
        for r in dept_roles:
            print(f"      - {r['name']}: {r.get('description', '')[:50]}")

        print(f"\n   {Colors.BOLD}Odoo:{Colors.END}")
        for r in odoo_roles:
            risk = " ⚠️ CRITIQUE" if "Admin" in r.get('name', '') else ""
            print(f"      - {r['name']}{risk}")

        print(f"\n   {Colors.BOLD}Application Métier:{Colors.END}")
        for r in app_roles:
            risk = " ⚠️ CRITIQUE" if "Admin" in r.get('name', '') else ""
            print(f"      - {r['name']}{risk}")

        return roles
    else:
        print_error(f"Erreur: {response.status_code}")
        return []

def demo_create_user_via_gateway(token, name, email, given_name, family_name):
    """Démonstration: Créer un utilisateur via la Gateway"""
    print_header(f"4. CRÉATION D'UTILISATEUR: {name}")

    # Vérifier si l'utilisateur existe déjà
    response = requests.get(
        f"{GATEWAY_URL}/api/v1/midpoint/users",
        headers=get_headers(token)
    )

    if response.status_code == 200:
        users = response.json().get('users', [])
        existing = [u for u in users if u.get('name') == name]
        if existing:
            print_warning(f"L'utilisateur {name} existe déjà")
            return existing[0].get('oid')

    # Créer via MidPoint REST API directement (la Gateway n'a pas d'endpoint de création)
    print_info(f"Création de l'utilisateur {name}...")

    user_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<user xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3">
    <name>{name}</name>
    <fullName>{given_name} {family_name}</fullName>
    <givenName>{given_name}</givenName>
    <familyName>{family_name}</familyName>
    <emailAddress>{email}</emailAddress>
    <activation>
        <administrativeStatus>enabled</administrativeStatus>
    </activation>
</user>"""

    response = requests.post(
        f"{MIDPOINT_URL}/midpoint/ws/rest/users",
        auth=('administrator', '5ecr3t'),
        headers={"Content-Type": "application/xml"},
        data=user_xml
    )

    if response.status_code == 201:
        print_success(f"Utilisateur {name} créé avec succès")
        # Récupérer l'OID
        time.sleep(1)
        response = requests.get(
            f"{GATEWAY_URL}/api/v1/midpoint/users",
            headers=get_headers(token)
        )
        if response.status_code == 200:
            users = response.json().get('users', [])
            user = next((u for u in users if u.get('name') == name), None)
            if user:
                return user.get('oid')
    else:
        print_error(f"Erreur création: {response.status_code}")
        print(response.text[:200])

    return None

def demo_assign_role(token, user_oid, role_oid, role_name):
    """Démonstration: Assigner un rôle à un utilisateur"""
    print_info(f"Assignation du rôle '{role_name}'...")

    # Utiliser MidPoint REST API
    modification = f"""<?xml version="1.0" encoding="UTF-8"?>
<objectModification xmlns="http://midpoint.evolveum.com/xml/ns/public/common/api-types-3"
                   xmlns:c="http://midpoint.evolveum.com/xml/ns/public/common/common-3">
    <itemDelta>
        <modificationType>add</modificationType>
        <path>c:assignment</path>
        <value>
            <c:targetRef oid="{role_oid}" type="c:RoleType"/>
        </value>
    </itemDelta>
</objectModification>"""

    response = requests.post(
        f"{MIDPOINT_URL}/midpoint/ws/rest/users/{user_oid}",
        auth=('administrator', '5ecr3t'),
        headers={"Content-Type": "application/xml"},
        data=modification
    )

    if response.status_code in [200, 204, 250]:
        print_success(f"Rôle '{role_name}' assigné avec succès")
        return True
    else:
        print_warning(f"Assignation du rôle: HTTP {response.status_code}")
        return False

def demo_check_provisioning(name):
    """Démonstration: Vérifier le provisionnement dans les systèmes cibles"""
    print_header(f"5. VÉRIFICATION DU PROVISIONNEMENT: {name}")

    import subprocess

    # Vérifier LDAP
    print_info("Vérification compte LDAP...")
    result = subprocess.run([
        "docker", "exec", "openldap", "ldapsearch", "-x",
        "-D", "cn=admin,dc=example,dc=com", "-w", "secret",
        "-b", "ou=users,dc=example,dc=com", f"(uid={name})", "dn", "mail"
    ], capture_output=True, text=True)

    if f"uid={name}" in result.stdout:
        print_success(f"Compte LDAP créé: uid={name},ou=users,dc=example,dc=com")
    else:
        print_warning("Compte LDAP non trouvé")

    # Vérifier Odoo
    print_info("Vérification compte Odoo (table iam_users)...")
    result = subprocess.run([
        "docker", "exec", "odoo-db", "psql", "-U", "odoo", "-d", "odoo",
        "-c", f"SELECT username, email, full_name FROM iam_users WHERE username = '{name}';"
    ], capture_output=True, text=True)

    if name in result.stdout:
        print_success(f"Compte Odoo créé dans iam_users")
        # Afficher les détails
        lines = [l for l in result.stdout.split('\n') if name in l]
        for line in lines:
            print(f"      {line.strip()}")
    else:
        print_warning("Compte Odoo non trouvé")

    # Vérifier PostgreSQL App
    print_info("Vérification compte Application Métier (PostgreSQL)...")
    result = subprocess.run([
        "docker", "exec", "gateway-db", "psql", "-U", "gateway", "-d", "gateway",
        "-c", f"SELECT username, email, user_ldap_dn FROM app_users WHERE username = '{name}';"
    ], capture_output=True, text=True)

    if name in result.stdout:
        print_success(f"Compte Application Métier créé dans app_users")
        lines = [l for l in result.stdout.split('\n') if name in l]
        for line in lines:
            print(f"      {line.strip()}")
    else:
        print_warning("Compte Application Métier non trouvé")

def demo_sync_comparison(token):
    """Démonstration: Comparaison Odoo vs MidPoint"""
    print_header("6. COMPARAISON ODOO ↔ MIDPOINT")

    response = requests.get(
        f"{GATEWAY_URL}/api/v1/live/sync/odoo-midpoint/compare",
        headers=get_headers(token)
    )

    if response.status_code == 200:
        data = response.json()
        print_success("Comparaison effectuée")
        print_info(f"\nStatistiques:")
        print(f"   - Employés Odoo: {data.get('odoo_count', 'N/A')}")
        print(f"   - Utilisateurs MidPoint: {data.get('midpoint_count', 'N/A')}")
        print(f"   - À synchroniser: {len(data.get('to_sync', []))}")
        print(f"   - Déjà synchronisés: {len(data.get('synced', []))}")

        if data.get('to_sync'):
            print_info("\nEmployés à synchroniser (5 premiers):")
            for emp in data.get('to_sync', [])[:5]:
                print(f"      - {emp.get('name', 'N/A')} ({emp.get('email', 'N/A')})")
    else:
        print_error(f"Erreur: {response.status_code}")

def main():
    """Démonstration principale"""
    print(f"""
{Colors.BOLD}{Colors.CYAN}
╔══════════════════════════════════════════════════════════════╗
║     IAM GATEWAY - DÉMONSTRATION MULTI-CONNECTEURS            ║
║                                                              ║
║  Ressources:                                                 ║
║    • OpenLDAP Directory                                      ║
║    • Odoo ERP (table iam_users)                              ║
║    • Application Métier PostgreSQL (table app_users)         ║
║    • Keycloak REST                                           ║
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
""")

    # Authentification
    token = get_token()
    if not token:
        return

    # 1. Lister les employés Odoo
    demo_list_odoo_employees(token)
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")

    # 2. Lister les utilisateurs MidPoint
    demo_list_midpoint_users(token)
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")

    # 3. Lister les rôles
    roles = demo_list_roles(token)
    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")

    # 4. Créer un nouvel utilisateur de démo
    timestamp = datetime.now().strftime("%H%M%S")
    demo_name = f"demo.user{timestamp}"
    demo_email = f"demo.user{timestamp}@example.com"

    user_oid = demo_create_user_via_gateway(
        token, demo_name, demo_email, "Demo", f"User{timestamp}"
    )

    if user_oid:
        # Trouver les OIDs des rôles
        employee_role = next((r for r in roles if r.get('name') == 'Employee-Full-Access'), None)
        app_role = next((r for r in roles if r.get('name') == 'App-Read'), None)

        if employee_role:
            time.sleep(2)
            demo_assign_role(token, user_oid, employee_role['oid'], 'Employee-Full-Access')

        if app_role:
            time.sleep(2)
            demo_assign_role(token, user_oid, app_role['oid'], 'App-Read')

        input(f"\n{Colors.CYAN}Appuyez sur Entrée pour vérifier le provisionnement...{Colors.END}")

        # 5. Vérifier le provisionnement
        time.sleep(3)
        demo_check_provisioning(demo_name)

    input(f"\n{Colors.CYAN}Appuyez sur Entrée pour continuer...{Colors.END}")

    # 6. Comparaison Odoo ↔ MidPoint
    demo_sync_comparison(token)

    print_header("FIN DE LA DÉMONSTRATION")
    print(f"""
{Colors.GREEN}
La démonstration a montré:
  ✓ Connexion à la Gateway IAM via API REST
  ✓ Liste des employés depuis Odoo
  ✓ Liste des utilisateurs MidPoint
  ✓ Catalogue des rôles disponibles
  ✓ Création d'utilisateur avec provisionnement automatique
  ✓ Assignation de rôles (Employee-Full-Access + App-Read)
  ✓ Vérification du provisionnement dans:
      - OpenLDAP
      - Odoo (table iam_users)
      - PostgreSQL Application (table app_users)
  ✓ Comparaison Odoo ↔ MidPoint pour synchronisation

Pour la démonstration via l'interface web:
  → Ouvrez http://localhost:3000
  → Connectez-vous avec admin / admin123
  → Explorez les pages:
      • Dashboard - Vue d'ensemble
      • Live Comparison - Synchronisation Odoo ↔ MidPoint
      • MidPoint Users - Gestion des utilisateurs
{Colors.END}
""")

if __name__ == "__main__":
    main()
