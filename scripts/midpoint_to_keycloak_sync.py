#!/usr/bin/env python3
"""
Script de synchronisation MidPoint → Keycloak
Provisionne les utilisateurs MidPoint vers Keycloak (realm gateway)
"""

import requests
from requests.auth import HTTPBasicAuth
import json
import os
import argparse
from datetime import datetime

# Configuration MidPoint
MIDPOINT_URL = os.getenv("MIDPOINT_URL", "http://localhost:8080/midpoint")
MIDPOINT_USER = os.getenv("MIDPOINT_USER", "administrator")
MIDPOINT_PASSWORD = os.getenv("MIDPOINT_PASSWORD", "5ecr3t")

# Configuration Keycloak
KEYCLOAK_URL = os.getenv("KEYCLOAK_URL", "http://localhost:8081")
KEYCLOAK_REALM = os.getenv("KEYCLOAK_REALM", "gateway")
KEYCLOAK_ADMIN_USER = os.getenv("KEYCLOAK_ADMIN_USER", "admin")
KEYCLOAK_ADMIN_PASSWORD = os.getenv("KEYCLOAK_ADMIN_PASSWORD", "admin")

# Rôle MidPoint qui déclenche le provisioning Keycloak
KEYCLOAK_ROLE_OID = "12345678-1234-1234-1234-000000000002"


def get_keycloak_token():
    """Obtient un token d'accès admin pour Keycloak"""
    print("[INFO] Obtention du token Keycloak...")

    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token",
            data={
                "username": KEYCLOAK_ADMIN_USER,
                "password": KEYCLOAK_ADMIN_PASSWORD,
                "grant_type": "password",
                "client_id": "admin-cli"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )

        if response.status_code == 200:
            token = response.json().get("access_token")
            print("[OK] Token Keycloak obtenu")
            return token
        else:
            print(f"[ERREUR] Token Keycloak: {response.status_code}")
            return None
    except Exception as e:
        print(f"[ERREUR] Connexion Keycloak: {e}")
        return None


def get_midpoint_users():
    """Récupère les utilisateurs MidPoint avec le rôle Keycloak"""
    print("[INFO] Récupération des utilisateurs MidPoint...")

    try:
        response = requests.get(
            f"{MIDPOINT_URL}/ws/rest/users",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={"Accept": "application/json"},
            params={"_size": 100},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            users = data.get("object", {}).get("object", [])
            print(f"[OK] {len(users)} utilisateurs trouvés dans MidPoint")
            return users
        else:
            print(f"[ERREUR] MidPoint API: {response.status_code}")
            return []
    except Exception as e:
        print(f"[ERREUR] Connexion MidPoint: {e}")
        return []


def get_user_details(oid):
    """Récupère les détails complets d'un utilisateur MidPoint"""
    try:
        response = requests.get(
            f"{MIDPOINT_URL}/ws/rest/users/{oid}",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={"Accept": "application/json"},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            # Les données sont sous la clé 'user'
            return data.get("user", data)
        return None
    except Exception as e:
        print(f"[ERREUR] Détails utilisateur {oid}: {e}")
        return None


def check_user_has_keycloak_role(user_data):
    """Vérifie si l'utilisateur a le rôle Keycloak User"""
    assignments = user_data.get("assignment", [])
    if not isinstance(assignments, list):
        assignments = [assignments]

    for assignment in assignments:
        target_ref = assignment.get("targetRef", {})
        if target_ref.get("oid") == KEYCLOAK_ROLE_OID:
            return True
    return False


def get_keycloak_users(token):
    """Récupère les utilisateurs existants dans Keycloak"""
    print(f"[INFO] Récupération des utilisateurs Keycloak (realm: {KEYCLOAK_REALM})...")

    try:
        response = requests.get(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            params={"max": 1000},
            timeout=30
        )

        if response.status_code == 200:
            users = response.json()
            print(f"[OK] {len(users)} utilisateurs dans Keycloak")
            return {u.get("username"): u for u in users}
        else:
            print(f"[ERREUR] Keycloak users API: {response.status_code}")
            return {}
    except Exception as e:
        print(f"[ERREUR] {e}")
        return {}


def create_keycloak_user(token, user_data):
    """Crée un utilisateur dans Keycloak"""
    username = user_data.get("username")
    print(f"[INFO] Création utilisateur Keycloak: {username}")

    keycloak_user = {
        "username": username,
        "email": user_data.get("email", f"{username}@example.com"),
        "firstName": user_data.get("firstName", ""),
        "lastName": user_data.get("lastName", ""),
        "enabled": True,
        "emailVerified": True,
        "credentials": [{
            "type": "password",
            "value": "changeme123",  # Mot de passe par défaut
            "temporary": True  # Force le changement au premier login
        }]
    }

    try:
        response = requests.post(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=keycloak_user,
            timeout=30
        )

        if response.status_code == 201:
            print(f"[OK] Utilisateur créé: {username}")
            return True
        elif response.status_code == 409:
            print(f"[WARN] Utilisateur existe déjà: {username}")
            return True
        else:
            print(f"[ERREUR] Création {username}: {response.status_code} - {response.text[:200]}")
            return False
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def update_keycloak_user(token, keycloak_id, user_data):
    """Met à jour un utilisateur dans Keycloak"""
    username = user_data.get("username")
    print(f"[INFO] Mise à jour utilisateur Keycloak: {username}")

    keycloak_user = {
        "email": user_data.get("email"),
        "firstName": user_data.get("firstName"),
        "lastName": user_data.get("lastName"),
        "enabled": True
    }

    try:
        response = requests.put(
            f"{KEYCLOAK_URL}/admin/realms/{KEYCLOAK_REALM}/users/{keycloak_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            json=keycloak_user,
            timeout=30
        )

        if response.status_code == 204:
            print(f"[OK] Utilisateur mis à jour: {username}")
            return True
        else:
            print(f"[ERREUR] Mise à jour {username}: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def sync_users():
    """Synchronise les utilisateurs MidPoint vers Keycloak"""
    print("=" * 60)
    print("  SYNCHRONISATION MIDPOINT → KEYCLOAK")
    print("=" * 60)
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Realm Keycloak: {KEYCLOAK_REALM}")
    print("=" * 60)

    # Obtenir le token Keycloak
    token = get_keycloak_token()
    if not token:
        print("[ERREUR] Impossible d'obtenir le token Keycloak")
        return

    # Récupérer les utilisateurs des deux côtés
    midpoint_users = get_midpoint_users()
    keycloak_users = get_keycloak_users(token)

    # Statistiques
    created = 0
    updated = 0
    skipped = 0

    # Traiter chaque utilisateur MidPoint
    for mp_user in midpoint_users:
        username = mp_user.get("name", "")
        oid = mp_user.get("oid", "")

        # Ignorer les utilisateurs système
        if username in ["administrator", "midpoint"]:
            skipped += 1
            continue

        # Récupérer les détails complets
        user_details = get_user_details(oid)
        if not user_details:
            continue

        # Préparer les données utilisateur
        user_data = {
            "username": username,
            "email": user_details.get("emailAddress", f"{username}@example.com"),
            "firstName": user_details.get("givenName", ""),
            "lastName": user_details.get("familyName", "")
        }

        # Vérifier si l'utilisateur existe dans Keycloak
        if username in keycloak_users:
            # Mettre à jour
            kc_user = keycloak_users[username]
            if update_keycloak_user(token, kc_user.get("id"), user_data):
                updated += 1
        else:
            # Créer
            if create_keycloak_user(token, user_data):
                created += 1

    print("\n" + "=" * 60)
    print("  RÉSUMÉ")
    print("=" * 60)
    print(f"  Utilisateurs créés: {created}")
    print(f"  Utilisateurs mis à jour: {updated}")
    print(f"  Utilisateurs ignorés: {skipped}")
    print("=" * 60)


def list_keycloak_users():
    """Liste les utilisateurs Keycloak"""
    print(f"\n[INFO] Utilisateurs dans Keycloak (realm: {KEYCLOAK_REALM}):")

    token = get_keycloak_token()
    if not token:
        return

    keycloak_users = get_keycloak_users(token)
    for username, user in keycloak_users.items():
        email = user.get("email", "no email")
        enabled = "enabled" if user.get("enabled") else "disabled"
        print(f"  - {username} ({email}) [{enabled}]")

    print(f"\n[OK] Total: {len(keycloak_users)} utilisateurs")


def provision_single_user(username):
    """Provisionne un utilisateur spécifique vers Keycloak"""
    print(f"\n[INFO] Provisioning de l'utilisateur: {username}")

    # Obtenir le token Keycloak
    token = get_keycloak_token()
    if not token:
        return False

    # Trouver l'utilisateur dans MidPoint
    midpoint_users = get_midpoint_users()
    mp_user = None
    for u in midpoint_users:
        if u.get("name") == username:
            mp_user = u
            break

    if not mp_user:
        print(f"[ERREUR] Utilisateur '{username}' non trouvé dans MidPoint")
        return False

    # Récupérer les détails
    user_details = get_user_details(mp_user.get("oid"))
    if not user_details:
        return False

    # Préparer les données
    user_data = {
        "username": username,
        "email": user_details.get("emailAddress", f"{username}@example.com"),
        "firstName": user_details.get("givenName", ""),
        "lastName": user_details.get("familyName", "")
    }

    # Créer dans Keycloak
    return create_keycloak_user(token, user_data)


def main():
    parser = argparse.ArgumentParser(description='Synchronisation MidPoint → Keycloak')
    parser.add_argument('--sync', action='store_true', help='Synchroniser tous les utilisateurs')
    parser.add_argument('--list', action='store_true', help='Lister les utilisateurs Keycloak')
    parser.add_argument('--user', type=str, help='Provisionner un utilisateur spécifique')
    args = parser.parse_args()

    if args.list:
        list_keycloak_users()
    elif args.user:
        provision_single_user(args.user)
    else:
        sync_users()


if __name__ == "__main__":
    main()
