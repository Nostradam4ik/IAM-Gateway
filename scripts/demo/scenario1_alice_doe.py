#!/usr/bin/env python3
"""
=============================================================================
SCÉNARIO 1 : Création et attribution des droits manuellement pour Alice Doe
=============================================================================

Ce script démontre le processus complet:
1. Création de l'employée Alice Doe dans Odoo (SI RH)
2. Import de l'identité vers MidPoint
3. Provisionnement LDAP avec les 4 groupes (Employee, Internet, Printer, SharePoint)
4. Provisionnement Odoo avec le rôle Odoo_User

Usage:
    python scenario1_alice_doe.py [--step N]

    --step 1 : Créer Alice dans Odoo uniquement
    --step 2 : Importer dans MidPoint
    --step 3 : Provisionner LDAP (attribuer le rôle Employee-Full-Access)
    --step 4 : Provisionner Odoo (attribuer le rôle Odoo_User)
    (sans argument : exécute toutes les étapes)
"""

import os
import sys
import json
import time
import argparse
import requests
from requests.auth import HTTPBasicAuth
import xmlrpc.client
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURATION
# =============================================================================

# Odoo
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'odoo')
ODOO_USER = os.getenv('ODOO_USER', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

# MidPoint
MIDPOINT_URL = os.getenv('MIDPOINT_URL', 'http://localhost:8080/midpoint')
MIDPOINT_USER = os.getenv('MIDPOINT_USER', 'administrator')
MIDPOINT_PASSWORD = os.getenv('MIDPOINT_PASSWORD', 'Test5ecr3t')

# OIDs des ressources et rôles
LDAP_RESOURCE_OID = "10000000-0000-0000-0000-000000000001"
ODOO_RESOURCE_OID = "10000000-0000-0000-0000-000000000002"
ROLE_EMPLOYEE_FULL_OID = "10000000-0000-0000-0000-000000000210"
ROLE_ODOO_USER_OID = "10000000-0000-0000-0000-000000000301"

# Données de l'employée Alice Doe
ALICE_DATA = {
    'firstname': 'Alice',
    'lastname': 'Doe',
    'email': 'alice.doe@example.com',
    'phone': '+33 1 23 45 67 89',
    'department': 'IT',
    'job_title': 'Software Developer',
    'start_date': datetime.now().strftime('%Y-%m-%d'),
}


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_step(step_num, description):
    print(f"\n{'─' * 70}")
    print(f"  ÉTAPE {step_num}: {description}")
    print(f"{'─' * 70}\n")


# =============================================================================
# ÉTAPE 1 : Création dans Odoo
# =============================================================================

def create_alice_in_odoo():
    """Créer l'employée Alice Doe dans Odoo avec son contrat"""
    print_step(1, "Création de l'employée dans Odoo (SI RH)")

    print(f"Connexion à Odoo: {ODOO_URL}")

    try:
        # Connexion XML-RPC
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

        if not uid:
            print("❌ Échec de l'authentification Odoo")
            return None

        print(f"✅ Connecté à Odoo (uid: {uid})")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')

        # Vérifier si Alice existe déjà
        existing = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.employee', 'search',
            [[('work_email', '=', ALICE_DATA['email'])]]
        )

        if existing:
            print(f"⚠️  Alice Doe existe déjà (ID: {existing[0]})")
            return existing[0]

        # Créer le département IT s'il n'existe pas
        dept_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.department', 'search',
            [[('name', '=', ALICE_DATA['department'])]]
        )

        if not dept_ids:
            dept_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'hr.department', 'create',
                [{'name': ALICE_DATA['department']}]
            )
            print(f"  → Département '{ALICE_DATA['department']}' créé (ID: {dept_id})")
        else:
            dept_id = dept_ids[0]

        # Créer le poste s'il n'existe pas
        job_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.job', 'search',
            [[('name', '=', ALICE_DATA['job_title'])]]
        )

        if not job_ids:
            job_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'hr.job', 'create',
                [{'name': ALICE_DATA['job_title']}]
            )
            print(f"  → Poste '{ALICE_DATA['job_title']}' créé (ID: {job_id})")
        else:
            job_id = job_ids[0]

        # Créer l'employée Alice
        employee_data = {
            'name': f"{ALICE_DATA['firstname']} {ALICE_DATA['lastname']}",
            'work_email': ALICE_DATA['email'],
            'work_phone': ALICE_DATA['phone'],
            'department_id': dept_id,
            'job_id': job_id,
        }

        employee_id = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'hr.employee', 'create',
            [employee_data]
        )

        print(f"\n✅ Employée créée dans Odoo:")
        print(f"   - ID: {employee_id}")
        print(f"   - Nom: {ALICE_DATA['firstname']} {ALICE_DATA['lastname']}")
        print(f"   - Email: {ALICE_DATA['email']}")
        print(f"   - Département: {ALICE_DATA['department']}")
        print(f"   - Poste: {ALICE_DATA['job_title']}")

        # Créer le contrat
        try:
            contract_data = {
                'name': f"Contrat - {ALICE_DATA['firstname']} {ALICE_DATA['lastname']}",
                'employee_id': employee_id,
                'date_start': ALICE_DATA['start_date'],
                'state': 'open',
                'wage': 3500,
            }

            contract_id = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'hr.contract', 'create',
                [contract_data]
            )
            print(f"\n✅ Contrat créé:")
            print(f"   - ID: {contract_id}")
            print(f"   - Date de début: {ALICE_DATA['start_date']}")
            print(f"   - Statut: Actif")
        except Exception as e:
            print(f"⚠️  Module hr_contract non disponible: {e}")

        return employee_id

    except Exception as e:
        print(f"❌ Erreur Odoo: {e}")
        return None


# =============================================================================
# ÉTAPE 2 : Import dans MidPoint
# =============================================================================

def create_alice_in_midpoint():
    """Créer l'identité Alice dans MidPoint"""
    print_step(2, "Import de l'identité dans MidPoint")

    print(f"Connexion à MidPoint: {MIDPOINT_URL}")

    # Générer l'OID pour Alice
    alice_oid = "10000000-1111-1111-1111-000000000001"

    # Vérifier si Alice existe déjà
    try:
        response = requests.get(
            f"{MIDPOINT_URL}/ws/rest/users/{alice_oid}",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Accept': 'application/json'},
            timeout=30
        )

        if response.status_code == 200:
            print(f"⚠️  Alice existe déjà dans MidPoint (OID: {alice_oid})")
            return alice_oid

    except Exception:
        pass

    # Rechercher par email
    search_query = f"""<?xml version="1.0" encoding="UTF-8"?>
<query xmlns="http://prism.evolveum.com/xml/ns/public/query-3">
    <filter>
        <equal>
            <path>emailAddress</path>
            <value>{ALICE_DATA['email']}</value>
        </equal>
    </filter>
</query>"""

    try:
        response = requests.post(
            f"{MIDPOINT_URL}/ws/rest/users/search",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml', 'Accept': 'application/json'},
            data=search_query,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            objects = data.get('object', {}).get('object', [])
            if objects:
                existing_oid = objects[0].get('oid')
                print(f"⚠️  Alice existe déjà (OID: {existing_oid})")
                return existing_oid

    except Exception:
        pass

    # Créer Alice dans MidPoint
    user_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<user xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      oid="{alice_oid}">
    <name>alice.doe</name>
    <fullName>{ALICE_DATA['firstname']} {ALICE_DATA['lastname']}</fullName>
    <givenName>{ALICE_DATA['firstname']}</givenName>
    <familyName>{ALICE_DATA['lastname']}</familyName>
    <emailAddress>{ALICE_DATA['email']}</emailAddress>
    <telephoneNumber>{ALICE_DATA['phone']}</telephoneNumber>
    <title>{ALICE_DATA['job_title']}</title>
    <organizationalUnit>{ALICE_DATA['department']}</organizationalUnit>

    <activation>
        <administrativeStatus>enabled</administrativeStatus>
        <validFrom>{ALICE_DATA['start_date']}T00:00:00Z</validFrom>
    </activation>

    <credentials>
        <password>
            <value>
                <clearValue>Welcome123!</clearValue>
            </value>
        </password>
    </credentials>
</user>"""

    try:
        response = requests.post(
            f"{MIDPOINT_URL}/ws/rest/users",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=user_xml,
            timeout=30
        )

        if response.status_code in [200, 201, 202]:
            print(f"\n✅ Identité créée dans MidPoint:")
            print(f"   - OID: {alice_oid}")
            print(f"   - Login: alice.doe")
            print(f"   - Nom: {ALICE_DATA['firstname']} {ALICE_DATA['lastname']}")
            print(f"   - Email: {ALICE_DATA['email']}")
            print(f"   - Cycle de vie: ACTIVE")
            return alice_oid
        else:
            print(f"❌ Erreur création: {response.status_code}")
            print(response.text[:500])
            return None

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None


# =============================================================================
# ÉTAPE 3 : Provisionnement LDAP
# =============================================================================

def provision_ldap_access(user_oid):
    """Attribuer le rôle Employee-Full-Access pour provisionner LDAP"""
    print_step(3, "Provisionnement LDAP (4 groupes)")

    print("Attribution du rôle 'Employee-Full-Access'...")
    print("Ce rôle provisionne automatiquement:")
    print("  • Groupe Employee")
    print("  • Groupe Internet")
    print("  • Groupe Printer (Imprimantes)")
    print("  • Groupe Public_Share_Folder_SharePoint")

    # D'abord, créer le rôle s'il n'existe pas
    role_xml = """<?xml version="1.0" encoding="UTF-8"?>
<role xmlns="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
      xmlns:q="http://prism.evolveum.com/xml/ns/public/query-3"
      xmlns:ri="http://midpoint.evolveum.com/xml/ns/public/resource/instance-3"
      oid="10000000-0000-0000-0000-000000000210">
    <name>Employee-Full-Access</name>
    <displayName>Employe - Acces Complet LDAP</displayName>
    <description>Attribue un compte LDAP avec les groupes Employee, Internet, Printer et Public_Share_Folder_SharePoint</description>
    <requestable>true</requestable>
    <riskLevel>low</riskLevel>
    <inducement>
        <construction>
            <resourceRef oid="10000000-0000-0000-0000-000000000001" type="ResourceType"/>
            <kind>account</kind>
            <intent>default</intent>
            <association>
                <ref>ri:ldapGroup</ref>
                <outbound>
                    <expression>
                        <associationTargetSearch>
                            <filter><q:equal><q:path>attributes/ri:cn</q:path><q:value>Employee</q:value></q:equal></filter>
                            <searchStrategy>onResource</searchStrategy>
                        </associationTargetSearch>
                    </expression>
                </outbound>
            </association>
            <association>
                <ref>ri:ldapGroup</ref>
                <outbound>
                    <expression>
                        <associationTargetSearch>
                            <filter><q:equal><q:path>attributes/ri:cn</q:path><q:value>Internet</q:value></q:equal></filter>
                            <searchStrategy>onResource</searchStrategy>
                        </associationTargetSearch>
                    </expression>
                </outbound>
            </association>
            <association>
                <ref>ri:ldapGroup</ref>
                <outbound>
                    <expression>
                        <associationTargetSearch>
                            <filter><q:equal><q:path>attributes/ri:cn</q:path><q:value>Printer</q:value></q:equal></filter>
                            <searchStrategy>onResource</searchStrategy>
                        </associationTargetSearch>
                    </expression>
                </outbound>
            </association>
            <association>
                <ref>ri:ldapGroup</ref>
                <outbound>
                    <expression>
                        <associationTargetSearch>
                            <filter><q:equal><q:path>attributes/ri:cn</q:path><q:value>Public_Share_Folder_SharePoint</q:value></q:equal></filter>
                            <searchStrategy>onResource</searchStrategy>
                        </associationTargetSearch>
                    </expression>
                </outbound>
            </association>
        </construction>
    </inducement>
</role>"""

    # Créer/mettre à jour le rôle
    try:
        response = requests.put(
            f"{MIDPOINT_URL}/ws/rest/roles/{ROLE_EMPLOYEE_FULL_OID}",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=role_xml,
            timeout=30
        )
        if response.status_code in [200, 201, 204]:
            print("✅ Rôle 'Employee-Full-Access' configuré")
    except Exception as e:
        print(f"⚠️  Rôle: {e}")

    # Attribuer le rôle à Alice
    assign_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<objectModification xmlns="http://midpoint.evolveum.com/xml/ns/public/common/api-types-3"
                    xmlns:c="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
                    xmlns:t="http://prism.evolveum.com/xml/ns/public/types-3">
    <itemDelta>
        <t:modificationType>add</t:modificationType>
        <t:path>c:assignment</t:path>
        <t:value>
            <c:targetRef oid="{ROLE_EMPLOYEE_FULL_OID}" type="c:RoleType"/>
        </t:value>
    </itemDelta>
</objectModification>"""

    try:
        response = requests.patch(
            f"{MIDPOINT_URL}/ws/rest/users/{user_oid}",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=assign_xml,
            timeout=60
        )

        if response.status_code in [200, 204]:
            print(f"\n✅ Rôle 'Employee-Full-Access' attribué à Alice")
            print("\n📋 Résultat attendu dans LDAP:")
            print(f"   - DN: uid=alice.doe,ou=users,dc=example,dc=com")
            print(f"   - Membre de: cn=Employee,ou=groups,dc=example,dc=com")
            print(f"   - Membre de: cn=Internet,ou=groups,dc=example,dc=com")
            print(f"   - Membre de: cn=Printer,ou=groups,dc=example,dc=com")
            print(f"   - Membre de: cn=Public_Share_Folder_SharePoint,ou=groups,dc=example,dc=com")
            return True
        else:
            print(f"❌ Erreur attribution: {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


# =============================================================================
# ÉTAPE 4 : Provisionnement Odoo
# =============================================================================

def provision_odoo_access(user_oid):
    """Attribuer le rôle Odoo_User"""
    print_step(4, "Provisionnement Odoo (rôle Odoo_User)")

    print("Attribution du rôle 'Odoo_User'...")

    # Attribuer le rôle Odoo_User
    assign_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<objectModification xmlns="http://midpoint.evolveum.com/xml/ns/public/common/api-types-3"
                    xmlns:c="http://midpoint.evolveum.com/xml/ns/public/common/common-3"
                    xmlns:t="http://prism.evolveum.com/xml/ns/public/types-3">
    <itemDelta>
        <t:modificationType>add</t:modificationType>
        <t:path>c:assignment</t:path>
        <t:value>
            <c:targetRef oid="{ROLE_ODOO_USER_OID}" type="c:RoleType"/>
        </t:value>
    </itemDelta>
</objectModification>"""

    try:
        response = requests.patch(
            f"{MIDPOINT_URL}/ws/rest/users/{user_oid}",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Content-Type': 'application/xml'},
            data=assign_xml,
            timeout=60
        )

        if response.status_code in [200, 204]:
            print(f"\n✅ Rôle 'Odoo_User' attribué à Alice")
            print("\n📋 Résultat attendu dans Odoo:")
            print(f"   - Contact créé: Alice Doe")
            print(f"   - Email: {ALICE_DATA['email']}")
            print(f"   - Type: Employee")
            print(f"   - Droits: User")
            return True
        else:
            print(f"❌ Erreur attribution: {response.status_code}")
            print(response.text[:500])
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False


# =============================================================================
# VÉRIFICATION FINALE
# =============================================================================

def verify_provisioning(user_oid):
    """Vérifier le provisionnement"""
    print_header("VÉRIFICATION DU PROVISIONNEMENT")

    # Récupérer l'utilisateur MidPoint avec ses projections
    try:
        response = requests.get(
            f"{MIDPOINT_URL}/ws/rest/users/{user_oid}",
            auth=HTTPBasicAuth(MIDPOINT_USER, MIDPOINT_PASSWORD),
            headers={'Accept': 'application/json'},
            params={'options': 'raw'},
            timeout=30
        )

        if response.status_code == 200:
            print("\n✅ Utilisateur MidPoint:")
            data = response.json()
            user = data.get('user', data)
            print(f"   - Nom: {user.get('fullName', {}).get('orig', 'N/A')}")
            print(f"   - Email: {user.get('emailAddress', 'N/A')}")

            # Compter les assignments
            assignments = user.get('assignment', [])
            if not isinstance(assignments, list):
                assignments = [assignments]
            print(f"   - Rôles attribués: {len(assignments)}")

    except Exception as e:
        print(f"⚠️  Vérification MidPoint: {e}")

    print("\n📌 Pour vérifier manuellement:")
    print("   1. LDAP (phpLDAPadmin): http://localhost:8081")
    print("      → Chercher: uid=alice.doe,ou=users,dc=example,dc=com")
    print("      → Vérifier l'appartenance aux 4 groupes")
    print("")
    print("   2. Odoo: http://localhost:8069")
    print("      → Contacts → Rechercher 'Alice Doe'")
    print("")
    print("   3. MidPoint: http://localhost:8080/midpoint")
    print("      → Users → alice.doe → Projections")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Scénario 1: Création et attribution des droits pour Alice Doe'
    )
    parser.add_argument('--step', type=int, choices=[1, 2, 3, 4],
                        help='Exécuter une étape spécifique (1-4)')
    args = parser.parse_args()

    print_header("SCÉNARIO 1: CRÉATION ET ATTRIBUTION DES DROITS")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Employée: {ALICE_DATA['firstname']} {ALICE_DATA['lastname']}")
    print(f"  Email: {ALICE_DATA['email']}")

    user_oid = "10000000-1111-1111-1111-000000000001"

    if args.step == 1 or args.step is None:
        create_alice_in_odoo()

    if args.step == 2 or args.step is None:
        result = create_alice_in_midpoint()
        if result:
            user_oid = result

    if args.step == 3 or args.step is None:
        provision_ldap_access(user_oid)

    if args.step == 4 or args.step is None:
        provision_odoo_access(user_oid)

    if args.step is None:
        time.sleep(2)  # Attendre la propagation
        verify_provisioning(user_oid)

    print_header("SCÉNARIO 1 TERMINÉ")
    print("\n💡 Prochaines étapes pour la démonstration vidéo:")
    print("   1. Montrer Alice dans Odoo (SI RH)")
    print("   2. Montrer Alice dans MidPoint (identité importée)")
    print("   3. Montrer le compte LDAP dans phpLDAPadmin")
    print("   4. Montrer l'appartenance aux 4 groupes LDAP")
    print("   5. Montrer le contact Odoo créé")


if __name__ == '__main__':
    main()
