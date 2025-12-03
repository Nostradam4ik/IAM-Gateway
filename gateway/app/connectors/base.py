"""
Interface de base pour les connecteurs
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import structlog

logger = structlog.get_logger()


class BaseConnector(ABC):
    """
    Interface abstraite pour tous les connecteurs.

    Chaque connecteur doit implementer ces methodes
    pour garantir une interface uniforme.
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self._connected = False

    @abstractmethod
    async def test_connection(self) -> bool:
        """Teste la connexion au systeme cible."""
        pass

    @abstractmethod
    async def create_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Cree un nouveau compte.

        Args:
            account_id: Identifiant unique du compte
            attributes: Attributs du compte

        Returns:
            Dict avec les details du compte cree
        """
        pass

    @abstractmethod
    async def update_account(
        self,
        account_id: str,
        attributes: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Met a jour un compte existant.

        Args:
            account_id: Identifiant du compte
            attributes: Attributs a mettre a jour

        Returns:
            Dict avec les details du compte mis a jour
        """
        pass

    @abstractmethod
    async def delete_account(self, account_id: str) -> bool:
        """
        Supprime un compte.

        Args:
            account_id: Identifiant du compte

        Returns:
            True si suppression reussie
        """
        pass

    @abstractmethod
    async def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """
        Recupere les details d'un compte.

        Args:
            account_id: Identifiant du compte

        Returns:
            Dict des attributs ou None si non trouve
        """
        pass

    @abstractmethod
    async def list_accounts(self) -> List[Dict[str, Any]]:
        """
        Liste tous les comptes du systeme.

        Returns:
            Liste des comptes
        """
        pass

    async def disable_account(self, account_id: str) -> bool:
        """
        Desactive un compte.

        Implementation par defaut: suppression.
        """
        return await self.delete_account(account_id)

    async def enable_account(self, account_id: str) -> bool:
        """
        Reactive un compte.

        Implementation par defaut: non supportee.
        """
        raise NotImplementedError(f"{self.name} does not support enable_account")

    async def add_to_group(
        self,
        account_id: str,
        group_id: str
    ) -> bool:
        """Ajoute un compte a un groupe."""
        raise NotImplementedError(f"{self.name} does not support add_to_group")

    async def remove_from_group(
        self,
        account_id: str,
        group_id: str
    ) -> bool:
        """Retire un compte d'un groupe."""
        raise NotImplementedError(f"{self.name} does not support remove_from_group")

    async def get_groups(self, account_id: str) -> List[str]:
        """Recupere les groupes d'un compte."""
        return []
