#!/usr/bin/env python3
"""
Script pour importer les configurations MidPoint (Ressources, Rôles)
Exécuter après un git pull pour configurer MidPoint automatiquement
"""

import requests
from requests.auth import HTTPBasicAuth
import os
import sys

# Configuration MidPoint
MIDPOINT_URL = os.getenv("MIDPOINT_URL", "http://localhost:8080/midpoint")
MIDPOINT_USER = os.getenv("MIDPOINT_USER", "administrator")
MIDPOINT_PASSWORD = os.getenv("MIDPOINT_PASSWORD", "5ecr3t")

# Chemins des fichiers à importer (dans l'ordre)
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Ordre d'import important : d'abord les ressources, puis les rôles
FILES_TO_IMPORT = [
    # Ressources (connecteurs)
    ("resources", "infrastructure/midpoint/resources/hr-csv-complete.xml", "CSV HR Import"),
    ("resources", "infrastructure/midpoint/resources/openldap-resource.xml", "OpenLDAP Directory"),

    # Rôles
    ("roles", "infrastructure/midpoint/roles/role-ldap-user.xml", "LDAP User Role"),
    ("roles", "infrastructure/midpoint/roles/keycloak-user-role.xml", "Keycloak User Role"),
    ("roles", "infrastructure/midpoint/roles/role-employee.xml", "Employee Role"),
]


def check_midpoint_available():
    """Vérifie si MidPoint est accessible"""
    try:
        response = requests.get(
            f"{MIDPOINT_URL}/ws/rest/users",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={"Accept": "application/json"},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[ERREUR] MidPoint non accessible: {e}")
        return False


def import_object(object_type, file_path, description):
    """Importe un objet dans MidPoint"""
    full_path = os.path.join(BASE_PATH, file_path)

    if not os.path.exists(full_path):
        print(f"[SKIP] Fichier non trouvé: {file_path}")
        return False

    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        # Endpoint selon le type d'objet
        endpoint = f"{MIDPOINT_URL}/ws/rest/{object_type}"

        response = requests.post(
            endpoint,
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={
                "Content-Type": "application/xml",
                "Accept": "application/json"
            },
            data=xml_content.encode('utf-8'),
            timeout=30
        )

        if response.status_code in [200, 201]:
            print(f"[OK] {description}")
            return True
        elif response.status_code == 409:
            print(f"[EXISTE] {description} (déjà configuré)")
            return True
        else:
            print(f"[ERREUR] {description}: HTTP {response.status_code}")
            if response.text:
                print(f"         {response.text[:200]}")
            return False

    except Exception as e:
        print(f"[ERREUR] {description}: {e}")
        return False


def main():
    print("=" * 60)
    print("    IMPORT CONFIGURATION MIDPOINT")
    print("=" * 60)
    print()

    # Vérifier MidPoint
    print("[INFO] Vérification de MidPoint...")
    if not check_midpoint_available():
        print("[ERREUR] MidPoint n'est pas accessible!")
        print("         Vérifiez que les services Docker sont démarrés:")
        print("         docker compose up -d")
        print("         Attendez 2-3 minutes et réessayez.")
        sys.exit(1)

    print("[OK] MidPoint est accessible")
    print()

    # Importer les objets
    print("[INFO] Import des configurations...")
    print("-" * 60)

    success_count = 0
    total_count = len(FILES_TO_IMPORT)

    for object_type, file_path, description in FILES_TO_IMPORT:
        if import_object(object_type, file_path, description):
            success_count += 1

    print("-" * 60)
    print()
    print(f"[RÉSULTAT] {success_count}/{total_count} objets importés")
    print()

    if success_count == total_count:
        print("[SUCCESS] Configuration MidPoint terminée!")
        print()
        print("Prochaines étapes:")
        print("  1. Synchroniser Odoo → MidPoint:")
        print("     python3 scripts/odoo_to_midpoint_sync.py")
        print()
        print("  2. Synchroniser MidPoint → Keycloak:")
        print("     python3 scripts/midpoint_to_keycloak_sync.py --sync")
        print()
        print("  3. Accéder à MidPoint:")
        print("     URL: http://localhost:8080/midpoint")
        print("     Login: administrator / 5ecr3t")
    else:
        print("[ATTENTION] Certains objets n'ont pas été importés.")
        print("            Vérifiez les erreurs ci-dessus.")


if __name__ == "__main__":
    main()
