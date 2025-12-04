#!/usr/bin/env python3
"""
Script pour changer le mot de passe administrateur de MidPoint
de 5ecr3t vers Nost1
"""
import asyncio
import httpx
import sys

MIDPOINT_URL = "http://localhost:8080/midpoint"
OLD_PASSWORD = "5ecr3t"
NEW_PASSWORD = "Nost1"
USERNAME = "administrator"


async def change_password():
    """Change le mot de passe administrateur MidPoint."""
    print("=" * 70)
    print("🔐 CHANGEMENT DU MOT DE PASSE MIDPOINT")
    print("=" * 70)
    print(f"\nURL: {MIDPOINT_URL}")
    print(f"User: {USERNAME}")
    print(f"Ancien mot de passe: {OLD_PASSWORD}")
    print(f"Nouveau mot de passe: {NEW_PASSWORD}\n")

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            auth=(USERNAME, OLD_PASSWORD)
        ) as client:
            # 1. Récupérer l'OID de l'utilisateur administrator
            print("1. Récupération de l'utilisateur administrator...")
            response = await client.get(
                f"{MIDPOINT_URL}/ws/rest/users",
                params={"query": f'name = "{USERNAME}"'}
            )

            if response.status_code != 200:
                print(f"   ❌ Erreur lors de la récupération: {response.status_code}")
                print(f"   Réponse: {response.text[:200]}")
                return False

            users_data = response.json()
            users = users_data.get("object", users_data.get("objects", []))

            if not users:
                print("   ❌ Utilisateur administrator non trouvé!")
                return False

            user_oid = users[0].get("oid")
            print(f"   ✅ Utilisateur trouvé (OID: {user_oid})")

            # 2. Modifier le mot de passe
            print(f"\n2. Changement du mot de passe vers '{NEW_PASSWORD}'...")

            # Modification via PATCH
            modification = {
                "objectModification": {
                    "@ns": "http://prism.evolveum.com/xml/ns/public/types-3",
                    "itemDelta": {
                        "modificationType": "replace",
                        "path": "credentials/password/value",
                        "value": {
                            "clearValue": NEW_PASSWORD
                        }
                    }
                }
            }

            response = await client.patch(
                f"{MIDPOINT_URL}/ws/rest/users/{user_oid}",
                json=modification,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 204, 250]:
                print(f"   ✅ Mot de passe changé avec succès!")

                # 3. Vérifier avec le nouveau mot de passe
                print(f"\n3. Vérification avec le nouveau mot de passe...")
                async with httpx.AsyncClient(
                    timeout=10.0,
                    auth=(USERNAME, NEW_PASSWORD)
                ) as new_client:
                    verify_response = await new_client.get(
                        f"{MIDPOINT_URL}/ws/rest/self"
                    )

                    if verify_response.status_code == 200:
                        print(f"   ✅ Vérification réussie!")
                        print("\n" + "=" * 70)
                        print("✅ MOT DE PASSE CHANGÉ AVEC SUCCÈS!")
                        print("=" * 70)
                        print(f"\nVous pouvez maintenant vous connecter avec:")
                        print(f"  Username: {USERNAME}")
                        print(f"  Password: {NEW_PASSWORD}\n")
                        return True
                    else:
                        print(f"   ❌ Vérification échouée: {verify_response.status_code}")
                        return False
            else:
                print(f"   ❌ Erreur lors du changement: {response.status_code}")
                print(f"   Réponse: {response.text[:500]}")
                return False

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(change_password())
    sys.exit(0 if result else 1)
