#!/usr/bin/env python3
"""
Crée des opérations de provisioning et des logs d'audit pour la démo.
"""
import subprocess
import json
import random
from datetime import datetime, timedelta

# Get a fresh token
def get_token():
    result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "http://localhost:8000/api/v1/admin/token",
        "-H", "Content-Type: application/x-www-form-urlencoded",
        "-d", "username=admin&password=admin123"
    ], capture_output=True, text=True)
    return json.loads(result.stdout)["access_token"]


def create_provisioning_operations(token):
    """Crée plusieurs opérations de provisioning."""
    print("\n" + "="*70)
    print("   CRÉATION DES OPÉRATIONS DE PROVISIONING")
    print("="*70)

    users_to_provision = [
        {"firstname": "Alice", "lastname": "Wonderland", "department": "IT", "email": "alice.wonderland@demo.com"},
        {"firstname": "Bob", "lastname": "Builder", "department": "Operations", "email": "bob.builder@demo.com"},
        {"firstname": "Charlie", "lastname": "Chaplin", "department": "Marketing", "email": "charlie.chaplin@demo.com"},
        {"firstname": "Diana", "lastname": "Prince", "department": "Executive", "email": "diana.prince@demo.com"},
        {"firstname": "Edward", "lastname": "Norton", "department": "Finance", "email": "edward.norton@demo.com"},
        {"firstname": "Fiona", "lastname": "Apple", "department": "R&D", "email": "fiona.apple@demo.com"},
        {"firstname": "George", "lastname": "Lucas", "department": "IT", "email": "george.lucas@demo.com"},
        {"firstname": "Helen", "lastname": "Troy", "department": "HR", "email": "helen.troy@demo.com"},
        {"firstname": "Ivan", "lastname": "Terrible", "department": "Legal", "email": "ivan.terrible@demo.com"},
        {"firstname": "Julia", "lastname": "Roberts", "department": "Sales", "email": "julia.roberts@demo.com"},
    ]

    success = 0
    for i, user in enumerate(users_to_provision):
        payload = {
            "source_type": "HR",
            "target_systems": random.sample(["LDAP", "SQL", "Odoo"], k=random.randint(1, 3)),
            "user_data": {
                "employee_id": f"DEMO{i+100:03d}",
                "firstname": user["firstname"],
                "lastname": user["lastname"],
                "email": user["email"],
                "department": user["department"],
                "first_name": user["firstname"],
                "last_name": user["lastname"],
                "account_id": f"{user['firstname'].lower()}.{user['lastname'].lower()}"
            },
            "priority": random.choice(["normal", "high", "low"])
        }

        result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "http://localhost:8000/api/v1/provision/",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps(payload)
        ], capture_output=True, text=True)

        try:
            response = json.loads(result.stdout)
            if "error" not in result.stdout.lower():
                success += 1
                print(f"  ✓ {user['firstname']} {user['lastname']} - {payload['target_systems']}")
            else:
                print(f"  ✗ {user['firstname']} {user['lastname']} - Error")
        except:
            print(f"  ? {user['firstname']} {user['lastname']} - Unknown response")

    print(f"\n  Total: {success} opérations créées")
    return success


def verify_dashboard_data(token):
    """Vérifie les données du dashboard."""
    print("\n" + "="*70)
    print("   VÉRIFICATION DES DONNÉES DASHBOARD")
    print("="*70)

    # Get system status
    result = subprocess.run([
        "curl", "-s",
        "http://localhost:8000/api/v1/admin/status",
        "-H", f"Authorization: Bearer {token}"
    ], capture_output=True, text=True)

    try:
        status = json.loads(result.stdout)
        print(f"\n  📊 Status système:")
        print(f"     • Provisioning actif: {status.get('provisioning_enabled', 'N/A')}")
        print(f"     • Opérations aujourd'hui: {status.get('operations_today', 'N/A')}")
        print(f"     • Taux de succès: {status.get('success_rate', 'N/A')}%")
        print(f"     • Approbations en attente: {status.get('pending_approvals', 'N/A')}")
    except Exception as e:
        print(f"  ⚠ Impossible de récupérer le status: {e}")

    # Get connector status
    result = subprocess.run([
        "curl", "-s",
        "http://localhost:8000/api/v1/admin/connectors/status",
        "-H", f"Authorization: Bearer {token}"
    ], capture_output=True, text=True)

    try:
        connectors = json.loads(result.stdout)
        print(f"\n  🔌 Connecteurs:")
        for name, info in connectors.items():
            status_icon = "✅" if info.get("status") == "connected" else "❌"
            print(f"     {status_icon} {name.upper()}: {info.get('status', 'unknown')}")
    except Exception as e:
        print(f"  ⚠ Impossible de récupérer les connecteurs: {e}")

    # Get operations list
    result = subprocess.run([
        "curl", "-s",
        "http://localhost:8000/api/v1/provision/",
        "-H", f"Authorization: Bearer {token}"
    ], capture_output=True, text=True)

    try:
        operations = json.loads(result.stdout)
        if isinstance(operations, list):
            print(f"\n  📋 Opérations récentes: {len(operations)}")
            for op in operations[:5]:
                print(f"     • {op.get('account_id', 'N/A')} - {op.get('status', 'N/A')}")
    except:
        pass


def show_all_endpoints(token):
    """Liste toutes les fonctionnalités disponibles."""
    print("\n" + "="*70)
    print("   FONCTIONNALITÉS DISPONIBLES")
    print("="*70)

    features = [
        ("Dashboard", "http://localhost:3000", "Vue d'ensemble du système"),
        ("Opérations", "http://localhost:3000/operations", "Créer/gérer les provisionnements"),
        ("Réconciliation", "http://localhost:3000/reconciliation", "Synchroniser les systèmes"),
        ("Règles", "http://localhost:3000/rules", "Gérer les règles de calcul"),
        ("Workflows", "http://localhost:3000/workflows", "Approbations multi-niveaux"),
        ("Audit Logs", "http://localhost:3000/audit", "Historique des actions"),
        ("Assistant IA", "http://localhost:3000/ai", "Assistant intelligent"),
        ("Paramètres", "http://localhost:3000/settings", "Configuration système"),
    ]

    print(f"\n  🌐 Frontend (http://localhost:3000):")
    for name, url, desc in features:
        print(f"     • {name}: {desc}")

    print(f"\n  🔧 Backends:")
    print(f"     • API Gateway: http://localhost:8000/docs")
    print(f"     • MidPoint: http://localhost:8080/midpoint")
    print(f"     • phpLDAPadmin: http://localhost:8088")
    print(f"     • Odoo: http://localhost:8069")
    print(f"     • Keycloak: http://localhost:8081")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║          CRÉATION DES DONNÉES DE DÉMONSTRATION                       ║
╚══════════════════════════════════════════════════════════════════════╝
""")

    token = get_token()
    print(f"  ✓ Token obtenu")

    create_provisioning_operations(token)
    verify_dashboard_data(token)
    show_all_endpoints(token)

    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                    ✅ DONNÉES DE DÉMO PRÊTES                         ║
╚══════════════════════════════════════════════════════════════════════╝
""")
