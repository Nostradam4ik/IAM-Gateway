#!/usr/bin/env python3
"""
Script de synchronisation Odoo → CSV → MidPoint
Exporte les employés d'Odoo vers un fichier CSV, puis déclenche l'import dans MidPoint
"""

import xmlrpc.client
import csv
import os
import requests
from requests.auth import HTTPBasicAuth
import argparse
from datetime import datetime

# Configuration Odoo
ODOO_URL = os.getenv("ODOO_URL", "http://localhost:8069")
ODOO_DB = os.getenv("ODOO_DB", "odoo")
ODOO_USER = os.getenv("ODOO_USER", "admin")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD", "admin")

# Configuration MidPoint
MIDPOINT_URL = os.getenv("MIDPOINT_URL", "http://localhost:8080/midpoint")
MIDPOINT_USER = os.getenv("MIDPOINT_USER", "administrator")
MIDPOINT_PASSWORD = os.getenv("MIDPOINT_PASSWORD", "5ecr3t")

# Chemin du fichier CSV
CSV_PATH = "/home/vboxuser/Desktop/Project3/datasets/hr_employees.csv"
MIDPOINT_CSV_PATH = "/opt/midpoint/var/import/hr_sample.csv"


def connect_odoo():
    """Connexion à Odoo via XML-RPC"""
    print(f"[INFO] Connexion à Odoo: {ODOO_URL}")

    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')

    try:
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if uid:
            print(f"[OK] Connecté à Odoo (uid: {uid})")
            models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
            return uid, models
        else:
            print("[ERREUR] Authentification Odoo échouée")
            return None, None
    except Exception as e:
        print(f"[ERREUR] Connexion Odoo: {e}")
        return None, None


def export_employees_from_odoo(uid, models):
    """Exporte les employés d'Odoo"""
    print("[INFO] Export des employés depuis Odoo...")

    try:
        # Rechercher tous les employés
        employee_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.employee', 'search',
            [[]]  # Tous les employés
        )

        if not employee_ids:
            print("[WARN] Aucun employé trouvé dans Odoo")
            return []

        # Récupérer les détails des employés
        employees = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.employee', 'read',
            [employee_ids],
            {'fields': ['name', 'work_email', 'department_id', 'job_title', 'identification_id']}
        )

        print(f"[OK] {len(employees)} employés trouvés")
        return employees

    except Exception as e:
        print(f"[ERREUR] Export Odoo: {e}")
        return []


def create_csv_file(employees, csv_path):
    """Crée le fichier CSV pour MidPoint"""
    print(f"[INFO] Création du fichier CSV: {csv_path}")

    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')

        # En-tête
        writer.writerow(['uid', 'givenName', 'familyName', 'email', 'department'])

        for i, emp in enumerate(employees, start=1):
            name_parts = emp.get('name', '').split(' ', 1)
            given_name = name_parts[0] if name_parts else ''
            family_name = name_parts[1] if len(name_parts) > 1 else ''

            email = emp.get('work_email') or f"user{i}@example.com"
            department = emp.get('department_id', [None, 'Unknown'])
            dept_name = department[1] if isinstance(department, list) and len(department) > 1 else 'Unknown'

            # Générer un UID unique
            uid = emp.get('identification_id') or f"u{1000 + i}"

            writer.writerow([uid, given_name, family_name, email, dept_name])
            print(f"  - {given_name} {family_name} ({email})")

    print(f"[OK] Fichier CSV créé avec {len(employees)} entrées")
    return csv_path


def copy_csv_to_midpoint(local_csv_path):
    """Copie le fichier CSV dans le container MidPoint"""
    print("[INFO] Copie du CSV vers MidPoint...")

    import subprocess
    result = subprocess.run(
        ['docker', 'cp', local_csv_path, f'midpoint-core:{MIDPOINT_CSV_PATH}'],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        print(f"[OK] CSV copié vers {MIDPOINT_CSV_PATH}")
        return True
    else:
        print(f"[ERREUR] Copie échouée: {result.stderr}")
        return False


def trigger_midpoint_import():
    """Déclenche l'import dans MidPoint via l'API REST"""
    print("[INFO] Déclenchement de l'import MidPoint...")

    # Récupérer l'OID de la ressource CSV
    resource_oid = "8a8b9c1d-0002-0000-0000-000000000001"  # HR CSV Resource

    try:
        # Tester la connexion à la ressource
        response = requests.post(
            f"{MIDPOINT_URL}/ws/rest/resources/{resource_oid}/test",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        print(f"[INFO] Test ressource: HTTP {response.status_code}")

        # Déclencher une tâche de réconciliation ou import
        task_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<task xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3">
    <name>Import HR CSV - {datetime.now().strftime('%Y%m%d_%H%M%S')}</name>
    <extension xmlns:mext="http://midpoint.evolveum.com/xml/ns/public/model/extension-3">
        <mext:objectclass>ri:AccountObjectClass</mext:objectclass>
    </extension>
    <ownerRef oid="00000000-0000-0000-0000-000000000002" type="UserType"/>
    <executionState>runnable</executionState>
    <category>ImportingAccounts</category>
    <handlerUri>http://midpoint.evolveum.com/xml/ns/public/model/synchronization/task/import/handler-3</handlerUri>
    <objectRef oid="{resource_oid}" type="ResourceType"/>
    <recurrence>single</recurrence>
</task>"""

        response = requests.post(
            f"{MIDPOINT_URL}/ws/rest/tasks",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={"Content-Type": "application/xml"},
            data=task_xml,
            timeout=30
        )

        if response.status_code in [200, 201, 202]:
            print("[OK] Tâche d'import créée dans MidPoint")
            return True
        else:
            print(f"[WARN] Réponse MidPoint: {response.status_code}")
            print(f"  {response.text[:500]}")
            return False

    except Exception as e:
        print(f"[ERREUR] Import MidPoint: {e}")
        return False


def list_midpoint_users():
    """Liste les utilisateurs dans MidPoint"""
    print("\n[INFO] Utilisateurs dans MidPoint:")

    try:
        response = requests.get(
            f"{MIDPOINT_URL}/ws/rest/users",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={"Accept": "application/json"},
            params={"_size": 20},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            users = data.get('object', {}).get('object', [])
            for user in users:
                name = user.get('name', 'Unknown')
                oid = user.get('oid', 'N/A')[:8]
                print(f"  - {name} (OID: {oid}...)")
            print(f"[OK] Total: {len(users)} utilisateurs")
        else:
            print(f"[ERREUR] {response.status_code}")

    except Exception as e:
        print(f"[ERREUR] {e}")


def main():
    parser = argparse.ArgumentParser(description='Synchronisation Odoo → CSV → MidPoint')
    parser.add_argument('--skip-odoo', action='store_true', help='Utiliser le CSV existant sans exporter depuis Odoo')
    parser.add_argument('--list-users', action='store_true', help='Lister les utilisateurs MidPoint')
    args = parser.parse_args()

    print("=" * 60)
    print("  SYNCHRONISATION ODOO → CSV → MIDPOINT")
    print("=" * 60)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if args.list_users:
        list_midpoint_users()
        return

    if not args.skip_odoo:
        # Étape 1: Connexion à Odoo
        uid, models = connect_odoo()

        if uid and models:
            # Étape 2: Export des employés
            employees = export_employees_from_odoo(uid, models)

            if employees:
                # Étape 3: Création du CSV
                create_csv_file(employees, CSV_PATH)
            else:
                print("[WARN] Utilisation du CSV existant")
        else:
            print("[WARN] Connexion Odoo échouée, utilisation du CSV existant")

    # Étape 4: Copie vers MidPoint
    csv_to_copy = CSV_PATH if os.path.exists(CSV_PATH) else "/home/vboxuser/Desktop/Project3/datasets/hr_sample.csv"
    if copy_csv_to_midpoint(csv_to_copy):
        # Étape 5: Import dans MidPoint
        trigger_midpoint_import()

    # Afficher les utilisateurs MidPoint
    list_midpoint_users()

    print("\n" + "=" * 60)
    print("  SYNCHRONISATION TERMINÉE")
    print("=" * 60)


if __name__ == "__main__":
    main()
