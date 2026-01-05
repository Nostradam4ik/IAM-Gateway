#!/usr/bin/env python3
"""
Setup Odoo with demo users and contacts for reconciliation.
Uses only core Odoo modules (res.users, res.partner).
"""

import xmlrpc.client
import random

# Odoo connection settings
ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_USER = "admin"
ODOO_PASSWORD = "admin"

# Demo users to create (matching LDAP/SQL users for reconciliation testing)
DEMO_USERS = [
    # IT Department
    {"firstname": "Jean", "lastname": "Dupont", "department": "IT"},
    {"firstname": "Sophie", "lastname": "Petit", "department": "IT"},
    {"firstname": "Hugo", "lastname": "Durand", "department": "IT"},
    {"firstname": "Antoine", "lastname": "Girard", "department": "IT"},
    {"firstname": "Julie", "lastname": "Moreau", "department": "IT"},

    # HR Department
    {"firstname": "Marie", "lastname": "Martin", "department": "HR"},
    {"firstname": "Lea", "lastname": "Leroy", "department": "HR"},
    {"firstname": "Claire", "lastname": "Bonnet", "department": "HR"},
    {"firstname": "Nathalie", "lastname": "Fournier", "department": "HR"},

    # Finance Department
    {"firstname": "Pierre", "lastname": "Bernard", "department": "Finance"},
    {"firstname": "Thomas", "lastname": "Moreau", "department": "Finance"},
    {"firstname": "Philippe", "lastname": "Mercier", "department": "Finance"},
    {"firstname": "Christine", "lastname": "Roux", "department": "Finance"},

    # Sales Department
    {"firstname": "Lucas", "lastname": "Robert", "department": "Sales"},
    {"firstname": "Maxime", "lastname": "Faure", "department": "Sales"},
    {"firstname": "Alexandre", "lastname": "Laurent", "department": "Sales"},
    {"firstname": "Benjamin", "lastname": "Clement", "department": "Sales"},

    # Marketing Department
    {"firstname": "Emma", "lastname": "Richard", "department": "Marketing"},
    {"firstname": "Charlotte", "lastname": "Morel", "department": "Marketing"},
    {"firstname": "Pauline", "lastname": "Blanc", "department": "Marketing"},
    {"firstname": "Aurelie", "lastname": "Garcia", "department": "Marketing"},

    # R&D Department
    {"firstname": "Camille", "lastname": "Simon", "department": "R&D"},
    {"firstname": "Nicolas", "lastname": "Leroux", "department": "R&D"},
    {"firstname": "Sebastien", "lastname": "Morin", "department": "R&D"},
    {"firstname": "Vincent", "lastname": "Gauthier", "department": "R&D"},

    # Operations Department
    {"firstname": "Guillaume", "lastname": "Andre", "department": "Operations"},
    {"firstname": "Olivier", "lastname": "Lefevre", "department": "Operations"},
    {"firstname": "Francois", "lastname": "Muller", "department": "Operations"},

    # Legal Department
    {"firstname": "Isabelle", "lastname": "Petit", "department": "Legal"},
    {"firstname": "Stephanie", "lastname": "Rousseau", "department": "Legal"},
]


def authenticate_odoo():
    """Authenticate with Odoo."""
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')

    # Check version
    version = common.version()
    print(f"Connected to Odoo {version.get('server_version')}")

    # Authenticate
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
    if not uid:
        raise Exception("Authentication failed")

    print(f"Authenticated as UID: {uid}")
    return uid


def get_models():
    """Get Odoo models proxy."""
    return xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')


def execute(uid, model, method, *args, **kwargs):
    """Execute Odoo RPC call."""
    models = get_models()
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        model, method, list(args), kwargs
    )


def create_contact_and_user(uid, user_data):
    """Create partner/contact and optionally user."""
    firstname = user_data['firstname']
    lastname = user_data['lastname']
    name = f"{firstname} {lastname}"
    login = f"{firstname.lower()}.{lastname.lower()}@example.com"
    department = user_data.get('department', '')

    # Check if partner already exists
    existing = execute(uid, 'res.partner', 'search', [('email', '=', login)])
    if existing:
        print(f"  Contact {login} already exists")
        return existing[0], None

    # Create partner (contact)
    partner_id = execute(uid, 'res.partner', 'create', [{
        'name': name,
        'email': login,
        'is_company': False,
        'phone': f"+33 6 {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}",
        'city': random.choice(['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes']),
        'comment': f"Department: {department}",
        'function': random.choice(['Manager', 'Engineer', 'Analyst', 'Specialist', 'Coordinator'])
    }])

    print(f"  Created contact: {name} ({department})")

    # Try to create user (may fail due to license)
    user_id = None
    try:
        user_id = execute(uid, 'res.users', 'create', [{
            'name': name,
            'login': login,
            'partner_id': partner_id,
            'active': True
        }])
        print(f"    + Created user: {login}")
    except Exception as e:
        # Likely license limit
        if "license" in str(e).lower() or "limit" in str(e).lower():
            print(f"    - User creation skipped (license limit)")
        else:
            print(f"    - Could not create user: {str(e)[:40]}...")

    return partner_id, user_id


def create_extra_contacts(uid, count=30):
    """Create additional contacts for reconciliation variety."""
    print(f"\nCreating {count} additional contacts...")

    firstnames = ["Marc", "Anne", "Paul", "Sarah", "Michel", "Celine", "David", "Laura",
                  "Eric", "Marion", "Jerome", "Helene", "Patrick", "Valerie", "Yves",
                  "Alain", "Sandrine", "Bruno", "Delphine", "Frederic"]
    lastnames = ["Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy",
                 "Moreau", "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "David",
                 "Bertrand", "Roux", "Vincent", "Fournier", "Morel", "Girard"]

    created = 0
    for i in range(count):
        firstname = random.choice(firstnames)
        lastname = random.choice(lastnames)
        name = f"{firstname} {lastname}"
        email = f"{firstname.lower()}.{lastname.lower()}{i}@example.com"

        # Check if exists
        existing = execute(uid, 'res.partner', 'search', [('email', '=', email)])
        if existing:
            continue

        # Create contact
        execute(uid, 'res.partner', 'create', [{
            'name': name,
            'email': email,
            'is_company': False,
            'phone': f"+33 6 {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}",
            'city': random.choice(['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nice', 'Nantes', 'Bordeaux', 'Lille']),
            'function': random.choice(['Manager', 'Engineer', 'Analyst', 'Specialist', 'Coordinator', 'Director', 'Assistant'])
        }])
        created += 1

    print(f"  Created {created} additional contacts")


def create_companies(uid, count=5):
    """Create company contacts for variety."""
    print(f"\nCreating {count} company contacts...")

    companies = [
        {"name": "TechCorp France", "city": "Paris"},
        {"name": "Innovation Labs", "city": "Lyon"},
        {"name": "Digital Solutions SA", "city": "Toulouse"},
        {"name": "CloudFirst SARL", "city": "Nantes"},
        {"name": "DataDriven SAS", "city": "Bordeaux"},
    ]

    created = 0
    for company in companies[:count]:
        existing = execute(uid, 'res.partner', 'search', [('name', '=', company['name'])])
        if existing:
            continue

        execute(uid, 'res.partner', 'create', [{
            'name': company['name'],
            'is_company': True,
            'city': company['city'],
            'email': f"contact@{company['name'].lower().replace(' ', '')}.com",
            'phone': f"+33 1 {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)} {random.randint(10, 99)}"
        }])
        created += 1
        print(f"  Created company: {company['name']}")

    print(f"  Created {created} companies")


def main():
    print("=" * 60)
    print("ODOO DEMO SETUP (Contacts & Users)")
    print("=" * 60)

    # Authenticate
    uid = authenticate_odoo()

    # Create main demo users/contacts
    print("\nCreating demo contacts and users...")
    for user_data in DEMO_USERS:
        create_contact_and_user(uid, user_data)

    # Create additional contacts
    create_extra_contacts(uid, 30)

    # Create companies
    create_companies(uid, 5)

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    # Count totals
    users = execute(uid, 'res.users', 'search_count', [[('active', '=', True)]])
    active_users = execute(uid, 'res.users', 'search_count', [[('active', '=', True), ('share', '=', False)]])
    partners = execute(uid, 'res.partner', 'search_count', [[('is_company', '=', False)]])
    companies = execute(uid, 'res.partner', 'search_count', [[('is_company', '=', True)]])

    print(f"  Internal Users:  {active_users}")
    print(f"  Total Users:     {users}")
    print(f"  Contacts:        {partners}")
    print(f"  Companies:       {companies}")

    # List all users
    print("\n  Odoo Users:")
    all_users = execute(uid, 'res.users', 'search_read',
                        [[('active', '=', True)]],
                        fields=['id', 'name', 'login'])
    for u in all_users[:20]:  # Limit display
        print(f"    - {u['name']} ({u['login']})")
    if len(all_users) > 20:
        print(f"    ... and {len(all_users) - 20} more")

    print("\nOdoo setup complete!")


if __name__ == "__main__":
    main()
