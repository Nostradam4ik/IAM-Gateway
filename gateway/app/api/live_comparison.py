"""
API de comparaison en temps reel entre systemes.
Fonctionnalite innovante pour visualiser l'etat de synchronisation.
"""
from fastapi import APIRouter, Depends, HTTPException
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
