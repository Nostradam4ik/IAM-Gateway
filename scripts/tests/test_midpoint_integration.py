#!/usr/bin/env python3
"""
Script de test pour l'intégration MidPoint-Gateway
"""
import asyncio
import sys
import os

# Ajouter le chemin du Gateway
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gateway'))

from app.services.midpoint_client import MidPointClient
from app.core.config import settings


async def test_midpoint_connection():
    """Teste la connexion à MidPoint."""
    print("=" * 70)
    print("TEST D'INTÉGRATION MIDPOINT-GATEWAY")
    print("=" * 70)
    print()

    print(f"Configuration MidPoint:")
    print(f"  URL: {settings.MIDPOINT_URL}")
    print(f"  User: {settings.MIDPOINT_USER}")
    print(f"  Password: {'*' * len(settings.MIDPOINT_PASSWORD)}")
    print()

    client = MidPointClient()

    try:
        # Test 1: Connexion
        print("1. Test de connexion à MidPoint...")
        connected = await client.test_connection()

        if connected:
            print("   ✅ Connexion réussie!")
        else:
            print("   ❌ Échec de la connexion")
            print("   MidPoint n'est peut-être pas encore démarré.")
            print("   Attendez quelques minutes et réessayez.")
            return

        print()

        # Test 2: Récupérer les utilisateurs
        print("2. Récupération des utilisateurs MidPoint...")
        users = await client.get_all_accounts()
        print(f"   ✅ {len(users)} utilisateur(s) trouvé(s)")

        if users:
            print("\n   Utilisateurs:")
            for user in users[:5]:  # Afficher les 5 premiers
                print(f"     - {user.get('name')} ({user.get('fullName', 'N/A')})")

        print()

        # Test 3: Récupérer les rôles
        print("3. Récupération des rôles MidPoint...")
        roles = await client.get_roles()
        print(f"   ✅ {len(roles)} rôle(s) trouvé(s)")

        if roles:
            print("\n   Rôles:")
            for role in roles[:5]:  # Afficher les 5 premiers
                role_name = role.get('role', {}).get('name', 'N/A')
                print(f"     - {role_name}")

        print()
        print("=" * 70)
        print("✅ INTÉGRATION MIDPOINT-GATEWAY FONCTIONNELLE!")
        print("=" * 70)
        print()
        print("Prochaines étapes:")
        print("  1. Accédez à http://localhost:3000 (Gateway Frontend)")
        print("  2. Connectez-vous avec admin/admin123")
        print("  3. Créez des opérations de provisionnement")
        print("  4. Les utilisateurs seront créés dans MidPoint et propagés aux systèmes cibles")
        print()

    except Exception as e:
        print(f"   ❌ Erreur: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_midpoint_connection())
