"""
Connecteur Odoo ERP via XML-RPC.

Ce module gere les operations CRUD sur Odoo via le protocole XML-RPC :
    - Authentification : /xmlrpc/2/common (authenticate)
    - Operations : /xmlrpc/2/object (execute_kw)

Flux de creation d'un compte :
    1. Creer un contact (res.partner) - nom, email, telephone
    2. Creer un utilisateur (res.users) lie au contact
    3. Creer un employe (hr.employee) lie a l'utilisateur
    4. Optionnel : creer/associer un departement (hr.department)

Particularites :
    - La suppression desactive le compte (active=False) au lieu de le supprimer
    - Les groupes sont des relations many2many : 4=add, 3=remove, 6=set
    - La normalisation des departements permet le mapping automatique des roles
"""
from typing import Dict, Any, Optional, List
import xmlrpc.client
import structlog

from app.connectors.base import BaseConnector
from app.core.config import settings

logger = structlog.get_logger()


class OdooConnector(BaseConnector):
    """
    Connecteur pour Odoo ERP via XML-RPC.

    Supporte:
    - Creation/modification/suppression d'utilisateurs
    - Gestion des contacts (res.partner)
    - Gestion des groupes d'acces
    """

    def __init__(self):
        super().__init__()
        self.url = settings.ODOO_URL
        self.db = settings.ODOO_DB
        self.username = settings.ODOO_USER
        self.password = settings.ODOO_PASSWORD
        self._uid = None

    def _authenticate(self) -> int:
        """Authenticate with Odoo and get user ID."""
        if self._uid:
            return self._uid

        common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
        self._uid = common.authenticate(self.db, self.username, self.password, {})

        if not self._uid:
            raise Exception("Odoo authentication failed")

        return self._uid

    def _get_models(self):
        """Get Odoo models proxy."""
        return xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

    def _execute(self, model: str, method: str, args_list, kwargs_dict=None):
        """Execute Odoo RPC call.

        Args:
            model: Odoo model name (e.g., 'res.users')
            method: Method to call (e.g., 'search_read')
            args_list: List of positional arguments for the method
            kwargs_dict: Optional dictionary of keyword arguments
        """
        uid = self._authenticate()
        models = self._get_models()
        if kwargs_dict:
            return models.execute_kw(
                self.db, uid, self.password,
                model, method, args_list, kwargs_dict
            )
        return models.execute_kw(
            self.db, uid, self.password,
            model, method, args_list
        )

    async def test_connection(self) -> bool:
        """Test Odoo connectivity."""
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            version = common.version()
            logger.info("Odoo connected", version=version.get('server_version'))
            return True
        except Exception as e:
            logger.error("Odoo connection test failed", error=str(e))
            return False

    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create Odoo user account (or update if exists)."""
        try:
            login = attributes.get('login') or attributes.get('email') or account_id

            # Check if user already exists by login or email
            existing_user = await self.get_account(login)
            if existing_user:
                # User exists, update instead of create
                logger.info("Odoo user already exists, updating instead", login=login)
                return await self.update_account(login, attributes)

            # First create a contact (res.partner)
            partner_data = {
                'name': f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip() or account_id,
                'is_company': False,
            }

            # Only add email and phone if not None
            if attributes.get('email') or attributes.get('login'):
                partner_data['email'] = attributes.get('email') or attributes.get('login')
            if attributes.get('phone'):
                partner_data['phone'] = attributes.get('phone')

            partner_result = self._execute('res.partner', 'create', [[partner_data]])
            # Extract partner_id from result (can be int or list)
            partner_id = partner_result[0] if isinstance(partner_result, list) else partner_result

            # Then create user linked to partner
            user_data = {
                'name': partner_data['name'],
                'login': login,
                'partner_id': partner_id,
                'active': attributes.get('active', True),
            }

            # Add groups if specified
            if attributes.get('groups'):
                user_data['groups_id'] = [(6, 0, attributes['groups'])]

            user_result = self._execute('res.users', 'create', [[user_data]])
            # Extract user_id from result (can be int or list)
            user_id = user_result[0] if isinstance(user_result, list) else user_result

            logger.info("Odoo account created", user_id=user_id, login=user_data['login'])

            # Create employee linked to user
            employee_id = await self._create_employee(user_id, partner_id, attributes)

            return {
                "id": user_id,
                "partner_id": partner_id,
                "employee_id": employee_id,
                "login": user_data['login'],
                "status": "created"
            }

        except Exception as e:
            logger.error("Failed to create Odoo account", error=str(e))
            raise

    async def _create_employee(
        self,
        user_id: int,
        partner_id: int,
        attributes: Dict[str, Any]
    ) -> Optional[int]:
        """Create Odoo employee linked to user."""
        try:
            # Check if employee already exists for this user
            existing = self._execute(
                'hr.employee', 'search_read',
                [[('user_id', '=', user_id)]],
                {'fields': ['id']}
            )
            if existing:
                logger.info("Employee already exists for user", user_id=user_id)
                return existing[0]['id']

            # Build employee name
            name = f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip()
            if not name:
                name = attributes.get('name', attributes.get('login', f'User {user_id}'))

            employee_data = {
                'name': name,
                'user_id': user_id,
            }

            # Add optional fields
            if attributes.get('email') or attributes.get('login'):
                employee_data['work_email'] = attributes.get('email') or attributes.get('login')
            if attributes.get('phone'):
                employee_data['work_phone'] = attributes.get('phone')
            if attributes.get('mobile'):
                employee_data['mobile_phone'] = attributes.get('mobile')
            if attributes.get('job_title') or attributes.get('title'):
                employee_data['job_title'] = attributes.get('job_title') or attributes.get('title')
            if attributes.get('department'):
                # Try to find or create department
                dept_id = await self._get_or_create_department(attributes['department'])
                if dept_id:
                    employee_data['department_id'] = dept_id

            employee_result = self._execute('hr.employee', 'create', [[employee_data]])
            employee_id = employee_result[0] if isinstance(employee_result, list) else employee_result

            logger.info("Odoo employee created", employee_id=employee_id, user_id=user_id)
            return employee_id

        except Exception as e:
            logger.warning("Failed to create Odoo employee", error=str(e), user_id=user_id)
            # Don't fail the whole operation if employee creation fails
            return None

    async def _get_or_create_department(self, department_name: str) -> Optional[int]:
        """Get or create department by name."""
        try:
            # Search for existing department
            departments = self._execute(
                'hr.department', 'search_read',
                [[('name', '=', department_name)]],
                {'fields': ['id']}
            )
            if departments:
                return departments[0]['id']

            # Create new department
            result = self._execute('hr.department', 'create', [[{'name': department_name}]])
            dept_id = result[0] if isinstance(result, list) else result
            logger.info("Odoo department created", name=department_name, id=dept_id)
            return dept_id

        except Exception as e:
            logger.warning("Failed to get/create department", error=str(e))
            return None

    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update Odoo user account."""
        try:
            # Find user by login
            user = await self.get_account(account_id)
            if not user:
                raise Exception(f"User {account_id} not found in Odoo")

            user_id = user['id']
            update_data = {}

            # Map attributes
            if 'firstname' in attributes or 'lastname' in attributes:
                name = f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip()
                if name:
                    update_data['name'] = name

            if 'email' in attributes:
                update_data['login'] = attributes['email']

            if 'active' in attributes:
                update_data['active'] = attributes['active']

            if update_data:
                self._execute('res.users', 'write', [[user_id], update_data])

            # Update partner if needed
            if user.get('partner_id') and ('email' in attributes or 'phone' in attributes):
                partner_data = {}
                if 'email' in attributes:
                    partner_data['email'] = attributes['email']
                if 'phone' in attributes:
                    partner_data['phone'] = attributes['phone']

                if partner_data:
                    self._execute('res.partner', 'write', [[user['partner_id']], partner_data])

            # Update or create employee
            employee_id = await self._update_or_create_employee(user_id, user.get('partner_id'), attributes)

            logger.info("Odoo account updated", user_id=user_id)
            return {"id": user_id, "employee_id": employee_id, "status": "updated"}

        except Exception as e:
            logger.error("Failed to update Odoo account", error=str(e))
            raise

    async def _update_or_create_employee(
        self,
        user_id: int,
        partner_id: Optional[int],
        attributes: Dict[str, Any]
    ) -> Optional[int]:
        """Update existing employee or create new one."""
        try:
            # Check if employee exists for this user
            existing = self._execute(
                'hr.employee', 'search_read',
                [[('user_id', '=', user_id)]],
                {'fields': ['id']}
            )

            if existing:
                # Update existing employee
                employee_id = existing[0]['id']
                update_data = {}

                if 'firstname' in attributes or 'lastname' in attributes:
                    name = f"{attributes.get('firstname', '')} {attributes.get('lastname', '')}".strip()
                    if name:
                        update_data['name'] = name

                if attributes.get('email'):
                    update_data['work_email'] = attributes['email']
                if attributes.get('phone'):
                    update_data['work_phone'] = attributes['phone']
                if attributes.get('mobile'):
                    update_data['mobile_phone'] = attributes['mobile']
                if attributes.get('job_title') or attributes.get('title'):
                    update_data['job_title'] = attributes.get('job_title') or attributes.get('title')
                if attributes.get('department'):
                    dept_id = await self._get_or_create_department(attributes['department'])
                    if dept_id:
                        update_data['department_id'] = dept_id

                if update_data:
                    self._execute('hr.employee', 'write', [[employee_id], update_data])
                    logger.info("Odoo employee updated", employee_id=employee_id)

                return employee_id
            else:
                # Create new employee
                return await self._create_employee(user_id, partner_id or 0, attributes)

        except Exception as e:
            logger.warning("Failed to update/create employee", error=str(e))
            return None

    async def delete_account(self, account_id: str) -> bool:
        """Delete Odoo user account."""
        try:
            user = await self.get_account(account_id)
            if not user:
                logger.warning("Odoo user not found for deletion", login=account_id)
                return True

            # Deactivate instead of delete (Odoo best practice)
            self._execute('res.users', 'write', [[user['id']], {'active': False}])

            logger.info("Odoo account deactivated", user_id=user['id'])
            return True

        except Exception as e:
            logger.error("Failed to delete Odoo account", error=str(e))
            return False

    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get Odoo user account by login, name, or email."""
        try:
            if account_id.isdigit():
                domain = [('id', '=', int(account_id))]
            else:
                domain = [
                    '|', '|', '|',
                    ('login', 'ilike', account_id),
                    ('name', 'ilike', account_id),
                    ('email', 'ilike', account_id),
                    ('login', '=', account_id),
                ]

            users = self._execute(
                'res.users', 'search_read',
                [domain],
                {'fields': ['id', 'name', 'login', 'email', 'active', 'partner_id', 'groups_id']}
            )

            if users:
                user = users[0]
                return {
                    "id": user['id'],
                    "name": user['name'],
                    "login": user['login'],
                    "email": user.get('email'),
                    "active": user['active'],
                    "partner_id": user['partner_id'][0] if user.get('partner_id') else None,
                    "groups": user.get('groups_id', [])
                }
            return None

        except Exception as e:
            logger.error("Failed to get Odoo account", error=str(e))
            return None

    async def list_accounts(self) -> List[Dict[str, Any]]:
        """List all Odoo user accounts."""
        try:
            # Get all users without domain filter (empty list = all records)
            users = self._execute(
                'res.users', 'search_read',
                [[]],
                {'fields': ['id', 'name', 'login', 'active']}
            )

            return [
                {
                    "id": u['id'],
                    "name": u['name'],
                    "login": u['login'],
                    "active": u['active']
                }
                for u in users
            ]

        except Exception as e:
            logger.error("Failed to list Odoo accounts", error=str(e))
            return []

    async def disable_account(self, account_id: str) -> bool:
        """Disable Odoo user account."""
        try:
            result = await self.update_account(account_id, {"active": False})
            return result.get("status") == "updated"
        except Exception:
            return False

    async def enable_account(self, account_id: str) -> bool:
        """Enable Odoo user account."""
        try:
            result = await self.update_account(account_id, {"active": True})
            return result.get("status") == "updated"
        except Exception:
            return False

    async def add_to_group(self, account_id: str, group_id: str) -> bool:
        """Add user to Odoo group."""
        try:
            user = await self.get_account(account_id)
            if not user:
                raise Exception(f"User {account_id} not found")

            # Add group (4 = add relation)
            self._execute(
                'res.users', 'write',
                [[user['id']], {'groups_id': [(4, int(group_id))]}]
            )

            logger.info("User added to Odoo group", user_id=user['id'], group_id=group_id)
            return True

        except Exception as e:
            logger.error("Failed to add user to group", error=str(e))
            return False

    async def remove_from_group(self, account_id: str, group_id: str) -> bool:
        """Remove user from Odoo group."""
        try:
            user = await self.get_account(account_id)
            if not user:
                raise Exception(f"User {account_id} not found")

            # Remove group (3 = remove relation)
            self._execute(
                'res.users', 'write',
                [[user['id']], {'groups_id': [(3, int(group_id))]}]
            )

            logger.info("User removed from Odoo group", user_id=user['id'], group_id=group_id)
            return True

        except Exception as e:
            logger.error("Failed to remove user from group", error=str(e))
            return False

    async def get_groups(self, account_id: str) -> List[str]:
        """Get groups for Odoo user."""
        try:
            user = await self.get_account(account_id)
            if user:
                return [str(g) for g in user.get('groups', [])]
            return []
        except Exception:
            return []

    async def get_available_groups(self) -> List[Dict[str, Any]]:
        """Get all available Odoo groups."""
        try:
            groups = self._execute(
                'res.groups', 'search_read',
                [[]],
                {'fields': ['id', 'name', 'full_name']}
            )
            return groups
        except Exception as e:
            logger.error("Failed to get Odoo groups", error=str(e))
            return []

    async def list_employees(self) -> List[Dict[str, Any]]:
        """List all Odoo employees with their details."""
        try:
            employees = self._execute(
                'hr.employee', 'search_read',
                [[]],
                {'fields': [
                    'id', 'name', 'work_email', 'work_phone', 'mobile_phone',
                    'job_title', 'department_id', 'user_id', 'active'
                ]}
            )

            result = []
            for emp in employees:
                # Normalize department name for mapping
                dept_name = emp['department_id'][1] if emp.get('department_id') else None
                dept_normalized = self._normalize_department(dept_name) if dept_name else None

                result.append({
                    "id": emp['id'],
                    "name": emp['name'],
                    "email": emp.get('work_email'),
                    "phone": emp.get('work_phone'),
                    "mobile": emp.get('mobile_phone'),
                    "job_title": emp.get('job_title'),
                    "department": dept_name,
                    "department_normalized": dept_normalized,
                    "department_id": emp['department_id'][0] if emp.get('department_id') else None,
                    "user_id": emp['user_id'][0] if emp.get('user_id') else None,
                    "active": emp.get('active', True)
                })

            return result

        except Exception as e:
            logger.error("Failed to list Odoo employees", error=str(e))
            return []

    def _normalize_department(self, department: str) -> str:
        """Normalize department name for role/group mapping."""
        if not department:
            return "default"

        dept_lower = department.lower().strip()

        # Mapping of department variations to normalized names
        mappings = {
            # IT / Informatique variations
            "it": "it", "informatique": "it", "information technology": "it",
            "systemes d'information": "it", "si": "it", "dsi": "it",
            "developpement": "it", "development": "it",
            # HR / RH variations
            "hr": "hr", "rh": "hr", "human resources": "hr",
            "ressources humaines": "hr", "personnel": "hr",
            # Finance / Comptabilite variations
            "finance": "finance", "comptabilite": "finance",
            "accounting": "finance", "comptable": "finance",
            "tresorerie": "finance", "treasury": "finance",
            # Sales / Commercial variations
            "sales": "sales", "ventes": "sales", "commercial": "sales",
            "commerciaux": "sales", "business development": "sales",
            # Marketing / Communication variations
            "marketing": "marketing", "communication": "marketing",
            "publicite": "marketing", "advertising": "marketing",
            # Management / Direction variations
            "management": "management", "direction": "management",
            "executive": "management", "direction generale": "management",
            "administration": "management",
            # R&D / Recherche variations
            "r&d": "rd", "rd": "rd", "recherche": "rd", "research": "rd",
            "recherche et developpement": "rd", "innovation": "rd",
            # Support / Helpdesk variations
            "support": "support", "helpdesk": "support", "assistance": "support",
            "service client": "support", "customer service": "support",
            # Juridique / Legal variations
            "juridique": "juridique", "legal": "juridique",
            "contentieux": "juridique", "conformite": "juridique",
            # Production / Operations variations
            "production": "production", "operations": "production",
            "fabrication": "production", "manufacturing": "production",
            # Qualite variations
            "qualite": "qualite", "quality": "qualite",
            "controle qualite": "qualite", "qc": "qualite",
            # Logistique variations
            "logistique": "logistique", "logistics": "logistique",
            "supply chain": "logistique", "approvisionnement": "logistique",
            # Achats variations
            "achats": "achats", "purchasing": "achats", "procurement": "achats",
        }

        for key, value in mappings.items():
            if key in dept_lower:
                return value

        return dept_lower.replace(" ", "-")

    async def get_employee(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get a specific Odoo employee by ID."""
        try:
            employees = self._execute(
                'hr.employee', 'search_read',
                [[('id', '=', employee_id)]],
                {'fields': [
                    'id', 'name', 'work_email', 'work_phone', 'mobile_phone',
                    'job_title', 'department_id', 'user_id', 'active'
                ]}
            )

            if employees:
                emp = employees[0]
                result = {
                    "id": emp['id'],
                    "name": emp['name'],
                    "email": emp.get('work_email'),
                    "phone": emp.get('work_phone'),
                    "mobile": emp.get('mobile_phone'),
                    "job_title": emp.get('job_title'),
                    "department": emp['department_id'][1] if emp.get('department_id') else None,
                    "department_id": emp['department_id'][0] if emp.get('department_id') else None,
                    "user_id": emp['user_id'][0] if emp.get('user_id') else None,
                    "active": emp.get('active', True)
                }

                # Get contract info
                contract = await self.get_employee_contract(emp['id'])
                if contract:
                    result["contract"] = contract

                return result
            return None

        except Exception as e:
            logger.error("Failed to get Odoo employee", error=str(e), employee_id=employee_id)
            return None

    async def get_employee_contract(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Get active contract for an employee."""
        try:
            contracts = self._execute(
                'hr.contract', 'search_read',
                [[('employee_id', '=', employee_id), ('state', '=', 'open')]],
                {'fields': [
                    'id', 'name', 'date_start', 'date_end', 'state',
                    'contract_type_id', 'wage'
                ], 'limit': 1}
            )

            if contracts:
                contract = contracts[0]
                return {
                    "id": contract['id'],
                    "name": contract['name'],
                    "date_start": contract.get('date_start'),
                    "date_end": contract.get('date_end'),
                    "state": contract.get('state'),
                    "type": contract['contract_type_id'][1] if contract.get('contract_type_id') else None,
                    "type_id": contract['contract_type_id'][0] if contract.get('contract_type_id') else None,
                }
            return None

        except Exception as e:
            logger.warning("Failed to get employee contract", error=str(e), employee_id=employee_id)
            return None

    async def list_employees_with_contracts(self) -> List[Dict[str, Any]]:
        """List all employees with their contract information."""
        try:
            employees = await self.list_employees()

            # Get all active contracts
            contracts = self._execute(
                'hr.contract', 'search_read',
                [[('state', 'in', ['draft', 'open'])]],
                {'fields': [
                    'id', 'name', 'employee_id', 'date_start', 'date_end',
                    'state', 'contract_type_id'
                ]}
            )

            # Map contracts by employee_id
            contracts_by_employee = {}
            for contract in contracts:
                emp_id = contract['employee_id'][0] if contract.get('employee_id') else None
                if emp_id:
                    contracts_by_employee[emp_id] = {
                        "id": contract['id'],
                        "name": contract['name'],
                        "date_start": contract.get('date_start'),
                        "date_end": contract.get('date_end'),
                        "state": contract.get('state'),
                        "type": contract['contract_type_id'][1] if contract.get('contract_type_id') else None,
                    }

            # Merge contracts with employees
            for emp in employees:
                emp["contract"] = contracts_by_employee.get(emp["id"])

            return employees

        except Exception as e:
            logger.error("Failed to list employees with contracts", error=str(e))
            return []

    async def get_expired_contracts(self) -> List[Dict[str, Any]]:
        """Get employees with expired contracts (date_end < today)."""
        from datetime import date

        try:
            today = date.today().isoformat()

            # Find contracts that have expired
            expired_contracts = self._execute(
                'hr.contract', 'search_read',
                [[('date_end', '<', today), ('state', '=', 'open')]],
                {'fields': [
                    'id', 'name', 'employee_id', 'date_start', 'date_end',
                    'state', 'contract_type_id'
                ]}
            )

            result = []
            for contract in expired_contracts:
                emp_id = contract['employee_id'][0] if contract.get('employee_id') else None
                if emp_id:
                    emp = await self.get_employee(emp_id)
                    if emp:
                        result.append({
                            "employee": emp,
                            "contract": {
                                "id": contract['id'],
                                "name": contract['name'],
                                "date_start": contract.get('date_start'),
                                "date_end": contract.get('date_end'),
                                "type": contract['contract_type_id'][1] if contract.get('contract_type_id') else None,
                            }
                        })

            return result

        except Exception as e:
            logger.error("Failed to get expired contracts", error=str(e))
            return []

    async def get_expiring_contracts(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get employees with contracts expiring within X days."""
        from datetime import date, timedelta

        try:
            today = date.today()
            future_date = (today + timedelta(days=days)).isoformat()
            today_str = today.isoformat()

            # Find contracts expiring soon
            expiring_contracts = self._execute(
                'hr.contract', 'search_read',
                [[
                    ('date_end', '>=', today_str),
                    ('date_end', '<=', future_date),
                    ('state', '=', 'open')
                ]],
                {'fields': [
                    'id', 'name', 'employee_id', 'date_start', 'date_end',
                    'state', 'contract_type_id'
                ]}
            )

            result = []
            for contract in expiring_contracts:
                emp_id = contract['employee_id'][0] if contract.get('employee_id') else None
                if emp_id:
                    emp = await self.get_employee(emp_id)
                    if emp:
                        # Calculate days until expiration
                        end_date = date.fromisoformat(contract['date_end'])
                        days_remaining = (end_date - today).days

                        result.append({
                            "employee": emp,
                            "contract": {
                                "id": contract['id'],
                                "name": contract['name'],
                                "date_start": contract.get('date_start'),
                                "date_end": contract.get('date_end'),
                                "type": contract['contract_type_id'][1] if contract.get('contract_type_id') else None,
                                "days_remaining": days_remaining
                            }
                        })

            return result

        except Exception as e:
            logger.error("Failed to get expiring contracts", error=str(e))
            return []
