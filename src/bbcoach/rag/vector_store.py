import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer
import logging
import os

logger = logging.getLogger(__name__)


class VectorStore:
    def __init__(
        self, persist_directory=".vectordb", collection_name="basketball_knowledge"
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = chromadb.PersistentClient(path=persist_directory)

        # Use sentence-transformers for embeddings
        # 'all-MiniLM-L6-v2' is a good balance of speed and quality
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

        self.collection = self.client.get_or_create_collection(
            name=collection_name, embedding_function=self.embedding_fn
        )
        logger.info(
            f"VectorStore initialized at {persist_directory} with collection '{collection_name}'"
        )

    def add_documents(self, documents, metadatas, ids):
        """
        Adds documents to the vector store.

        Args:
            documents (list[str]): List of document texts.
            metadatas (list[dict]): List of metadata dictionaries.
            ids (list[str]): List of unique IDs for the documents.
        """
        if not documents:
            return

        try:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(f"Added {len(documents)} documents to vector store.")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")

    def query(self, query_text, n_results=5):
        """
        Queries the vector store.

        Args:
            query_text (str): The query text.
            n_results (int): Number of results to return.

        Returns:
            dict: The query results (documents, metadatas, distances).
        """
        try:
            results = self.collection.query(
                query_texts=[query_text], n_results=n_results
            )
            return results
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return None

    def count(self):
        return self.collection.count()

    def reset(self):
        """Deletes and recreates the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, embedding_function=self.embedding_fn
        )
