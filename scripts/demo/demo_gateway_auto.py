#!/usr/bin/env python3
"""
===================================================================
    DÉMONSTRATION IAM GATEWAY - VERSION NON-INTERACTIVE
===================================================================

Ce script démontre les capacités de l'IAM Gateway automatiquement.
"""

import requests
import json
import time
from datetime import datetime
import subprocess

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
    """Liste les employés Odoo"""
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
    """Liste les utilisateurs MidPoint"""
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
    """Liste les rôles disponibles"""
    print_header("3. RÔLES DISPONIBLES DANS MIDPOINT")

    response = requests.get(
        f"{GATEWAY_URL}/api/v1/midpoint/roles",
        headers=get_headers(token)
    )

    if response.status_code == 200:
        data = response.json()
        print_success(f"Nombre de rôles: {data.get('total', 0)}")

        roles = data.get('roles', [])
        dept_roles = [r for r in roles if 'Department' in r.get('name', '')]
        employee_roles = [r for r in roles if 'Employee' in r.get('name', '')]
        app_roles = [r for r in roles if 'App' in r.get('name', '')]

        print_info("\nRôles par catégorie:")
        print(f"\n   {Colors.BOLD}Employé:{Colors.END}")
        for r in employee_roles:
            print(f"      - {r['name']}")

        print(f"\n   {Colors.BOLD}Départements:{Colors.END}")
        for r in dept_roles[:5]:
            print(f"      - {r['name']}")

        print(f"\n   {Colors.BOLD}Application Métier:{Colors.END}")
        for r in app_roles:
            risk = " ⚠️ CRITIQUE" if "Admin" in r.get('name', '') else ""
            print(f"      - {r['name']}{risk}")

        return roles
    else:
        print_error(f"Erreur: {response.status_code}")
        return []

def demo_check_provisioning(name):
    """Vérifier le provisionnement dans les systèmes cibles"""
    print_header(f"4. VÉRIFICATION DU PROVISIONNEMENT: {name}")

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
    """Comparaison Odoo vs MidPoint"""
    print_header("5. COMPARAISON ODOO ↔ MIDPOINT")

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
╚══════════════════════════════════════════════════════════════╝
{Colors.END}
""")

    # Authentification
    token = get_token()
    if not token:
        return

    # 1. Lister les employés Odoo
    demo_list_odoo_employees(token)

    # 2. Lister les utilisateurs MidPoint
    demo_list_midpoint_users(token)

    # 3. Lister les rôles
    demo_list_roles(token)

    # 4. Vérifier un utilisateur existant (sabine.decreteil)
    demo_check_provisioning("sabine.decreteil")

    # 5. Comparaison Odoo ↔ MidPoint
    demo_sync_comparison(token)

    print_header("FIN DE LA DÉMONSTRATION")
    print(f"""
{Colors.GREEN}
La démonstration a montré:
  ✓ Connexion à la Gateway IAM via API REST
  ✓ Liste des employés depuis Odoo
  ✓ Liste des utilisateurs MidPoint
  ✓ Catalogue des rôles disponibles
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
