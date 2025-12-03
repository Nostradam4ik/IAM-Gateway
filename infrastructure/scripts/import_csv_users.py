#!/usr/bin/env python3
"""
Script d'import des utilisateurs CSV dans MidPoint via API REST

Ce script :
1. Lit le fichier CSV hr_sample.csv
2. Crée les utilisateurs dans MidPoint via l'API REST
3. Affiche le résultat de chaque opération

Usage:
    python3 import_csv_users.py

Prérequis:
    pip install requests
"""

import csv
import requests
import json
import sys
from typing import Dict, List

# Configuration MidPoint
MIDPOINT_URL = "http://localhost:8080/midpoint"
MIDPOINT_USER = "administrator"
MIDPOINT_PASSWORD = input("Enter MidPoint administrator password: ")

# Désactiver les avertissements SSL (pour dev uniquement)
requests.packages.urllib3.disable_warnings()

# Headers pour l'API REST
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def read_csv_file(csv_path: str) -> List[Dict[str, str]]:
    """Lit le fichier CSV et retourne une liste de dictionnaires"""
    users = []
    print(f"📖 Lecture du fichier CSV : {csv_path}")

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                users.append(row)
        print(f"✅ {len(users)} utilisateurs trouvés dans le CSV")
        return users
    except FileNotFoundError:
        print(f"❌ Erreur : Fichier {csv_path} non trouvé")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du CSV : {e}")
        sys.exit(1)

def create_user_object(csv_row: Dict[str, str]) -> Dict:
    """Crée l'objet JSON UserType pour MidPoint"""
    return {
        "@ns": "http://midpoint.evolveum.com/xml/ns/public/common/common-3",
        "user": {
            "name": csv_row['uid'],
            "givenName": csv_row['givenName'],
            "familyName": csv_row['familyName'],
            "fullName": f"{csv_row['givenName']} {csv_row['familyName']}",
            "emailAddress": csv_row['email'],
            "organizationalUnit": csv_row['department'],
            "activation": {
                "administrativeStatus": "enabled"
            }
        }
    }

def check_user_exists(username: str) -> bool:
    """Vérifie si un utilisateur existe déjà"""
    url = f"{MIDPOINT_URL}/ws/rest/users/{username}"

    try:
        response = requests.get(
            url,
            auth=(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers=HEADERS,
            verify=False
        )
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️  Erreur lors de la vérification de {username}: {e}")
        return False

def create_user_in_midpoint(user_data: Dict) -> bool:
    """Crée un utilisateur dans MidPoint via API REST"""
    username = user_data['user']['name']

    # Vérifier si l'utilisateur existe déjà
    if check_user_exists(username):
        print(f"⚠️  Utilisateur {username} existe déjà, ignoré")
        return True

    url = f"{MIDPOINT_URL}/ws/rest/users"

    try:
        print(f"🔄 Création de l'utilisateur {username}...")

        response = requests.post(
            url,
            auth=(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers=HEADERS,
            json=user_data,
            verify=False
        )

        if response.status_code in [200, 201]:
            print(f"✅ Utilisateur {username} créé avec succès !")
            return True
        else:
            print(f"❌ Erreur lors de la création de {username}")
            print(f"   Status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"❌ Exception lors de la création de {username}: {e}")
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🚀 Import des utilisateurs CSV dans MidPoint")
    print("=" * 60)
    print()

    # Chemin du CSV
    csv_path = "datasets/hr_sample.csv"

    # 1. Lire le CSV
    users = read_csv_file(csv_path)
    print()

    # 2. Tester la connexion à MidPoint
    print("🔌 Test de connexion à MidPoint...")
    test_url = f"{MIDPOINT_URL}/ws/rest/users/{MIDPOINT_USER}"
    try:
        response = requests.get(
            test_url,
            auth=(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers=HEADERS,
            verify=False
        )
        if response.status_code == 200:
            print("✅ Connexion à MidPoint OK")
        else:
            print(f"❌ Erreur de connexion : Status {response.status_code}")
            print("   Vérifiez le mot de passe administrator")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Impossible de se connecter à MidPoint : {e}")
        print("   Vérifiez que MidPoint est accessible sur http://localhost:8080")
        sys.exit(1)

    print()

    # 3. Créer chaque utilisateur
    print(f"👥 Création des {len(users)} utilisateurs...")
    print("-" * 60)

    success_count = 0
    failed_count = 0

    for csv_row in users:
        user_object = create_user_object(csv_row)
        if create_user_in_midpoint(user_object):
            success_count += 1
        else:
            failed_count += 1
        print()

    # 4. Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ")
    print("=" * 60)
    print(f"✅ Utilisateurs créés : {success_count}")
    print(f"❌ Échecs : {failed_count}")
    print()

    if success_count > 0:
        print("🎉 Import terminé avec succès !")
        print()
        print("📋 Prochaines étapes :")
        print("1. Vérifier dans MidPoint : Users → All users")
        print("2. Vous devriez voir : u1001, u1002, u1003")
        print()

    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Import annulé par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
