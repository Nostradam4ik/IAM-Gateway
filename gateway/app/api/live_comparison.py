"""
API de comparaison en temps reel entre systemes.
Fonctionnalite innovante pour visualiser l'etat de synchronisation.
Inclut LiveSync Odoo -> MidPoint.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import structlog
import asyncio

from app.core.security import get_current_user, require_role
from app.core.database import get_session
from app.connectors.ldap_connector import LDAPConnector
from app.connectors.sql_connector import SQLConnector
from app.connectors.odoo_connector import OdooConnector
from app.services.midpoint_client import MidPointClient
from app.services.workflow_service import WorkflowService
import uuid

router = APIRouter()
logger = structlog.get_logger()


class SystemStats(BaseModel):
    """Statistiques d'un systeme."""
    name: str
    total_users: int
    active_users: int
    status: str
    last_check: str
    sample_users: List[Dict[str, Any]]


class ComparisonResult(BaseModel):
    """Resultat de comparaison entre systemes."""
    timestamp: str
    systems: List[SystemStats]
    cross_system_stats: Dict[str, Any]
    common_users: List[str]
    discrepancies: List[Dict[str, Any]]


class UserCrossReference(BaseModel):
    """Reference croisee d'un utilisateur."""
    identifier: str
    ldap: Optional[Dict[str, Any]] = None
    sql: Optional[Dict[str, Any]] = None
    odoo: Optional[Dict[str, Any]] = None
    sync_status: str


@router.get("/stats", response_model=Dict[str, Any])
async def get_live_stats(
    current_user: dict = Depends(get_current_user)
):
    """
    Recupere les statistiques en temps reel de tous les systemes.
    C'est un snapshot instantane de l'etat des bases.
    """
    stats = {
        "timestamp": datetime.utcnow().isoformat(),
        "systems": {},
        "total_identities": 0
    }

    # LDAP Stats
    try:
        ldap = LDAPConnector()
        if await ldap.test_connection():
            ldap_users = await ldap.list_accounts()
            stats["systems"]["LDAP"] = {
                "status": "connected",
                "total_users": len(ldap_users),
                "sample": [{"uid": u.get("uid"), "cn": u.get("cn"), "mail": u.get("mail")}
                          for u in ldap_users[:5]]
            }
            stats["total_identities"] += len(ldap_users)
        else:
            stats["systems"]["LDAP"] = {"status": "disconnected", "total_users": 0}
    except Exception as e:
        stats["systems"]["LDAP"] = {"status": "error", "error": str(e)[:100]}

    # SQL Stats
    try:
        sql = SQLConnector()
        if await sql.test_connection():
            sql_users = await sql.list_accounts()
            stats["systems"]["SQL"] = {
                "status": "connected",
                "total_users": len(sql_users),
                "sample": [{"username": u.get("username"), "email": u.get("email"),
                           "department": u.get("department")} for u in sql_users[:5]]
            }
            stats["total_identities"] += len(sql_users)
        else:
            stats["systems"]["SQL"] = {"status": "disconnected", "total_users": 0}
    except Exception as e:
        stats["systems"]["SQL"] = {"status": "error", "error": str(e)[:100]}

    # Odoo Stats
    try:
        odoo = OdooConnector()
        if await odoo.test_connection():
            odoo_users = await odoo.list_accounts()
            stats["systems"]["Odoo"] = {
                "status": "connected",
                "total_users": len(odoo_users),
                "sample": [{"id": u.get("id"), "name": u.get("name"), "login": u.get("login")}
                          for u in odoo_users[:5]]
            }
            stats["total_identities"] += len(odoo_users)
        else:
            stats["systems"]["Odoo"] = {"status": "disconnected", "total_users": 0}
    except Exception as e:
        stats["systems"]["Odoo"] = {"status": "error", "error": str(e)[:100]}

    return stats


@router.get("/compare", response_model=Dict[str, Any])
async def compare_systems(
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Compare en temps reel les utilisateurs entre tous les systemes.
    Detecte les divergences et les utilisateurs manquants.
    """
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "comparison": {},
        "discrepancies": [],
        "summary": {}
    }

    # Fetch all users from all systems
    ldap_users = {}
    sql_users = {}
    odoo_users = {}

    # LDAP
    try:
        ldap = LDAPConnector()
        ldap_list = await ldap.list_accounts()
        for u in ldap_list:
            email = u.get("mail", "").lower() if u.get("mail") else None
            uid = u.get("uid", "").lower() if u.get("uid") else None
            key = email or uid
            if key:
                ldap_users[key] = {
                    "uid": u.get("uid"),
                    "cn": u.get("cn"),
                    "mail": u.get("mail"),
                    "source": "LDAP"
                }
    except Exception as e:
        logger.error("LDAP fetch failed", error=str(e))

    # SQL
    try:
        sql = SQLConnector()
        sql_list = await sql.list_accounts()
        for u in sql_list:
            email = u.get("email", "").lower() if u.get("email") else None
            username = u.get("username", "").lower() if u.get("username") else None
            key = email or username
            if key:
                sql_users[key] = {
                    "username": u.get("username"),
                    "email": u.get("email"),
                    "department": u.get("department"),
                    "source": "SQL"
                }
    except Exception as e:
        logger.error("SQL fetch failed", error=str(e))

    # Odoo
    try:
        odoo = OdooConnector()
        odoo_list = await odoo.list_accounts()
        for u in odoo_list:
            login = u.get("login", "").lower() if u.get("login") else None
            name = u.get("name", "").lower().replace(" ", ".") if u.get("name") else None
            key = login or name
            if key:
                odoo_users[key] = {
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "login": u.get("login"),
                    "active": u.get("active"),
                    "source": "Odoo"
                }
    except Exception as e:
        logger.error("Odoo fetch failed", error=str(e))

    # Find common identifiers (by email pattern)
    all_keys = set(ldap_users.keys()) | set(sql_users.keys()) | set(odoo_users.keys())

    cross_reference = []
    in_all_systems = []
    missing_somewhere = []

    for key in sorted(all_keys):
        ref = {
            "identifier": key,
            "in_ldap": key in ldap_users,
            "in_sql": key in sql_users,
            "in_odoo": key in odoo_users,
            "ldap_data": ldap_users.get(key),
            "sql_data": sql_users.get(key),
            "odoo_data": odoo_users.get(key)
        }

        # Determine sync status
        present_count = sum([ref["in_ldap"], ref["in_sql"], ref["in_odoo"]])
        if present_count == 3:
            ref["sync_status"] = "synced"
            in_all_systems.append(key)
        elif present_count == 2:
            ref["sync_status"] = "partial"
            missing_in = []
            if not ref["in_ldap"]:
                missing_in.append("LDAP")
            if not ref["in_sql"]:
                missing_in.append("SQL")
            if not ref["in_odoo"]:
                missing_in.append("Odoo")
            ref["missing_in"] = missing_in
            missing_somewhere.append(ref)
        else:
            ref["sync_status"] = "isolated"
            ref["only_in"] = []
            if ref["in_ldap"]:
                ref["only_in"].append("LDAP")
            if ref["in_sql"]:
                ref["only_in"].append("SQL")
            if ref["in_odoo"]:
                ref["only_in"].append("Odoo")

        cross_reference.append(ref)

    # Build result
    result["comparison"] = {
        "ldap_count": len(ldap_users),
        "sql_count": len(sql_users),
        "odoo_count": len(odoo_users),
        "total_unique_identities": len(all_keys)
    }

    result["cross_reference"] = cross_reference[:50]  # Limit for response size

    result["summary"] = {
        "fully_synced": len(in_all_systems),
        "partially_synced": len([r for r in cross_reference if r["sync_status"] == "partial"]),
        "isolated": len([r for r in cross_reference if r["sync_status"] == "isolated"]),
        "sync_rate": f"{(len(in_all_systems) / max(len(all_keys), 1)) * 100:.1f}%"
    }

    # Discrepancies for action
    result["discrepancies"] = missing_somewhere[:20]

    return result


@router.get("/user/{identifier}", response_model=Dict[str, Any])
async def get_user_cross_reference(
    identifier: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Recherche un utilisateur dans tous les systemes par son identifiant.
    Retourne toutes les donnees trouvees pour cet utilisateur.
    """
    result = {
        "identifier": identifier,
        "timestamp": datetime.utcnow().isoformat(),
        "found_in": [],
        "data": {}
    }

    search_terms = [identifier.lower()]
    if "@" not in identifier:
        search_terms.append(f"{identifier}@example.com")

    # Search LDAP
    try:
        ldap = LDAPConnector()
        for term in search_terms:
            user = await ldap.get_account(term)
            if user:
                result["found_in"].append("LDAP")
                result["data"]["ldap"] = user
                break
    except Exception as e:
        result["data"]["ldap_error"] = str(e)[:100]

    # Search SQL
    try:
        sql = SQLConnector()
        for term in search_terms:
            user = await sql.get_account(term)
            if user:
                result["found_in"].append("SQL")
                result["data"]["sql"] = user
                break
    except Exception as e:
        result["data"]["sql_error"] = str(e)[:100]

    # Search Odoo
    try:
        odoo = OdooConnector()
        for term in search_terms:
            user = await odoo.get_account(term)
            if user:
                result["found_in"].append("Odoo")
                result["data"]["odoo"] = user
                break
    except Exception as e:
        result["data"]["odoo_error"] = str(e)[:100]

    # Calculate sync status
    count = len(result["found_in"])
    if count == 3:
        result["sync_status"] = "fully_synced"
        result["message"] = "Utilisateur present dans tous les systemes"
    elif count == 2:
        result["sync_status"] = "partially_synced"
        missing = [s for s in ["LDAP", "SQL", "Odoo"] if s not in result["found_in"]]
        result["message"] = f"Manquant dans: {', '.join(missing)}"
    elif count == 1:
        result["sync_status"] = "isolated"
        result["message"] = f"Present uniquement dans: {result['found_in'][0]}"
    else:
        result["sync_status"] = "not_found"
        result["message"] = "Utilisateur non trouve"

    return result


@router.post("/sync-user/{identifier}", response_model=Dict[str, Any])
async def sync_user_to_systems(
    identifier: str,
    target_systems: List[str],
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Synchronise un utilisateur vers les systemes specifies.
    Copie les donnees depuis le systeme source vers les cibles.
    """
    # First find the user
    user_ref = await get_user_cross_reference(identifier, current_user)

    if user_ref["sync_status"] == "not_found":
        raise HTTPException(status_code=404, detail="Utilisateur non trouve")

    # Determine source data (prefer LDAP > SQL > Odoo)
    source_data = None
    source_system = None

    if "ldap" in user_ref["data"]:
        source_data = user_ref["data"]["ldap"]
        source_system = "LDAP"
    elif "sql" in user_ref["data"]:
        source_data = user_ref["data"]["sql"]
        source_system = "SQL"
    elif "odoo" in user_ref["data"]:
        source_data = user_ref["data"]["odoo"]
        source_system = "Odoo"

    if not source_data:
        raise HTTPException(status_code=400, detail="Aucune donnee source disponible")

    result = {
        "identifier": identifier,
        "source_system": source_system,
        "sync_results": {},
        "timestamp": datetime.utcnow().isoformat()
    }

    # Normalize data for syncing
    sync_data = {
        "firstname": source_data.get("givenName") or source_data.get("first_name") or source_data.get("name", "").split()[0] if source_data.get("name") else "",
        "lastname": source_data.get("sn") or source_data.get("last_name") or " ".join(source_data.get("name", "").split()[1:]) if source_data.get("name") else "",
        "email": source_data.get("mail") or source_data.get("email") or source_data.get("login"),
        "login": source_data.get("uid") or source_data.get("username") or source_data.get("login"),
    }

    # Sync to each target
    for target in target_systems:
        if target == source_system:
            result["sync_results"][target] = {"status": "skipped", "reason": "Source system"}
            continue

        try:
            if target == "LDAP" and target not in user_ref["found_in"]:
                ldap = LDAPConnector()
                await ldap.create_account(sync_data["login"], {
                    "firstname": sync_data["firstname"],
                    "lastname": sync_data["lastname"],
                    "email": sync_data["email"]
                })
                result["sync_results"]["LDAP"] = {"status": "created"}

            elif target == "SQL" and target not in user_ref["found_in"]:
                sql = SQLConnector()
                await sql.create_account(sync_data["login"], {
                    "first_name": sync_data["firstname"],
                    "last_name": sync_data["lastname"],
                    "email": sync_data["email"],
                    "department": "Imported"
                })
                result["sync_results"]["SQL"] = {"status": "created"}

            elif target == "Odoo" and target not in user_ref["found_in"]:
                odoo = OdooConnector()
                await odoo.create_account(sync_data["login"], {
                    "firstname": sync_data["firstname"],
                    "lastname": sync_data["lastname"],
                    "email": sync_data["email"]
                })
                result["sync_results"]["Odoo"] = {"status": "created"}

            else:
                result["sync_results"][target] = {"status": "skipped", "reason": "Already exists"}

        except Exception as e:
            result["sync_results"][target] = {"status": "error", "error": str(e)[:100]}

    return result


@router.get("/odoo/contacts", response_model=Dict[str, Any])
async def get_odoo_contacts(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    """
    Liste les contacts Odoo (res.partner) avec leurs informations.
    Inclut contacts et entreprises pour une vue complete.
    """
    import xmlrpc.client
    from app.core.config import settings

    try:
        common = xmlrpc.client.ServerProxy(f'{settings.ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(settings.ODOO_DB, settings.ODOO_USER, settings.ODOO_PASSWORD, {})

        if not uid:
            raise HTTPException(status_code=500, detail="Odoo authentication failed")

        models = xmlrpc.client.ServerProxy(f'{settings.ODOO_URL}/xmlrpc/2/object')

        # Get contacts (non-companies)
        contacts = models.execute_kw(
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            'res.partner', 'search_read',
            [[('is_company', '=', False)]],
            {'fields': ['id', 'name', 'email', 'phone', 'city', 'function', 'create_date'],
             'limit': limit,
             'order': 'create_date desc'}
        )

        # Get companies
        companies = models.execute_kw(
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            'res.partner', 'search_read',
            [[('is_company', '=', True)]],
            {'fields': ['id', 'name', 'email', 'phone', 'city'],
             'limit': 10}
        )

        # Get users
        users = models.execute_kw(
            settings.ODOO_DB, uid, settings.ODOO_PASSWORD,
            'res.users', 'search_read',
            [[]],
            {'fields': ['id', 'name', 'login', 'active']}
        )

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "contacts": {
                "count": len(contacts),
                "data": contacts
            },
            "companies": {
                "count": len(companies),
                "data": companies
            },
            "users": {
                "count": len(users),
                "data": users
            },
            "summary": {
                "total_contacts": len(contacts),
                "total_companies": len(companies),
                "total_users": len(users)
            }
        }

    except Exception as e:
        logger.error("Odoo contacts fetch failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Odoo error: {str(e)[:200]}")


@router.get("/health-check", response_model=Dict[str, Any])
async def check_all_systems_health(
    current_user: dict = Depends(get_current_user)
):
    """
    Verifie la connectivite de tous les systemes cibles.
    Retourne l'etat de sante de chaque systeme.
    """
    health = {
        "timestamp": datetime.utcnow().isoformat(),
        "systems": {},
        "overall_status": "healthy"
    }

    # Check LDAP
    try:
        ldap = LDAPConnector()
        ldap_ok = await ldap.test_connection()
        health["systems"]["LDAP"] = {
            "status": "healthy" if ldap_ok else "unhealthy",
            "latency_ms": 0  # Could add timing
        }
    except Exception as e:
        health["systems"]["LDAP"] = {"status": "error", "error": str(e)[:100]}
        health["overall_status"] = "degraded"

    # Check SQL
    try:
        sql = SQLConnector()
        sql_ok = await sql.test_connection()
        health["systems"]["SQL"] = {
            "status": "healthy" if sql_ok else "unhealthy"
        }
    except Exception as e:
        health["systems"]["SQL"] = {"status": "error", "error": str(e)[:100]}
        health["overall_status"] = "degraded"

    # Check Odoo
    try:
        odoo = OdooConnector()
        odoo_ok = await odoo.test_connection()
        health["systems"]["Odoo"] = {
            "status": "healthy" if odoo_ok else "unhealthy"
        }
    except Exception as e:
        health["systems"]["Odoo"] = {"status": "error", "error": str(e)[:100]}
        health["overall_status"] = "degraded"

    # Check if all systems are down
    unhealthy_count = sum(1 for s in health["systems"].values() if s.get("status") != "healthy")
    if unhealthy_count == len(health["systems"]):
        health["overall_status"] = "critical"
    elif unhealthy_count > 0:
        health["overall_status"] = "degraded"

    return health


# ==================== LiveSync Odoo -> MidPoint ====================

@router.get("/odoo/employees", response_model=Dict[str, Any])
async def get_odoo_employees(
    current_user: dict = Depends(get_current_user)
):
    """
    Liste tous les employes Odoo avec leurs informations.
    Utilise pour la synchronisation vers MidPoint.
    """
    try:
        odoo = OdooConnector()
        employees = await odoo.list_employees()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(employees),
            "employees": employees
        }

    except Exception as e:
        logger.error("Failed to get Odoo employees", error=str(e))
        raise HTTPException(status_code=500, detail=f"Odoo error: {str(e)[:200]}")


@router.get("/midpoint/users", response_model=Dict[str, Any])
async def get_midpoint_users_for_sync(
    current_user: dict = Depends(get_current_user)
):
    """
    Liste tous les utilisateurs MidPoint pour la comparaison.
    """
    try:
        client = MidPointClient()
        users = await client.get_all_accounts()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(users),
            "users": users
        }

    except Exception as e:
        logger.error("Failed to get MidPoint users", error=str(e))
        raise HTTPException(status_code=500, detail=f"MidPoint error: {str(e)[:200]}")


@router.get("/sync/odoo-midpoint/compare", response_model=Dict[str, Any])
async def compare_odoo_midpoint(
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Compare les employes Odoo avec les utilisateurs MidPoint.
    Identifie les employes a synchroniser.
    """
    try:
        # Get Odoo employees
        odoo = OdooConnector()
        odoo_employees = await odoo.list_employees()

        # Get MidPoint users
        client = MidPointClient()
        midpoint_users = await client.get_all_accounts()

        # Build lookup by email/name
        midpoint_by_email = {}
        midpoint_by_name = {}
        for user in midpoint_users:
            email = user.get("email", "").lower() if user.get("email") else None
            full_name = user.get("fullName", "").lower() if user.get("fullName") else None
            # MidPointClient._parse_user retourne 'name' pour le username
            username = user.get("name", "").lower() if user.get("name") else None

            if email:
                midpoint_by_email[email] = user
            if full_name:
                midpoint_by_name[full_name] = user
            if username:
                midpoint_by_name[username] = user

        # Compare
        synced = []
        to_sync = []
        odoo_only = []

        for emp in odoo_employees:
            email = emp.get("email", "").lower() if emp.get("email") else None
            name = emp.get("name", "").lower() if emp.get("name") else None

            found_in_midpoint = None
            if email and email in midpoint_by_email:
                found_in_midpoint = midpoint_by_email[email]
            elif name and name in midpoint_by_name:
                found_in_midpoint = midpoint_by_name[name]

            if found_in_midpoint:
                synced.append({
                    "odoo": emp,
                    "midpoint": found_in_midpoint,
                    "status": "synced"
                })
            else:
                to_sync.append(emp)
                odoo_only.append(emp)

        # Users only in MidPoint (not in Odoo)
        odoo_emails = {e.get("email", "").lower() for e in odoo_employees if e.get("email")}
        odoo_names = {e.get("name", "").lower() for e in odoo_employees if e.get("name")}
        midpoint_only = []

        for user in midpoint_users:
            email = user.get("email", "").lower() if user.get("email") else None
            name = user.get("fullName", "").lower() if user.get("fullName") else None

            if email and email in odoo_emails:
                continue
            if name and name in odoo_names:
                continue
            midpoint_only.append(user)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "odoo_employees": len(odoo_employees),
                "midpoint_users": len(midpoint_users),
                "synced": len(synced),
                "to_sync_from_odoo": len(to_sync),
                "midpoint_only": len(midpoint_only)
            },
            "to_sync": to_sync[:50],  # Limit for response size
            "synced": synced[:20],
            "midpoint_only": midpoint_only[:20]
        }

    except Exception as e:
        logger.error("Failed to compare Odoo-MidPoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)[:200]}")


@router.post("/sync/odoo-to-midpoint", response_model=Dict[str, Any])
async def sync_odoo_employees_to_midpoint(
    employee_ids: List[int] = Query(default=None, description="List of Odoo employee IDs to sync. If empty, syncs all."),
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Synchronise les employes Odoo vers MidPoint.
    Cree les utilisateurs MidPoint correspondants.
    """
    try:
        odoo = OdooConnector()
        client = MidPointClient()

        # Get employees to sync
        if employee_ids:
            employees = []
            for emp_id in employee_ids:
                emp = await odoo.get_employee(emp_id)
                if emp:
                    employees.append(emp)
        else:
            employees = await odoo.list_employees()

        if not employees:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Aucun employe a synchroniser",
                "synced": 0,
                "results": []
            }

        # Get existing MidPoint users for duplicate check
        midpoint_users = await client.get_all_accounts()
        existing_emails = {u.get("email", "").lower() for u in midpoint_users if u.get("email")}
        # MidPointClient._parse_user retourne 'name' pour le username
        existing_usernames = {u.get("name", "").lower() for u in midpoint_users if u.get("name")}

        results = []
        synced_count = 0
        skipped_count = 0
        error_count = 0

        for emp in employees:
            emp_name = emp.get("name", "")
            emp_email = emp.get("email", "")

            # Generate username from name
            name_parts = emp_name.split()
            if len(name_parts) >= 2:
                firstname = name_parts[0]
                lastname = " ".join(name_parts[1:])
                username = f"{firstname.lower()}{lastname.lower().replace(' ', '')}"
            else:
                firstname = emp_name
                lastname = ""
                username = emp_name.lower().replace(" ", "")

            # Check if already exists
            if emp_email and emp_email.lower() in existing_emails:
                results.append({
                    "employee_id": emp.get("id"),
                    "name": emp_name,
                    "status": "skipped",
                    "reason": "Email already exists in MidPoint"
                })
                skipped_count += 1
                continue

            if username.lower() in existing_usernames:
                results.append({
                    "employee_id": emp.get("id"),
                    "name": emp_name,
                    "status": "skipped",
                    "reason": "Username already exists in MidPoint"
                })
                skipped_count += 1
                continue

            # Create in MidPoint
            try:
                user_data = {
                    "username": username,
                    "firstname": firstname,
                    "lastname": lastname,
                    "email": emp_email or f"{username}@example.com",
                    "department": emp.get("department"),
                    "title": emp.get("job_title"),
                }

                midpoint_result = await client.create_account(user_data)

                # Check if user already exists (returned by improved create_account)
                if midpoint_result and midpoint_result.get("status") == "already_exists":
                    results.append({
                        "employee_id": emp.get("id"),
                        "name": emp_name,
                        "username": username,
                        "status": "skipped",
                        "reason": "User already exists in MidPoint"
                    })
                    skipped_count += 1
                else:
                    results.append({
                        "employee_id": emp.get("id"),
                        "name": emp_name,
                        "username": username,
                        "status": "created",
                        "midpoint_oid": midpoint_result.get("oid") if midpoint_result else None
                    })
                    synced_count += 1

                # Add to existing set to prevent duplicates in same batch
                if emp_email:
                    existing_emails.add(emp_email.lower())
                existing_usernames.add(username.lower())

            except Exception as create_error:
                error_msg = str(create_error)
                # Check for common "already exists" error patterns
                if "409" in error_msg or "already" in error_msg.lower() or "conflict" in error_msg.lower():
                    results.append({
                        "employee_id": emp.get("id"),
                        "name": emp_name,
                        "username": username,
                        "status": "skipped",
                        "reason": "User already exists in MidPoint"
                    })
                    skipped_count += 1
                else:
                    results.append({
                        "employee_id": emp.get("id"),
                        "name": emp_name,
                        "status": "error",
                        "error": error_msg[:100]
                    })
                    error_count += 1

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_employees": len(employees),
                "synced": synced_count,
                "skipped": skipped_count,
                "errors": error_count
            },
            "results": results
        }

    except Exception as e:
        logger.error("Failed to sync Odoo to MidPoint", error=str(e))
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)[:200]}")


# ==================== LiveSync avec Workflow d'Approbation ====================

class SyncWithApprovalRequest(BaseModel):
    """Requete de synchronisation avec approbation."""
    employee_ids: Optional[List[int]] = None
    manager_email: str
    workflow_type: str = "full"  # "full", "manager_only", "rh_it"


@router.post("/sync/odoo-to-midpoint/with-approval", response_model=Dict[str, Any])
async def sync_odoo_to_midpoint_with_approval(
    request: SyncWithApprovalRequest,
    current_user: dict = Depends(require_role(["admin", "iam_engineer"])),
    session=Depends(get_session)
):
    """
    Synchronise les employes Odoo vers MidPoint AVEC workflow d'approbation multi-niveaux.

    Chaine d'approbation: Manager → RH → IT Admin

    1. Cree un workflow d'approbation pour chaque employe
    2. Envoie notification email au manager
    3. Le compte est cree dans MidPoint uniquement apres approbation complete
    """
    try:
        odoo = OdooConnector()
        workflow_service = WorkflowService(session)

        # Get employees to sync
        if request.employee_ids:
            employees = []
            for emp_id in request.employee_ids:
                emp = await odoo.get_employee(emp_id)
                if emp:
                    employees.append(emp)
        else:
            employees = await odoo.list_employees()

        if not employees:
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Aucun employe a synchroniser",
                "workflows_created": 0,
                "results": []
            }

        # Get existing MidPoint users for duplicate check
        client = MidPointClient()
        midpoint_users = await client.get_all_accounts()
        existing_emails = {u.get("email", "").lower() for u in midpoint_users if u.get("email")}
        existing_usernames = {u.get("name", "").lower() for u in midpoint_users if u.get("name")}

        results = []
        workflows_created = 0
        skipped_count = 0

        for emp in employees:
            emp_name = emp.get("name", "")
            emp_email = emp.get("email", "") or emp.get("work_email", "")
            department = emp.get("department", "N/A")
            job_title = emp.get("job_title", "N/A")
            manager_name = emp.get("manager_name", "")

            # Generate username from name
            name_parts = emp_name.split()
            if len(name_parts) >= 2:
                firstname = name_parts[0]
                lastname = " ".join(name_parts[1:])
                username = f"{firstname.lower()}.{lastname.lower().replace(' ', '')}"
            else:
                firstname = emp_name
                lastname = ""
                username = emp_name.lower().replace(" ", ".")

            # Check if already exists in MidPoint
            if emp_email and emp_email.lower() in existing_emails:
                results.append({
                    "employee_id": emp.get("id"),
                    "name": emp_name,
                    "status": "skipped",
                    "reason": "Email deja existant dans MidPoint"
                })
                skipped_count += 1
                continue

            if username.lower() in existing_usernames:
                results.append({
                    "employee_id": emp.get("id"),
                    "name": emp_name,
                    "status": "skipped",
                    "reason": "Username deja existant dans MidPoint"
                })
                skipped_count += 1
                continue

            # Creer le workflow d'approbation multi-niveaux
            operation_id = f"odoo-sync-{emp.get('id')}-{str(uuid.uuid4())[:8]}"

            user_data = {
                "account_id": username,
                "firstname": firstname,
                "lastname": lastname,
                "email": emp_email or f"{username}@upec.fr",
                "department": department,
                "job_title": job_title,
                "employee_id": str(emp.get("id")),
                "permission_level": 1,
                "source": "odoo",
                "odoo_employee_id": emp.get("id"),
                "manager_name": manager_name,
            }

            # Determiner l'email du manager
            # Si l'employe a un manager dans Odoo, utiliser son email, sinon utiliser celui fourni
            manager_email_to_use = request.manager_email
            if emp.get("manager_email"):
                manager_email_to_use = emp.get("manager_email")

            try:
                workflow_result = await workflow_service.create_multi_level_approval_workflow(
                    operation_id=operation_id,
                    user_data=user_data,
                    manager_email=manager_email_to_use,
                    requester=current_user.get("username", "admin"),
                    workflow_type=request.workflow_type
                )

                results.append({
                    "employee_id": emp.get("id"),
                    "name": emp_name,
                    "username": username,
                    "status": "workflow_created",
                    "workflow_id": workflow_result.get("workflow_id"),
                    "workflow_type": request.workflow_type,
                    "total_levels": workflow_result.get("total_levels", 3),
                    "email_sent_to": manager_email_to_use,
                    "email_sent": workflow_result.get("email_sent", False)
                })
                workflows_created += 1

                # Add to existing sets to prevent duplicates in same batch
                if emp_email:
                    existing_emails.add(emp_email.lower())
                existing_usernames.add(username.lower())

            except Exception as wf_error:
                results.append({
                    "employee_id": emp.get("id"),
                    "name": emp_name,
                    "status": "error",
                    "error": str(wf_error)[:100]
                })

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_type": request.workflow_type,
            "approval_chain": "Manager → RH → IT Admin" if request.workflow_type == "full" else
                             "Manager uniquement" if request.workflow_type == "manager_only" else
                             "RH → IT Admin",
            "summary": {
                "total_employees": len(employees),
                "workflows_created": workflows_created,
                "skipped": skipped_count
            },
            "message": f"{workflows_created} workflow(s) d'approbation cree(s). Les comptes seront crees apres approbation complete.",
            "results": results
        }

    except Exception as e:
        logger.error("Failed to create approval workflows", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.post("/sync/execute-approved/{workflow_id}", response_model=Dict[str, Any])
async def execute_approved_sync(
    workflow_id: str,
    current_user: dict = Depends(require_role(["admin", "it_admin"])),
    session=Depends(get_session)
):
    """
    Execute la creation du compte MidPoint apres approbation complete du workflow.
    Cette fonction est appelee automatiquement ou manuellement apres approbation.
    """
    from app.core.memory_store import memory_store

    workflow = memory_store.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow non trouve")

    if workflow.get("status") != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Workflow non approuve. Statut actuel: {workflow.get('status')}"
        )

    context = workflow.get("context", {})

    # Verifier si c'est un sync Odoo
    if context.get("source") != "odoo":
        raise HTTPException(status_code=400, detail="Ce workflow n'est pas une synchronisation Odoo")

    try:
        client = MidPointClient()

        user_data = {
            "username": context.get("account_id"),
            "firstname": context.get("firstname"),
            "lastname": context.get("lastname"),
            "email": context.get("email"),
            "department": context.get("department"),
            "title": context.get("job_title"),
        }

        midpoint_result = await client.create_account(user_data)

        # Update workflow with execution result
        workflow["executed"] = True
        workflow["executed_at"] = datetime.utcnow().isoformat()
        workflow["midpoint_oid"] = midpoint_result.get("oid") if midpoint_result else None
        workflow["history"].append({
            "timestamp": datetime.utcnow().isoformat(),
            "action": "account_created",
            "details": f"Compte cree dans MidPoint: {context.get('account_id')}"
        })
        memory_store.save_workflow(workflow_id, workflow)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_id": workflow_id,
            "status": "created",
            "username": context.get("account_id"),
            "midpoint_oid": midpoint_result.get("oid") if midpoint_result else None,
            "message": f"Compte {context.get('account_id')} cree avec succes dans MidPoint"
        }

    except Exception as e:
        logger.error("Failed to execute approved sync", error=str(e), workflow_id=workflow_id)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


# ==================== Account Activation/Deactivation ====================

@router.post("/account/{username}/disable", response_model=Dict[str, Any])
async def disable_user_account(
    username: str,
    systems: List[str] = Query(default=["midpoint", "ldap", "odoo"]),
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Desactive un compte utilisateur dans les systemes specifies.
    Ne supprime pas le compte, le rend simplement inactif.
    """
    results = {
        "username": username,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "disable",
        "results": {}
    }

    if "midpoint" in systems:
        try:
            client = MidPointClient()
            success = await client.disable_account(username)
            results["results"]["midpoint"] = {"status": "disabled" if success else "failed"}
        except Exception as e:
            results["results"]["midpoint"] = {"status": "error", "error": str(e)[:100]}

    if "ldap" in systems:
        try:
            ldap = LDAPConnector()
            success = await ldap.disable_account(username)
            results["results"]["ldap"] = {"status": "disabled" if success else "failed"}
        except Exception as e:
            results["results"]["ldap"] = {"status": "error", "error": str(e)[:100]}

    if "odoo" in systems:
        try:
            odoo = OdooConnector()
            success = await odoo.disable_account(username)
            results["results"]["odoo"] = {"status": "disabled" if success else "failed"}
        except Exception as e:
            results["results"]["odoo"] = {"status": "error", "error": str(e)[:100]}

    return results


@router.post("/account/{username}/enable", response_model=Dict[str, Any])
async def enable_user_account(
    username: str,
    systems: List[str] = Query(default=["midpoint", "ldap", "odoo"]),
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Reactive un compte utilisateur dans les systemes specifies.
    """
    results = {
        "username": username,
        "timestamp": datetime.utcnow().isoformat(),
        "action": "enable",
        "results": {}
    }

    if "midpoint" in systems:
        try:
            client = MidPointClient()
            success = await client.enable_account(username)
            results["results"]["midpoint"] = {"status": "enabled" if success else "failed"}
        except Exception as e:
            results["results"]["midpoint"] = {"status": "error", "error": str(e)[:100]}

    if "ldap" in systems:
        try:
            ldap = LDAPConnector()
            success = await ldap.enable_account(username)
            results["results"]["ldap"] = {"status": "enabled" if success else "failed"}
        except Exception as e:
            results["results"]["ldap"] = {"status": "error", "error": str(e)[:100]}

    if "odoo" in systems:
        try:
            odoo = OdooConnector()
            success = await odoo.enable_account(username)
            results["results"]["odoo"] = {"status": "enabled" if success else "failed"}
        except Exception as e:
            results["results"]["odoo"] = {"status": "error", "error": str(e)[:100]}

    return results


# ==================== Contract Management ====================

@router.get("/contracts/expired", response_model=Dict[str, Any])
async def get_expired_contracts(
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Liste les employes avec des contrats expires.
    Ces comptes devraient etre desactives.
    """
    try:
        odoo = OdooConnector()
        expired = await odoo.get_expired_contracts()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(expired),
            "expired_contracts": expired
        }

    except Exception as e:
        logger.error("Failed to get expired contracts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.get("/contracts/expiring", response_model=Dict[str, Any])
async def get_expiring_contracts(
    days: int = Query(default=30, description="Nombre de jours avant expiration"),
    current_user: dict = Depends(require_role(["admin", "iam_engineer"]))
):
    """
    Liste les employes dont le contrat expire dans X jours.
    Permet d'anticiper les departs.
    """
    try:
        odoo = OdooConnector()
        expiring = await odoo.get_expiring_contracts(days)

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "days_threshold": days,
            "count": len(expiring),
            "expiring_contracts": expiring
        }

    except Exception as e:
        logger.error("Failed to get expiring contracts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")


@router.get("/odoo/employees-with-contracts", response_model=Dict[str, Any])
async def get_odoo_employees_with_contracts(
    current_user: dict = Depends(get_current_user)
):
    """
    Liste tous les employes Odoo avec leurs informations de contrat.
    """
    try:
        odoo = OdooConnector()
        employees = await odoo.list_employees_with_contracts()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "count": len(employees),
            "employees": employees
        }

    except Exception as e:
        logger.error("Failed to get employees with contracts", error=str(e))
        raise HTTPException(status_code=500, detail=f"Error: {str(e)[:200]}")
