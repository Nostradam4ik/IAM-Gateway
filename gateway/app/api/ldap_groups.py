"""
API pour la gestion des groupes LDAP
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from ldap3 import Server, Connection, ALL, SUBTREE, MODIFY_ADD, MODIFY_DELETE
import structlog

from app.core.config import settings
from app.api.admin import get_current_user

logger = structlog.get_logger()
router = APIRouter(prefix="/ldap/groups", tags=["LDAP Groups"])


class GroupInfo(BaseModel):
    """Information sur un groupe LDAP"""
    cn: str
    dn: str
    description: Optional[str] = None
    member_count: int = 0


class GroupMember(BaseModel):
    """Membre d'un groupe"""
    dn: str
    uid: str
    cn: Optional[str] = None
    mail: Optional[str] = None


class GroupDetails(BaseModel):
    """Détails complets d'un groupe"""
    cn: str
    dn: str
    description: Optional[str] = None
    members: List[GroupMember] = []


class AddRemoveMemberRequest(BaseModel):
    """Requête pour ajouter/retirer un membre"""
    username: str


def get_ldap_connection() -> Connection:
    """Obtenir une connexion LDAP"""
    server = Server(settings.LDAP_HOST, port=settings.LDAP_PORT, get_info=ALL)
    conn = Connection(
        server,
        user=settings.LDAP_BIND_DN,
        password=settings.LDAP_BIND_PASSWORD,
        auto_bind=True
    )
    return conn


@router.get("", response_model=List[GroupInfo])
async def list_groups(current_user: dict = Depends(get_current_user)):
    """
    Liste tous les groupes LDAP disponibles.
    """
    conn = None
    try:
        conn = get_ldap_connection()
        groups_ou = f"ou=groups,{settings.LDAP_BASE_DN}"

        # Rechercher tous les groupes
        conn.search(
            search_base=groups_ou,
            search_filter="(|(objectClass=groupOfNames)(objectClass=groupOfUniqueNames)(objectClass=posixGroup))",
            search_scope=SUBTREE,
            attributes=['cn', 'description', 'member', 'uniqueMember', 'memberUid', 'objectClass']
        )

        groups = []
        for entry in conn.entries:
            # Compter les membres (supporter member, uniqueMember et memberUid)
            # Ne compter que les membres valides (avec uid= dans le DN)
            member_count = 0
            if hasattr(entry, 'uniqueMember') and entry.uniqueMember:
                members = entry.uniqueMember.values if hasattr(entry.uniqueMember, 'values') else [entry.uniqueMember]
                member_count = len([m for m in members if m and 'uid=' in str(m)])
            elif hasattr(entry, 'member') and entry.member:
                members = entry.member.values if hasattr(entry.member, 'values') else [entry.member]
                member_count = len([m for m in members if m and 'uid=' in str(m)])
            elif hasattr(entry, 'memberUid') and entry.memberUid:
                members = entry.memberUid.values if hasattr(entry.memberUid, 'values') else [entry.memberUid]
                member_count = len([m for m in members if m])

            groups.append(GroupInfo(
                cn=str(entry.cn),
                dn=str(entry.entry_dn),
                description=str(entry.description) if hasattr(entry, 'description') and entry.description else None,
                member_count=member_count
            ))

        # Trier par nom
        groups.sort(key=lambda g: g.cn.lower())

        logger.info("Listed LDAP groups", count=len(groups))
        return groups

    except Exception as e:
        logger.error("Failed to list LDAP groups", error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur LDAP: {str(e)}")
    finally:
        if conn:
            conn.unbind()


@router.get("/{group_name}", response_model=GroupDetails)
async def get_group_details(group_name: str, current_user: dict = Depends(get_current_user)):
    """
    Obtenir les détails d'un groupe et ses membres.
    """
    conn = None
    try:
        conn = get_ldap_connection()
        groups_ou = f"ou=groups,{settings.LDAP_BASE_DN}"
        users_ou = f"ou=users,{settings.LDAP_BASE_DN}"

        # Rechercher le groupe
        conn.search(
            search_base=groups_ou,
            search_filter=f"(cn={group_name})",
            search_scope=SUBTREE,
            attributes=['cn', 'description', 'member', 'uniqueMember', 'memberUid', 'objectClass']
        )

        if not conn.entries:
            raise HTTPException(status_code=404, detail=f"Groupe '{group_name}' non trouvé")

        entry = conn.entries[0]

        # Récupérer les membres (supporter uniqueMember et member)
        members = []
        member_dns = []

        if hasattr(entry, 'uniqueMember') and entry.uniqueMember:
            member_dns = entry.uniqueMember.values if hasattr(entry.uniqueMember, 'values') else [str(entry.uniqueMember)]
        elif hasattr(entry, 'member') and entry.member:
            member_dns = entry.member.values if hasattr(entry.member, 'values') else [str(entry.member)]

        # Pour chaque membre, récupérer ses infos
        for member_dn in member_dns:
            if not member_dn or member_dn == '':
                continue

            # Extraire l'uid du DN
            uid = None
            if 'uid=' in str(member_dn):
                uid = str(member_dn).split('uid=')[1].split(',')[0]

            if uid:
                # Rechercher les détails de l'utilisateur
                conn.search(
                    search_base=users_ou,
                    search_filter=f"(uid={uid})",
                    search_scope=SUBTREE,
                    attributes=['uid', 'cn', 'mail']
                )

                if conn.entries:
                    user_entry = conn.entries[0]
                    members.append(GroupMember(
                        dn=str(member_dn),
                        uid=str(user_entry.uid) if hasattr(user_entry, 'uid') else uid,
                        cn=str(user_entry.cn) if hasattr(user_entry, 'cn') else None,
                        mail=str(user_entry.mail) if hasattr(user_entry, 'mail') else None
                    ))
                else:
                    members.append(GroupMember(
                        dn=str(member_dn),
                        uid=uid
                    ))

        # Trier les membres par uid
        members.sort(key=lambda m: m.uid.lower() if m.uid else '')

        return GroupDetails(
            cn=str(entry.cn),
            dn=str(entry.entry_dn),
            description=str(entry.description) if hasattr(entry, 'description') and entry.description else None,
            members=members
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get group details", group=group_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur LDAP: {str(e)}")
    finally:
        if conn:
            conn.unbind()


@router.post("/{group_name}/members")
async def add_member_to_group(
    group_name: str,
    request: AddRemoveMemberRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Ajouter un utilisateur à un groupe LDAP.
    """
    conn = None
    try:
        conn = get_ldap_connection()
        groups_ou = f"ou=groups,{settings.LDAP_BASE_DN}"
        users_ou = f"ou=users,{settings.LDAP_BASE_DN}"

        # Vérifier que l'utilisateur existe
        conn.search(
            search_base=users_ou,
            search_filter=f"(uid={request.username})",
            search_scope=SUBTREE,
            attributes=['uid']
        )

        if not conn.entries:
            raise HTTPException(status_code=404, detail=f"Utilisateur '{request.username}' non trouvé")

        user_dn = str(conn.entries[0].entry_dn)
        group_dn = f"cn={group_name},{groups_ou}"

        # Déterminer le type de groupe (groupOfUniqueNames ou groupOfNames)
        conn.search(
            search_base=group_dn,
            search_filter="(objectClass=*)",
            search_scope=SUBTREE,
            attributes=['objectClass']
        )

        if not conn.entries:
            raise HTTPException(status_code=404, detail=f"Groupe '{group_name}' non trouvé")

        object_classes = [str(oc).lower() for oc in conn.entries[0].objectClass.values]

        # Choisir l'attribut approprié selon le type de groupe
        if 'groupofuniquenames' in object_classes:
            member_attr = 'uniqueMember'
        elif 'groupofnames' in object_classes:
            member_attr = 'member'
        else:
            member_attr = 'memberUid'  # posixGroup

        # Ajouter l'utilisateur au groupe
        result = conn.modify(
            group_dn,
            {member_attr: [(MODIFY_ADD, [user_dn])]}
        )

        if result:
            logger.info("User added to group", user=request.username, group=group_name)
            return {
                "status": "success",
                "message": f"Utilisateur '{request.username}' ajouté au groupe '{group_name}'",
                "user_dn": user_dn,
                "group_dn": group_dn
            }
        else:
            # Vérifier si c'est parce que l'utilisateur est déjà membre
            if "already exists" in str(conn.result).lower() or "attribute or value exists" in str(conn.result).lower():
                return {
                    "status": "already_member",
                    "message": f"Utilisateur '{request.username}' est déjà membre du groupe '{group_name}'"
                }
            raise HTTPException(status_code=400, detail=f"Échec: {conn.result}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add member to group", user=request.username, group=group_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur LDAP: {str(e)}")
    finally:
        if conn:
            conn.unbind()


@router.delete("/{group_name}/members/{username}")
async def remove_member_from_group(
    group_name: str,
    username: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Retirer un utilisateur d'un groupe LDAP.
    """
    conn = None
    try:
        conn = get_ldap_connection()
        groups_ou = f"ou=groups,{settings.LDAP_BASE_DN}"
        users_ou = f"ou=users,{settings.LDAP_BASE_DN}"

        # Trouver le DN de l'utilisateur
        conn.search(
            search_base=users_ou,
            search_filter=f"(uid={username})",
            search_scope=SUBTREE,
            attributes=['uid']
        )

        if not conn.entries:
            raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé")

        user_dn = str(conn.entries[0].entry_dn)
        group_dn = f"cn={group_name},{groups_ou}"

        # Déterminer le type de groupe
        conn.search(
            search_base=group_dn,
            search_filter="(objectClass=*)",
            search_scope=SUBTREE,
            attributes=['objectClass']
        )

        if not conn.entries:
            raise HTTPException(status_code=404, detail=f"Groupe '{group_name}' non trouvé")

        object_classes = [str(oc).lower() for oc in conn.entries[0].objectClass.values]

        # Choisir l'attribut approprié
        if 'groupofuniquenames' in object_classes:
            member_attr = 'uniqueMember'
        elif 'groupofnames' in object_classes:
            member_attr = 'member'
        else:
            member_attr = 'memberUid'

        # Retirer l'utilisateur du groupe
        result = conn.modify(
            group_dn,
            {member_attr: [(MODIFY_DELETE, [user_dn])]}
        )

        if result:
            logger.info("User removed from group", user=username, group=group_name)
            return {
                "status": "success",
                "message": f"Utilisateur '{username}' retiré du groupe '{group_name}'"
            }
        else:
            raise HTTPException(status_code=400, detail=f"Échec: {conn.result}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to remove member from group", user=username, group=group_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur LDAP: {str(e)}")
    finally:
        if conn:
            conn.unbind()


class LDAPUser(BaseModel):
    """Utilisateur LDAP pour l'autocomplétion"""
    uid: str
    cn: Optional[str] = None
    mail: Optional[str] = None


@router.get("/users/search", response_model=List[LDAPUser])
async def search_ldap_users(q: str = "", limit: int = 10, current_user: dict = Depends(get_current_user)):
    """
    Rechercher des utilisateurs LDAP par uid, cn ou mail.
    Utilisé pour l'autocomplétion lors de l'ajout de membres aux groupes.
    """
    conn = None
    try:
        conn = get_ldap_connection()
        users_ou = f"ou=users,{settings.LDAP_BASE_DN}"

        # Si la recherche est vide, retourner les premiers utilisateurs
        if not q or len(q) < 1:
            search_filter = "(objectClass=inetOrgPerson)"
        else:
            # Rechercher par uid, cn ou mail (insensible à la casse)
            search_filter = f"(|(uid=*{q}*)(cn=*{q}*)(mail=*{q}*))"

        conn.search(
            search_base=users_ou,
            search_filter=search_filter,
            search_scope=SUBTREE,
            attributes=['uid', 'cn', 'mail'],
            size_limit=limit
        )

        users = []
        for entry in conn.entries:
            uid = str(entry.uid) if hasattr(entry, 'uid') and entry.uid else ""
            # Filtrer les OIDs MidPoint (format UUID) - garder seulement les vrais usernames
            if uid and not (len(uid) == 36 and uid.count('-') == 4):
                users.append(LDAPUser(
                    uid=uid,
                    cn=str(entry.cn) if hasattr(entry, 'cn') and entry.cn else None,
                    mail=str(entry.mail) if hasattr(entry, 'mail') and entry.mail else None
                ))

        # Trier par uid
        users.sort(key=lambda u: u.uid.lower())

        logger.info("Searched LDAP users", query=q, count=len(users))
        return users

    except Exception as e:
        logger.error("Failed to search LDAP users", query=q, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur LDAP: {str(e)}")
    finally:
        if conn:
            conn.unbind()


@router.get("/user/{username}/memberships", response_model=List[str])
async def get_user_groups(username: str, current_user: dict = Depends(get_current_user)):
    """
    Obtenir la liste des groupes dont un utilisateur est membre.
    """
    conn = None
    try:
        conn = get_ldap_connection()
        groups_ou = f"ou=groups,{settings.LDAP_BASE_DN}"
        users_ou = f"ou=users,{settings.LDAP_BASE_DN}"

        # Trouver le DN de l'utilisateur
        conn.search(
            search_base=users_ou,
            search_filter=f"(uid={username})",
            search_scope=SUBTREE,
            attributes=['uid']
        )

        if not conn.entries:
            raise HTTPException(status_code=404, detail=f"Utilisateur '{username}' non trouvé")

        user_dn = str(conn.entries[0].entry_dn)

        # Rechercher les groupes contenant cet utilisateur
        conn.search(
            search_base=groups_ou,
            search_filter=f"(member={user_dn})",
            search_scope=SUBTREE,
            attributes=['cn']
        )

        groups = [str(entry.cn) for entry in conn.entries]
        groups.sort()

        return groups

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get user groups", user=username, error=str(e))
        raise HTTPException(status_code=500, detail=f"Erreur LDAP: {str(e)}")
    finally:
        if conn:
            conn.unbind()
