import logging
from typing import Any, Dict, List, Optional
import pymongo
from pymongo.collection import Collection
from pymongo.database import Database
from ..config import settings

logger = logging.getLogger(__name__)

class MongoDBService:
    """
    Primary Persistent Database Service using MongoDB.
    Manages connections, collections, indices, and article/user documents.
    Connects to the remote MongoDB instance specified in settings.MONGODB_URI.
    Gracefully falls back to an in-memory mongomock instance if the external database is unreachable.
    """
    def __init__(self, uri: Optional[str] = None, db_name: Optional[str] = None):
        self.uri = uri or settings.MONGODB_URI
        self.db_name = db_name or settings.MONGODB_DB_NAME
        self.client: Any = None
        self.db: Database = None
        self.is_mock: bool = False
        self._connect()
        self._ensure_indices()

    def _connect(self):
        """Attempts connection to live MongoDB using settings.MONGODB_URI; falls back to mongomock if unavailable."""
        timeout_ms = getattr(settings, "MONGODB_SERVER_SELECTION_TIMEOUT_MS", 10000)
        allow_invalid_certs = getattr(settings, "MONGODB_TLS_ALLOW_INVALID_CERTS", True)

        client_kwargs: Dict[str, Any] = {
            "serverSelectionTimeoutMS": timeout_ms,
            "connectTimeoutMS": timeout_ms,
            "socketTimeoutMS": timeout_ms
        }

        # Handle TLS/SSL options for cloud endpoints (e.g. firestore.goog)
        if "tls=true" in self.uri.lower() or "ssl=true" in self.uri.lower() or "firestore.goog" in self.uri:
            client_kwargs["tlsAllowInvalidCertificates"] = allow_invalid_certs

        try:
            logger.info(f"Connecting to MongoDB instance at {self._sanitized_uri(self.uri)}...")
            live_client = pymongo.MongoClient(self.uri, **client_kwargs)
            # Verify connectivity with ping command
            live_client.admin.command('ping')
            self.client = live_client

            # Detect default database name from URI path if present (e.g., nzz-flexread-db)
            try:
                default_db = live_client.get_default_database()
                if default_db is not None and default_db.name:
                    self.db = default_db
                    self.db_name = default_db.name
                else:
                    self.db = self.client[self.db_name]
            except Exception:
                self.db = self.client[self.db_name]

            self.is_mock = False
            logger.info(f"Connected to primary MongoDB database '{self.db_name}' at {self._sanitized_uri(self.uri)}")
        except Exception as e:
            logger.warning(
                f"Could not connect to external MongoDB at {self._sanitized_uri(self.uri)} ({e}). "
                "Initializing in-memory mongomock database to preserve seamless offline execution."
            )
            try:
                import mongomock
                self.client = mongomock.MongoClient()
                self.db = self.client[self.db_name]
                self.is_mock = True
                logger.info(f"Initialized in-memory MongoDB mock for database '{self.db_name}'.")
            except Exception as mock_err:
                logger.error(f"Failed to initialize mongomock: {mock_err}")
                raise

    def _sanitized_uri(self, uri: str) -> str:
        """Hides credentials when logging connection URIs."""
        if "@" in uri:
            prefix = uri.split("://")[0]
            host_part = uri.split("@")[-1]
            return f"{prefix}://***:***@{host_part}"
        return uri

    def _ensure_indices(self):
        """Creates indexes on articles and users collections when supported."""
        # Cloud Firestore MongoDB compatibility layer manages indexes via GCP; skip client-side create_index to avoid blocking
        if "firestore.goog" in self.uri:
            logger.info("Connected to Firestore MongoDB endpoint; index creation is managed through Google Cloud.")
            return

        try:
            articles_col = self.get_collection("articles")
            articles_col.create_index("id", unique=True)
            articles_col.create_index("nzz_id")
            articles_col.create_index("section")
            articles_col.create_index("date")
            articles_col.create_index("preprocessing.tone")
            articles_col.create_index("preprocessing.article_length")

            users_col = self.get_collection("users")
            users_col.create_index("user_id", unique=True)
            logger.debug("MongoDB indexes verified successfully.")
        except Exception as e:
            logger.debug(f"Index creation notice (non-fatal): {e}")

    def get_collection(self, collection_name: str) -> Collection:
        """Returns the specified collection."""
        return self.db[collection_name]

    # --------------------------------------------------------------------------
    # Article Operations
    # --------------------------------------------------------------------------

    def save_article(self, article_dict: Dict[str, Any]) -> str:
        """Persists or updates an article document in MongoDB."""
        col = self.get_collection("articles")
        article_id = article_dict.get("id") or article_dict.get("nzz_id")
        if not article_id:
            raise ValueError("Article document must contain an 'id' or 'nzz_id' field")

        clean_id = str(article_id).replace(".", "").lower()
        if not clean_id.startswith("ld"):
            clean_id = f"ld{clean_id}"

        doc_to_save = dict(article_dict)
        doc_to_save["id"] = clean_id
        if "nzz_id" not in doc_to_save:
            doc_to_save["nzz_id"] = f"ld.{clean_id[2:]}"
        doc_to_save.pop("_id", None)

        dotted_id = f"ld.{clean_id[2:]}"
        query = {
            "$or": [
                {"id": clean_id},
                {"nzz_id": dotted_id},
                {"nzz_id": article_id},
                {"_id": dotted_id},
                {"_id": article_id}
            ]
        }

        col.update_one(query, {"$set": doc_to_save}, upsert=True)
        return clean_id

    def get_article(self, article_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves an article by ID from MongoDB.
        Flexible matcher for clean id ('ld10021904'), dotted id ('ld.10021904'), or numeric id.
        """
        col = self.get_collection("articles")
        clean_id = str(article_id).replace(".", "").lower()
        dotted_id = f"ld.{clean_id[2:]}" if clean_id.startswith("ld") else f"ld.{clean_id}"

        query = {
            "$or": [
                {"id": clean_id},
                {"id": article_id},
                {"nzz_id": dotted_id},
                {"nzz_id": article_id},
                {"_id": dotted_id},
                {"_id": article_id},
                {"document_id": dotted_id},
                {"document_id": article_id}
            ]
        }

        doc = col.find_one(query)
        if doc:
            doc.pop("_id", None)
            if "id" not in doc or not doc["id"]:
                raw_id = doc.get("nzz_id") or doc.get("document_id") or article_id
                doc["id"] = str(raw_id).replace(".", "").lower()
            if "raw_content" not in doc or not doc["raw_content"]:
                doc["raw_content"] = doc.get("body_text", "")
        return doc

    def list_articles(
        self,
        section: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "date",
        descending: bool = True
    ) -> List[Dict[str, Any]]:
        """Queries articles with optional section filter, sort, and pagination."""
        col = self.get_collection("articles")
        query: Dict[str, Any] = {}
        if section:
            query["section"] = {"$regex": f"^{section}$", "$options": "i"}

        sort_field = "published_at" if sort_by == "date" else sort_by
        sort_dir = pymongo.DESCENDING if descending else pymongo.ASCENDING

        cursor = col.find(query).sort(sort_field, sort_dir).skip(offset).limit(limit)
        results = []
        for doc in cursor:
            doc.pop("_id", None)
            if "id" not in doc or not doc["id"]:
                raw_id = doc.get("nzz_id") or doc.get("document_id") or "unknown"
                doc["id"] = str(raw_id).replace(".", "").lower()
            if "raw_content" not in doc or not doc["raw_content"]:
                doc["raw_content"] = doc.get("body_text", "")
            results.append(doc)
        return results

    def count_articles(self, section: Optional[str] = None) -> int:
        """Returns count of articles in MongoDB."""
        col = self.get_collection("articles")
        query = {"section": {"$regex": f"^{section}$", "$options": "i"}} if section else {}
        return col.count_documents(query)

    def update_article_preprocessing(self, article_id: str, preprocessing: Dict[str, Any]) -> bool:
        """Updates the preprocessed metadata for a specific article in MongoDB."""
        col = self.get_collection("articles")
        clean_id = str(article_id).replace(".", "").lower()
        dotted_id = f"ld.{clean_id[2:]}" if clean_id.startswith("ld") else f"ld.{clean_id}"

        query = {
            "$or": [
                {"id": clean_id},
                {"id": article_id},
                {"nzz_id": dotted_id},
                {"nzz_id": article_id},
                {"_id": dotted_id},
                {"_id": article_id}
            ]
        }

        update_payload = {
            "$set": {
                "preprocessing": preprocessing,
                "word_count": preprocessing.get("word_count", 0),
                "reading_time_seconds": preprocessing.get("reading_time", 0),
                "reading_time_minutes": preprocessing.get("reading_time_minutes", 0.0),
                "tone": preprocessing.get("tone"),
                "article_length": preprocessing.get("article_length")
            }
        }
        result = col.update_one(query, update_payload)
        return result.matched_count > 0

    def get_unprocessed_articles(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieves articles from MongoDB that haven't been preprocessed yet
        (where preprocessing is None, missing, or has no main_points).
        """
        col = self.get_collection("articles")
        results = []
        for doc in col.find():
            prep = doc.get("preprocessing")
            is_unprocessed = False
            if not prep or not isinstance(prep, dict):
                is_unprocessed = True
            elif not prep.get("main_points"):
                is_unprocessed = True

            if is_unprocessed:
                doc.pop("_id", None)
                if "id" not in doc or not doc["id"]:
                    raw_id = doc.get("nzz_id") or doc.get("document_id") or "unknown"
                    doc["id"] = str(raw_id).replace(".", "").lower()
                if "raw_content" not in doc or not doc["raw_content"]:
                    doc["raw_content"] = doc.get("body_text", "")
                results.append(doc)
                if len(results) >= limit:
                    break
        return results

    # --------------------------------------------------------------------------
    # User Operations
    # --------------------------------------------------------------------------

    def save_user(self, user_dict: Dict[str, Any]) -> str:
        """Persists or updates a user document in MongoDB."""
        col = self.get_collection("users")
        user_id = user_dict.get("user_id")
        if not user_id:
            raise ValueError("User document must contain a 'user_id' field")

        doc_to_save = dict(user_dict)
        doc_to_save.pop("_id", None)

        col.update_one(
            {"user_id": user_id},
            {"$set": doc_to_save},
            upsert=True
        )
        return user_id

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a user document by user_id from MongoDB."""
        col = self.get_collection("users")
        doc = col.find_one({"user_id": user_id})
        if doc:
            doc.pop("_id", None)
        return doc

    def list_users(self) -> List[Dict[str, Any]]:
        """Lists all users in MongoDB."""
        col = self.get_collection("users")
        results = []
        for doc in col.find():
            doc.pop("_id", None)
            results.append(doc)
        return results

    def ping(self) -> Dict[str, Any]:
        """Health check for MongoDB."""
        if self.is_mock:
            return {"connected": True, "mode": "in-memory-mock", "database": self.db_name}
        try:
            self.client.admin.command('ping')
            return {
                "connected": True,
                "mode": "mongodb-live",
                "database": self.db_name,
                "uri": self._sanitized_uri(self.uri)
            }
        except Exception as e:
            return {"connected": False, "error": str(e), "database": self.db_name}

# Global singleton instance
mongodb_service = MongoDBService()
