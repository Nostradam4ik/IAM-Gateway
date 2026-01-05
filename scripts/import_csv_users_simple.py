#!/usr/bin/env python3
"""
Script d'import des utilisateurs CSV dans MidPoint via API REST
VERSION SIMPLIFIÉE - Sans dépendances externes

Ce script utilise uniquement les bibliothèques standard Python (urllib)

Usage:
    python3 import_csv_users_simple.py [mot_de_passe_admin]
"""

import csv
import json
import sys
import urllib.request
import urllib.error
import base64
import ssl

# Configuration MidPoint
MIDPOINT_URL = "http://localhost:8080/midpoint"
MIDPOINT_USER = "administrator"

def get_password():
    """Récupère le mot de passe (argument ou saisie)"""
    if len(sys.argv) > 1:
        return sys.argv[1]
    else:
        import getpass
        return getpass.getpass("Enter MidPoint administrator password: ")

def read_csv_file(csv_path):
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

def make_request(url, method="GET", data=None, auth=None):
    """Fait une requête HTTP avec urllib"""
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Ajouter l'authentification Basic
    if auth:
        credentials = f"{auth[0]}:{auth[1]}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        headers["Authorization"] = f"Basic {encoded_credentials}"

    # Préparer les données
    if data:
        data = json.dumps(data).encode('utf-8')

    # Créer la requête
    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    # Désactiver la vérification SSL (pour dev uniquement)
    context = ssl._create_unverified_context()

    try:
        with urllib.request.urlopen(req, context=context) as response:
            body = response.read().decode('utf-8')
            return response.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8') if e.fp else str(e)
    except Exception as e:
        raise Exception(f"Erreur de connexion : {e}")

def create_user_object(csv_row):
    """Crée l'objet JSON UserType pour MidPoint"""
    return {
        "user": {
            "@ns": "http://midpoint.evolveum.com/xml/ns/public/common/common-3",
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

def check_user_exists(username, password):
    """Vérifie si un utilisateur existe déjà"""
    url = f"{MIDPOINT_URL}/ws/rest/users/{username}"

    try:
        status, _ = make_request(url, auth=(MIDPOINT_USER, password))
        return status == 200
    except Exception:
        return False

def create_user_in_midpoint(user_data, password):
    """Crée un utilisateur dans MidPoint via API REST"""
    username = user_data['user']['name']

    # Vérifier si l'utilisateur existe déjà
    if check_user_exists(username, password):
        print(f"⚠️  Utilisateur {username} existe déjà, ignoré")
        return True

    url = f"{MIDPOINT_URL}/ws/rest/users"

    try:
        print(f"🔄 Création de l'utilisateur {username}...")

        status, response_body = make_request(
            url,
            method="POST",
            data=user_data,
            auth=(MIDPOINT_USER, password)
        )

        if status in [200, 201]:
            print(f"✅ Utilisateur {username} créé avec succès !")
            return True
        else:
            print(f"❌ Erreur lors de la création de {username}")
            print(f"   Status code: {status}")
            print(f"   Response: {response_body[:200]}")
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

    # Récupérer le mot de passe
    password = get_password()

    # Chemin du CSV
    csv_path = "datasets/hr_sample.csv"

    # 1. Lire le CSV
    users = read_csv_file(csv_path)
    print()

    # 2. Tester la connexion à MidPoint
    print("🔌 Test de connexion à MidPoint...")
    test_url = f"{MIDPOINT_URL}/ws/rest/users"
    try:
        status, _ = make_request(test_url, auth=(MIDPOINT_USER, password))
        if status == 200:
            print("✅ Connexion à MidPoint OK")
        else:
            print(f"❌ Erreur de connexion : Status {status}")
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
        if create_user_in_midpoint(user_object, password):
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
