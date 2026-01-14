#!/usr/bin/env python3
"""
Script de Démonstration: Synchronisation Directe Sans Gateway
Synchronise Odoo → LDAP et Odoo → PostgreSQL directement
"""

import xmlrpc.client
import psycopg2
import sys
from typing import List, Dict

# Couleurs pour l'affichage
class Colors:
    BLUE = '\033[0;34m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'

def print_step(msg: str):
    print(f"{Colors.BLUE}[ETAPE]{Colors.NC} {msg}")

def print_success(msg: str):
    print(f"{Colors.GREEN}[OK]{Colors.NC} {msg}")

def print_warning(msg: str):
    print(f"{Colors.YELLOW}[ATTENTION]{Colors.NC} {msg}")

def print_error(msg: str):
    print(f"{Colors.RED}[ERREUR]{Colors.NC} {msg}")

def print_header():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║  DEMONSTRATION: SYNCHRONISATION DIRECTE SANS GATEWAY IAM      ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()

def get_odoo_employees() -> List[Dict]:
    """Récupère les employés depuis Odoo"""
    print_step("Connexion à Odoo...")

    try:
        url = "http://localhost:8069"
        db = "odoo"
        username = "admin"
        password = "admin"

        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})

        if not uid:
            print_error("Authentification Odoo échouée")
            return []

        print_success(f"Connecté à Odoo (UID: {uid})")

        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

        # Récupérer les employés avec leurs informations
        employees = models.execute_kw(db, uid, password,
            'hr.employee', 'search_read',
            [[]],
            {'fields': ['name', 'work_email', 'department_id', 'job_id', 'work_phone', 'mobile_phone']}
        )

        print_success(f"Récupéré {len(employees)} employés depuis Odoo")
        return employees

    except Exception as e:
        print_error(f"Erreur Odoo: {e}")
        return []

def sync_to_ldif(employees: List[Dict]) -> str:
    """Génère un fichier LDIF à partir des employés Odoo"""
    print_step("Génération du fichier LDIF...")

    ldif_content = []
    count = 0

    for emp in employees:
        if emp.get('work_email'):
            username = emp['work_email'].split('@')[0]
            name_parts = emp['name'].split()
            first_name = name_parts[0] if name_parts else ''
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]

            ldif_content.append(f"dn: uid={username},ou=people,dc=example,dc=com")
            ldif_content.append(f"objectClass: inetOrgPerson")
            ldif_content.append(f"objectClass: organizationalPerson")
            ldif_content.append(f"objectClass: person")
            ldif_content.append(f"objectClass: top")
            ldif_content.append(f"uid: {username}")
            ldif_content.append(f"cn: {emp['name']}")
            ldif_content.append(f"sn: {last_name}")
            ldif_content.append(f"givenName: {first_name}")
            ldif_content.append(f"mail: {emp['work_email']}")

            if emp.get('department_id'):
                dept = emp['department_id'][1]
                ldif_content.append(f"ou: {dept}")

            if emp.get('work_phone'):
                ldif_content.append(f"telephoneNumber: {emp['work_phone']}")

            if emp.get('job_id'):
                ldif_content.append(f"title: {emp['job_id'][1]}")

            ldif_content.append("")
            count += 1

    ldif_file = '/tmp/odoo_sync_to_ldap.ldif'
    with open(ldif_file, 'w') as f:
        f.write('\n'.join(ldif_content))

    print_success(f"Fichier LDIF créé : {ldif_file}")
    print_success(f"{count} utilisateurs prêts pour LDAP")

    return ldif_file

def sync_to_postgresql(employees: List[Dict]) -> int:
    """Synchronise les employés vers PostgreSQL"""
    print_step("Synchronisation vers PostgreSQL...")

    try:
        conn = psycopg2.connect(
            host="localhost",
            port="55432",
            database="intranet",
            user="intranet",
            password="intranet"
        )
        cur = conn.cursor()

        print_success("Connecté à PostgreSQL")

        count_success = 0
        count_error = 0

        for emp in employees:
            if emp.get('work_email'):
                try:
                    username = emp['work_email'].split('@')[0]
                    name_parts = emp['name'].split()
                    first_name = name_parts[0] if name_parts else ''
                    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else name_parts[0]
                    department = emp['department_id'][1] if emp.get('department_id') else None
                    job_title = emp['job_id'][1] if emp.get('job_id') else None
                    phone = emp.get('work_phone') or emp.get('mobile_phone')

                    cur.execute("""
                        INSERT INTO users (username, email, first_name, last_name, department, job_title, phone, is_active)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, true)
                        ON CONFLICT (username)
                        DO UPDATE SET
                            email = EXCLUDED.email,
                            first_name = EXCLUDED.first_name,
                            last_name = EXCLUDED.last_name,
                            department = EXCLUDED.department,
                            job_title = EXCLUDED.job_title,
                            phone = EXCLUDED.phone,
                            updated_at = CURRENT_TIMESTAMP
                    """, (username, emp['work_email'], first_name, last_name, department, job_title, phone))

                    count_success += 1

                except Exception as e:
                    print_warning(f"Erreur pour {emp['name']}: {e}")
                    count_error += 1

        conn.commit()
        cur.close()
        conn.close()

        print_success(f"{count_success} utilisateurs synchronisés vers PostgreSQL")
        if count_error > 0:
            print_warning(f"{count_error} erreurs lors de la synchronisation")

        return count_success

    except Exception as e:
        print_error(f"Erreur PostgreSQL: {e}")
        return 0

def verify_ldap():
    """Vérifie le nombre d'entrées dans LDAP"""
    print_step("Vérification LDAP...")

    import subprocess

    try:
        result = subprocess.run([
            'docker', 'exec', 'openldap',
            'ldapsearch', '-x', '-H', 'ldap://localhost',
            '-b', 'ou=people,dc=example,dc=com',
            '-D', 'cn=admin,dc=example,dc=com',
            '-w', 'secret',
            '(objectClass=inetOrgPerson)'
        ], capture_output=True, text=True)

        count = result.stdout.count('dn: uid=')
        print_success(f"LDAP contient {count} utilisateurs")
        return count

    except Exception as e:
        print_warning(f"Impossible de vérifier LDAP: {e}")
        return None

def verify_postgresql():
    """Vérifie le nombre d'utilisateurs dans PostgreSQL"""
    print_step("Vérification PostgreSQL...")

    try:
        conn = psycopg2.connect(
            host="localhost",
            port="55432",
            database="intranet",
            user="intranet",
            password="intranet"
        )
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM users;")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        print_success(f"PostgreSQL contient {count} utilisateurs")
        return count

    except Exception as e:
        print_warning(f"Impossible de vérifier PostgreSQL: {e}")
        return None

def print_summary(odoo_count: int, ldif_file: str, postgres_count: int):
    """Affiche le résumé de la synchronisation"""
    print()
    print("════════════════════════════════════════════════════════════════")
    print_step("RÉSULTATS DE LA SYNCHRONISATION")
    print("════════════════════════════════════════════════════════════════")
    print()

    print("📊 Statistiques:")
    print(f"   Employés Odoo:        {odoo_count}")
    print(f"   Fichier LDIF:         {ldif_file}")
    print(f"   Synchro PostgreSQL:   {postgres_count}")
    print()

    ldap_count = verify_ldap()
    postgres_total = verify_postgresql()

    print()
    print("📈 État des systèmes:")
    print(f"   OpenLDAP:     {ldap_count if ldap_count else 'N/A'} entrées")
    print(f"   PostgreSQL:   {postgres_total if postgres_total else 'N/A'} utilisateurs")
    print()

    print("════════════════════════════════════════════════════════════════")
    print_step("PROCHAINES ÉTAPES")
    print("════════════════════════════════════════════════════════════════")
    print()
    print("1. Importer le fichier LDIF dans OpenLDAP:")
    print(f"   docker exec -i openldap ldapadd -x -H ldap://localhost \\")
    print(f"     -D 'cn=admin,dc=example,dc=com' -w secret \\")
    print(f"     < {ldif_file}")
    print()
    print("2. Vérifier dans phpLDAPadmin:")
    print("   → http://localhost:8088")
    print("   → Login: cn=admin,dc=example,dc=com / secret")
    print()
    print("3. Vérifier dans PostgreSQL:")
    print("   docker exec intranet-db psql -U intranet -d intranet \\")
    print("     -c 'SELECT username, email, department FROM users LIMIT 10;'")
    print()
    print("════════════════════════════════════════════════════════════════")
    print_success("SYNCHRONISATION TERMINÉE")
    print("════════════════════════════════════════════════════════════════")
    print()

def main():
    """Fonction principale"""
    print_header()

    # 1. Récupérer les employés d'Odoo
    employees = get_odoo_employees()

    if not employees:
        print_error("Aucun employé récupéré. Vérifiez qu'Odoo est accessible.")
        sys.exit(1)

    print()

    # 2. Générer le fichier LDIF
    ldif_file = sync_to_ldif(employees)
    print()

    # 3. Synchroniser vers PostgreSQL
    postgres_count = sync_to_postgresql(employees)
    print()

    # 4. Afficher le résumé
    print_summary(len(employees), ldif_file, postgres_count)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Interruption par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print()
        print_error(f"Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
