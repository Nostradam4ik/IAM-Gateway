#!/usr/bin/env python3
import json
import subprocess
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsInJvbGVzIjpbImFkbWluIiwiaWFtX2VuZ2luZWVyIl0sImV4cCI6MTc2NTIwMzUzOH0.19fiRuMa-ZjpAx3v7c7hbC7MuEZWlwvDPN1ajtGcfxw"

users = [
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

print(f"=== Creation de {len(users)} utilisateurs ===\n")

success = 0
failed = 0

for i, user in enumerate(users):
    payload = {
        "source_type": "HR",
        "target_systems": ["LDAP", "Odoo"],
        "user_data": {
            "employee_id": user["employee_id"],
            "firstname": user["firstname"],
            "lastname": user["lastname"],
            "email": user["email"],
            "department": user["department"],
            "first_name": user["firstname"],
            "last_name": user["lastname"],
            "account_id": f"{user['firstname'].lower()}.{user['lastname'].lower()}"
        },
        "priority": "normal"
    }

    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "http://localhost:8000/api/v1/provision/",
        "-H", f"Authorization: Bearer {TOKEN}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ], capture_output=True, text=True)

    try:
        response = json.loads(result.stdout)
        status = response.get("status", "unknown")
        if "error" in result.stdout.lower():
            print(f"[{i+1:02d}/{len(users)}] ERREUR - {user['firstname']} {user['lastname']}: {result.stdout[:60]}")
            failed += 1
        else:
            print(f"[{i+1:02d}/{len(users)}] OK - {user['firstname']} {user['lastname']} ({user['department']})")
            success += 1
    except:
        print(f"[{i+1:02d}/{len(users)}] ??? - {user['firstname']} {user['lastname']}: {result.stdout[:60]}")
        failed += 1

    time.sleep(0.2)

print(f"\n=== Resultat: {success} succes, {failed} echecs ===")
