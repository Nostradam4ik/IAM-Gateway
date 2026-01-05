#!/usr/bin/env python3
"""
Script d'import des employés Odoo vers MidPoint via CSV
Récupère les dates de début et fin de contrat depuis Odoo
"""

import csv
import json
import subprocess
import requests
from datetime import datetime
import xmlrpc.client
import os
import sys

# Configuration Odoo
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

# Configuration MidPoint
MIDPOINT_URL = os.getenv('MIDPOINT_URL', 'http://localhost:8080/midpoint')
MIDPOINT_USER = os.getenv('MIDPOINT_USER', 'administrator')
MIDPOINT_PASSWORD = os.getenv('MIDPOINT_PASSWORD', 'Holimolly1')

# Chemin du fichier CSV
CSV_OUTPUT_PATH = '/tmp/odoo_employees.csv'
MIDPOINT_CSV_PATH = '/opt/midpoint/var/csv/users.csv'


def connect_odoo():
    """Connexion à Odoo via XML-RPC"""
    print(f"Connexion à Odoo: {ODOO_URL}")

    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')

    try:
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if not uid:
            print("❌ Échec de l'authentification Odoo")
            return None, None

        print(f"✅ Connecté à Odoo (uid: {uid})")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        return uid, models
    except Exception as e:
        print(f"❌ Erreur de connexion Odoo: {e}")
        return None, None


def get_odoo_employees(uid, models):
    """Récupérer les employés depuis Odoo avec les dates"""
    print("\nRécupération des employés Odoo...")

    # Champs à récupérer
    fields = [
        'id', 'name', 'work_email', 'work_phone', 'mobile_phone',
        'department_id', 'job_id', 'parent_id',
        'employee_type', 'active',
        # Dates importantes
        'create_date',
        # Contrat (si module hr_contract installé)
    ]

    employees = models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        'hr.employee', 'search_read',
        [[]],
        {'fields': fields}
    )

    print(f"✅ {len(employees)} employés trouvés")

    # Essayer de récupérer les contrats
    contracts = {}
    try:
        contract_fields = ['employee_id', 'date_start', 'date_end', 'state']
        contract_data = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.contract', 'search_read',
            [[('state', 'in', ['open', 'close'])]],
            {'fields': contract_fields}
        )
        for c in contract_data:
            emp_id = c['employee_id'][0] if c['employee_id'] else None
            if emp_id:
                # Garder le contrat le plus récent
                if emp_id not in contracts or (c.get('date_start') and c['date_start'] > contracts[emp_id].get('date_start', '')):
                    contracts[emp_id] = c
        print(f"✅ {len(contracts)} contrats trouvés")
    except Exception as e:
        print(f"⚠️ Module hr_contract non disponible ou erreur: {e}")

    return employees, contracts


def generate_uid(name, email):
    """Générer un UID unique à partir du nom"""
    if email and '@' in email:
        return email.split('@')[0].lower().replace('.', '_')

    parts = name.lower().split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1]}".replace(' ', '_')
    return name.lower().replace(' ', '_')


def create_csv(employees, contracts):
    """Créer le fichier CSV pour MidPoint"""
    print(f"\nCréation du fichier CSV: {CSV_OUTPUT_PATH}")

    # En-têtes du CSV
    headers = [
        'uid', 'firstname', 'lastname', 'email', 'phone',
        'department', 'job_title', 'manager',
        'start_date', 'end_date', 'active', 'password'
    ]

    rows = []
    for emp in employees:
        name = emp.get('name', '')
        name_parts = name.split(' ', 1)
        firstname = name_parts[0] if name_parts else ''
        lastname = name_parts[1] if len(name_parts) > 1 else ''

        email = emp.get('work_email', '') or ''
        uid = generate_uid(name, email)

        # Récupérer les dates du contrat
        emp_id = emp.get('id')
        contract = contracts.get(emp_id, {})
        start_date = contract.get('date_start', '') or ''
        end_date = contract.get('date_end', '') or ''

        # Si pas de contrat, utiliser create_date comme date de début
        if not start_date and emp.get('create_date'):
            start_date = emp['create_date'][:10]  # Format YYYY-MM-DD

        department = ''
        if emp.get('department_id'):
            department = emp['department_id'][1] if isinstance(emp['department_id'], list) else str(emp['department_id'])

        job_title = ''
        if emp.get('job_id'):
            job_title = emp['job_id'][1] if isinstance(emp['job_id'], list) else str(emp['job_id'])

        manager = ''
        if emp.get('parent_id'):
            manager = emp['parent_id'][1] if isinstance(emp['parent_id'], list) else str(emp['parent_id'])

        row = {
            'uid': uid,
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'phone': emp.get('work_phone', '') or emp.get('mobile_phone', '') or '',
            'department': department,
            'job_title': job_title,
            'manager': manager,
            'start_date': start_date,
            'end_date': end_date,
            'active': 'true' if emp.get('active', True) else 'false',
            'password': ''
        }
        rows.append(row)
        print(f"  - {uid}: {firstname} {lastname} ({department})")

    # Écrire le CSV
    with open(CSV_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ {len(rows)} employés exportés vers {CSV_OUTPUT_PATH}")
    return CSV_OUTPUT_PATH


def copy_to_midpoint(csv_path):
    """Copier le CSV dans le conteneur MidPoint"""
    print(f"\nCopie du CSV vers MidPoint...")

    try:
        # Copier dans le conteneur
        result = subprocess.run(
            ['docker', 'cp', csv_path, f'midpoint-core:{MIDPOINT_CSV_PATH}'],
            capture_output=True, text=True
        )

        if result.returncode == 0:
            print(f"✅ CSV copié vers {MIDPOINT_CSV_PATH}")
            return True
        else:
            print(f"❌ Erreur de copie: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def test_midpoint_resource():
    """Tester la ressource CSV dans MidPoint"""
    print("\nTest de la ressource CSV MidPoint...")

    try:
        response = requests.post(
            f'{MIDPOINT_URL}/ws/rest/resources/10000000-0000-0000-0000-000000000004/test',
            auth=(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Accept': 'application/json'}
        )

        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'unknown')
            if status == 'success':
                print("✅ Ressource CSV fonctionnelle")
                return True
            else:
                print(f"⚠️ Status: {status}")
                return False
        else:
            print(f"❌ Erreur HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def import_accounts_to_midpoint():
    """Importer les comptes depuis la ressource CSV"""
    print("\nImport des comptes dans MidPoint...")

    # Mettre à jour la ressource CSV d'abord
    resource_path = os.path.join(os.path.dirname(__file__),
        '../infrastructure/midpoint/resources/csv-resource.xml')
    if os.path.exists(resource_path):
        with open(resource_path, 'r') as f:
            resource_xml = f.read()
        response = requests.put(
            f'{MIDPOINT_URL}/ws/rest/resources/10000000-0000-0000-0000-000000000004',
            auth=(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=resource_xml
        )
        if response.status_code in [200, 204]:
            print("✅ Ressource CSV mise à jour")

    # Lancer une tâche d'import avec objectClass spécifié
    from datetime import datetime
    task_name = f"Import CSV Employees - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import_task = f"""<?xml version="1.0" encoding="UTF-8"?>
<task xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      xmlns:ri="http://midpoint.evolveum.com/xml/ns/public/resource/instance-3">
    <name>{task_name}</name>
    <executionState>runnable</executionState>
    <activity>
        <work>
            <import>
                <resourceObjects>
                    <resourceRef oid="10000000-0000-0000-0000-000000000004"/>
                    <kind>account</kind>
                    <intent>default</intent>
                    <objectclass>ri:AccountObjectClass</objectclass>
                </resourceObjects>
            </import>
        </work>
    </activity>
</task>"""

    try:
        response = requests.post(
            f'{MIDPOINT_URL}/ws/rest/tasks',
            auth=(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=import_task
        )

        if response.status_code in [200, 201, 202]:
            print("✅ Tâche d'import lancée avec succès")
            return True
        else:
            print(f"⚠️ Réponse: {response.status_code}")
            print(response.text[:500])
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


def main():
    print("=" * 60)
    print("Import Odoo → MidPoint via CSV")
    print("=" * 60)

    # 1. Connexion à Odoo
    uid, models = connect_odoo()
    if not uid:
        print("\n⚠️ Utilisation du fichier CSV existant...")
        # Utiliser le fichier téléchargé manuellement
        csv_source = '/home/vboxuser/Downloads/Employee (hr.employee).csv'
        if os.path.exists(csv_source):
            print(f"Conversion du fichier: {csv_source}")
            convert_downloaded_csv(csv_source)
        else:
            sys.exit(1)
    else:
        # 2. Récupérer les employés
        employees, contracts = get_odoo_employees(uid, models)

        # 3. Créer le CSV
        create_csv(employees, contracts)

    # 4. Copier vers MidPoint
    if not copy_to_midpoint(CSV_OUTPUT_PATH):
        sys.exit(1)

    # 5. Tester la ressource
    test_midpoint_resource()

    # 6. Importer dans MidPoint
    import_accounts_to_midpoint()

    print("\n" + "=" * 60)
    print("✅ Import terminé!")
    print("=" * 60)


def convert_downloaded_csv(source_path):
    """Convertir le CSV téléchargé d'Odoo au format MidPoint"""
    print(f"Conversion de {source_path}...")

    rows = []
    with open(source_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('Employee Name', '')
            name_parts = name.split(' ', 1)
            firstname = name_parts[0] if name_parts else ''
            lastname = name_parts[1] if len(name_parts) > 1 else ''

            email = row.get('Work Email', '') or ''
            uid = generate_uid(name, email)

            # Extraire le département (prendre le dernier niveau)
            dept_full = row.get('Department', '')
            department = dept_full.split('/')[-1].strip() if dept_full else ''

            new_row = {
                'uid': uid,
                'firstname': firstname,
                'lastname': lastname,
                'email': email,
                'phone': row.get('Work Phone', ''),
                'department': department,
                'job_title': row.get('Job Position', ''),
                'manager': row.get('Manager', ''),
                'start_date': '',  # À remplir via API
                'end_date': '',
                'active': 'true',
                'password': ''
            }
            rows.append(new_row)
            print(f"  - {uid}: {firstname} {lastname}")

    # Écrire le nouveau CSV
    headers = ['uid', 'firstname', 'lastname', 'email', 'phone',
               'department', 'job_title', 'manager', 'start_date', 'end_date', 'active', 'password']

    with open(CSV_OUTPUT_PATH, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ {len(rows)} employés convertis")


if __name__ == '__main__':
    main()
