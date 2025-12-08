#!/usr/bin/env python3
"""
Script pour peupler toutes les bases de données avec des utilisateurs de test.
LDAP + Intranet PostgreSQL
"""
import subprocess
import json

# Liste de 30 utilisateurs variés
USERS = [
    {"employee_id": "EMP001", "firstname": "Jean", "lastname": "Dupont", "email": "jean.dupont@example.com", "department": "IT"},
    {"employee_id": "EMP002", "firstname": "Marie", "lastname": "Martin", "email": "marie.martin@example.com", "department": "HR"},
    {"employee_id": "EMP003", "firstname": "Pierre", "lastname": "Bernard", "email": "pierre.bernard@example.com", "department": "Finance"},
    {"employee_id": "EMP004", "firstname": "Sophie", "lastname": "Petit", "email": "sophie.petit@example.com", "department": "IT"},
    {"employee_id": "EMP005", "firstname": "Lucas", "lastname": "Robert", "email": "lucas.robert@example.com", "department": "Sales"},
    {"employee_id": "EMP006", "firstname": "Emma", "lastname": "Richard", "email": "emma.richard@example.com", "department": "Marketing"},
    {"employee_id": "EMP007", "firstname": "Hugo", "lastname": "Durand", "email": "hugo.durand@example.com", "department": "IT"},
    {"employee_id": "EMP008", "firstname": "Lea", "lastname": "Leroy", "email": "lea.leroy@example.com", "department": "HR"},
    {"employee_id": "EMP009", "firstname": "Thomas", "lastname": "Moreau", "email": "thomas.moreau@example.com", "department": "Finance"},
    {"employee_id": "EMP010", "firstname": "Camille", "lastname": "Simon", "email": "camille.simon@example.com", "department": "IT"},
    {"employee_id": "EMP011", "firstname": "Antoine", "lastname": "Laurent", "email": "antoine.laurent@example.com", "department": "Sales"},
    {"employee_id": "EMP012", "firstname": "Julie", "lastname": "Lefebvre", "email": "julie.lefebvre@example.com", "department": "Marketing"},
    {"employee_id": "EMP013", "firstname": "Nicolas", "lastname": "Michel", "email": "nicolas.michel@example.com", "department": "IT"},
    {"employee_id": "EMP014", "firstname": "Sarah", "lastname": "Garcia", "email": "sarah.garcia@example.com", "department": "HR"},
    {"employee_id": "EMP015", "firstname": "Maxime", "lastname": "David", "email": "maxime.david@example.com", "department": "Finance"},
    {"employee_id": "EMP016", "firstname": "Chloe", "lastname": "Bertrand", "email": "chloe.bertrand@example.com", "department": "IT"},
    {"employee_id": "EMP017", "firstname": "Alexandre", "lastname": "Roux", "email": "alexandre.roux@example.com", "department": "Sales"},
    {"employee_id": "EMP018", "firstname": "Laura", "lastname": "Vincent", "email": "laura.vincent@example.com", "department": "Marketing"},
    {"employee_id": "EMP019", "firstname": "Julien", "lastname": "Fournier", "email": "julien.fournier@example.com", "department": "IT"},
    {"employee_id": "EMP020", "firstname": "Manon", "lastname": "Morel", "email": "manon.morel@example.com", "department": "HR"},
    {"employee_id": "EMP021", "firstname": "Paul", "lastname": "Girard", "email": "paul.girard@example.com", "department": "IT"},
    {"employee_id": "EMP022", "firstname": "Charlotte", "lastname": "Bonnet", "email": "charlotte.bonnet@example.com", "department": "Finance"},
    {"employee_id": "EMP023", "firstname": "Gabriel", "lastname": "Dupuis", "email": "gabriel.dupuis@example.com", "department": "Sales"},
    {"employee_id": "EMP024", "firstname": "Ines", "lastname": "Lambert", "email": "ines.lambert@example.com", "department": "Marketing"},
    {"employee_id": "EMP025", "firstname": "Raphael", "lastname": "Fontaine", "email": "raphael.fontaine@example.com", "department": "IT"},
    {"employee_id": "EMP026", "firstname": "Oceane", "lastname": "Rousseau", "email": "oceane.rousseau@example.com", "department": "HR"},
    {"employee_id": "EMP027", "firstname": "Louis", "lastname": "Blanc", "email": "louis.blanc@example.com", "department": "Finance"},
    {"employee_id": "EMP028", "firstname": "Clara", "lastname": "Guerin", "email": "clara.guerin@example.com", "department": "IT"},
    {"employee_id": "EMP029", "firstname": "Nathan", "lastname": "Muller", "email": "nathan.muller@example.com", "department": "Sales"},
    {"employee_id": "EMP030", "firstname": "Pauline", "lastname": "Henry", "email": "pauline.henry@example.com", "department": "Marketing"},
]


def create_ldap_users():
    """Crée les utilisateurs dans LDAP."""
    print("\n" + "="*60)
    print("CREATION DES UTILISATEURS LDAP")
    print("="*60)

    success = 0
    failed = 0

    for user in USERS:
        uid = f"{user['firstname'].lower()}.{user['lastname'].lower()}"
        cn = f"{user['firstname']} {user['lastname']}"

        ldif = f"""dn: uid={uid},ou=users,dc=example,dc=com
objectClass: inetOrgPerson
objectClass: organizationalPerson
objectClass: person
objectClass: top
uid: {uid}
cn: {cn}
sn: {user['lastname']}
givenName: {user['firstname']}
mail: {user['email']}
employeeNumber: {user['employee_id']}
departmentNumber: {user['department']}
userPassword: password123
"""

        # Write LDIF to temp file and add
        result = subprocess.run(
            ["docker", "exec", "-i", "openldap", "ldapadd",
             "-x", "-H", "ldap://localhost",
             "-D", "cn=admin,dc=example,dc=com",
             "-w", "secret"],
            input=ldif,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"  [OK] LDAP: {cn} ({uid})")
            success += 1
        elif "Already exists" in result.stderr:
            print(f"  [SKIP] LDAP: {cn} - existe deja")
            success += 1
        else:
            print(f"  [FAIL] LDAP: {cn} - {result.stderr.strip()}")
            failed += 1

    print(f"\nLDAP: {success} succes, {failed} echecs")
    return success, failed


def create_intranet_users():
    """Crée les utilisateurs dans Intranet PostgreSQL."""
    print("\n" + "="*60)
    print("CREATION DES UTILISATEURS INTRANET (PostgreSQL)")
    print("="*60)

    success = 0
    failed = 0

    for user in USERS:
        username = f"{user['firstname'].lower()[0]}{user['lastname'].lower()}"

        sql = f"""
INSERT INTO users (username, email, first_name, last_name, department, employee_id, is_active)
VALUES ('{username}', '{user['email']}', '{user['firstname']}', '{user['lastname']}', '{user['department']}', '{user['employee_id']}', true)
ON CONFLICT (email) DO NOTHING;
"""

        result = subprocess.run(
            ["docker", "exec", "intranet-db", "psql", "-U", "intranet", "-d", "intranet", "-c", sql],
            capture_output=True,
            text=True
        )

        if "INSERT" in result.stdout or result.returncode == 0:
            print(f"  [OK] Intranet: {user['firstname']} {user['lastname']} ({username})")
            success += 1
        else:
            print(f"  [FAIL] Intranet: {user['firstname']} {user['lastname']} - {result.stderr.strip()}")
            failed += 1

    print(f"\nIntranet: {success} succes, {failed} echecs")
    return success, failed


def show_summary():
    """Affiche le résumé des bases."""
    print("\n" + "="*60)
    print("RESUME DES BASES DE DONNEES")
    print("="*60)

    # LDAP count
    result = subprocess.run(
        ["docker", "exec", "openldap", "ldapsearch",
         "-x", "-H", "ldap://localhost",
         "-b", "ou=users,dc=example,dc=com",
         "-D", "cn=admin,dc=example,dc=com",
         "-w", "secret",
         "(objectClass=inetOrgPerson)", "dn"],
        capture_output=True,
        text=True
    )
    ldap_count = result.stdout.count("dn:")
    print(f"\n📂 LDAP: {ldap_count} utilisateurs")

    # Intranet count
    result = subprocess.run(
        ["docker", "exec", "intranet-db", "psql", "-U", "intranet", "-d", "intranet",
         "-t", "-c", "SELECT COUNT(*) FROM users;"],
        capture_output=True,
        text=True
    )
    intranet_count = result.stdout.strip()
    print(f"🗄️  Intranet DB: {intranet_count} utilisateurs")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("   PEUPLEMENT MASSIF DES BASES DE DONNEES IAM")
    print("="*60)

    ldap_ok, ldap_fail = create_ldap_users()
    intranet_ok, intranet_fail = create_intranet_users()

    show_summary()

    print("\n" + "="*60)
    print(f"TOTAL: {ldap_ok + intranet_ok} operations reussies")
    print("="*60 + "\n")
