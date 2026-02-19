"""
Client Qdrant pour la recherche semantique dans les logs d'audit.
Utilise le conteneur gateway-qdrant sur le port 6333.
Indexe les logs d'audit pour une recherche textuelle et semantique.
"""
from typing import List, Dict, Any, Optional
import hashlib
import struct
import uuid
import structlog

from app.core.config import settings

logger = structlog.get_logger()

COLLECTION_NAME = "audit_logs"
VECTOR_SIZE = 128


def _text_to_vector(text: str) -> List[float]:
    """
    Genere un vecteur deterministe a partir du texte.
    Utilise un hash-based approach pour creer un vecteur de dimension fixe.
    Peut etre remplace par un modele d'embedding ML (ex: all-MiniLM-L6-v2).
    """
    vector = []
    # Generer des sous-hash pour remplir le vecteur
    for i in range(VECTOR_SIZE):
        h = hashlib.sha256(f"{text}_{i}".encode()).digest()
        val = struct.unpack('f', h[:4])[0]
        # Normaliser entre -1 et 1
        val = max(-1.0, min(1.0, val / 1e10))
        vector.append(val)

    # Normaliser le vecteur (L2 norm)
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0:
        vector = [v / norm for v in vector]

    return vector


class QdrantStore:
    """Client Qdrant pour l'indexation et la recherche d'audit logs."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._client = None

    async def connect(self) -> bool:
        """Etablit la connexion a Qdrant et cree la collection si necessaire."""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            self._client = QdrantClient(
                host=settings.QDRANT_HOST,
                port=settings.QDRANT_PORT,
                timeout=5
            )

            # Creer la collection si elle n'existe pas
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]

            if COLLECTION_NAME not in collection_names:
                self._client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=VectorParams(
                        size=VECTOR_SIZE,
                        distance=Distance.COSINE
                    )
                )
                logger.info("Qdrant collection created", collection=COLLECTION_NAME)

            logger.info("Qdrant connected", host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
            return True

        except Exception as e:
            logger.warning("Qdrant connection failed, semantic search disabled", error=str(e))
            self._client = None
            return False

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    async def health_check(self) -> dict:
        """Verifie l'etat de Qdrant."""
        if not self._client:
            return {"status": "disconnected"}
        try:
            info = self._client.get_collection(COLLECTION_NAME)
            return {
                "status": "healthy",
                "points_count": info.points_count,
                "collection": COLLECTION_NAME
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def index_audit_log(self, log_entry: Dict[str, Any]) -> bool:
        """
        Indexe une entree d'audit dans Qdrant pour la recherche semantique.

        Args:
            log_entry: Dictionnaire avec les champs: event_type, action, account_id,
                       target_system, actor, severity, details, created_at
        """
        if not self._client:
            return False

        try:
            from qdrant_client.models import PointStruct

            # Construire le texte pour l'embedding
            summary_parts = [
                log_entry.get("event_type", ""),
                log_entry.get("action", ""),
                log_entry.get("account_id", ""),
                log_entry.get("target_system", ""),
                log_entry.get("actor", ""),
            ]
            # Ajouter des details si disponibles
            details = log_entry.get("details", {})
            if isinstance(details, dict):
                for k, v in details.items():
                    if isinstance(v, str):
                        summary_parts.append(v)

            summary = " ".join(filter(None, summary_parts))
            vector = _text_to_vector(summary)

            point_id = str(uuid.uuid4())

            self._client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    PointStruct(
                        id=point_id,
                        vector=vector,
                        payload={
                            "event_type": log_entry.get("event_type", ""),
                            "action": log_entry.get("action", ""),
                            "account_id": log_entry.get("account_id", ""),
                            "target_system": log_entry.get("target_system", ""),
                            "actor": log_entry.get("actor", ""),
                            "severity": log_entry.get("severity", "info"),
                            "created_at": log_entry.get("created_at", ""),
                            "summary": summary,
                            "db_id": log_entry.get("db_id", "")
                        }
                    )
                ]
            )
            return True

        except Exception as e:
            logger.error("Failed to index audit log in Qdrant", error=str(e))
            return False

    async def search_logs(
        self,
        query: str,
        limit: int = 20,
        event_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Recherche semantique dans les logs d'audit.

        Args:
            query: Texte de recherche
            limit: Nombre max de resultats
            event_type: Filtre optionnel par type d'evenement
            severity: Filtre optionnel par severite

        Returns:
            Liste de logs correspondants avec score de pertinence
        """
        if not self._client:
            return []

        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue

            query_vector = _text_to_vector(query)

            # Construire les filtres
            conditions = []
            if event_type:
                conditions.append(
                    FieldCondition(key="event_type", match=MatchValue(value=event_type))
                )
            if severity:
                conditions.append(
                    FieldCondition(key="severity", match=MatchValue(value=severity))
                )

            query_filter = Filter(must=conditions) if conditions else None

            results = self._client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter
            )

            return [
                {
                    "score": hit.score,
                    "event_type": hit.payload.get("event_type", ""),
                    "action": hit.payload.get("action", ""),
                    "account_id": hit.payload.get("account_id", ""),
                    "target_system": hit.payload.get("target_system", ""),
                    "actor": hit.payload.get("actor", ""),
                    "severity": hit.payload.get("severity", ""),
                    "created_at": hit.payload.get("created_at", ""),
                    "summary": hit.payload.get("summary", ""),
                    "db_id": hit.payload.get("db_id", "")
                }
                for hit in results
            ]

        except Exception as e:
            logger.error("Qdrant search failed", error=str(e))
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """Statistiques de la collection Qdrant."""
        if not self._client:
            return {"status": "disconnected", "points_count": 0}

        try:
            info = self._client.get_collection(COLLECTION_NAME)
            return {
                "status": "healthy",
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}


# Instance globale
qdrant_store = QdrantStore()
