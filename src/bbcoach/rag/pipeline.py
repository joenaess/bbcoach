import logging
import uuid
from bbcoach.scrapers.breakthrough_scraper import BreakthroughScraper
from bbcoach.rag.vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(self):
        self.scraper = BreakthroughScraper()
        self.vector_store = VectorStore()  # Default checks .vectordb

    def run_ingestion(self, start_urls, max_depth=1, max_pages=10):
        """
        Scrapes list of start_urls, follows links up to max_depth, and adds to vector store.
        """
        documents = []
        metadatas = []
        ids = []

        visited = set()
        queue = [(url, 0) for url in start_urls]
        pages_scraped = 0

        while queue and pages_scraped < max_pages:
            url, depth = queue.pop(0)
            if url in visited:
                continue
            visited.add(url)

            logger.info(f"Scraping {url} (Depth {depth})...")

            # Fetch raw html to get links first (if depth < max_depth)
            html = self.scraper.fetch_page(url)
            if not html:
                continue

            # Parse and add content
            data = self.scraper.parse_page(html, url)
            content = data.get("content", "")

            if content:
                # Chunking Logic
                # Simple paragraph splitting for now
                chunks = content.split("\n\n")
                current_chunk = ""
                chunk_size_limit = 1000

                for paragraph in chunks:
                    if len(current_chunk) + len(paragraph) < chunk_size_limit:
                        current_chunk += paragraph + "\n\n"
                    else:
                        if current_chunk.strip():
                            documents.append(current_chunk.strip())
                            metadatas.append(
                                {"url": url, "title": data.get("title", "Unknown")}
                            )
                            ids.append(str(uuid.uuid4()))
                        current_chunk = paragraph + "\n\n"

                if current_chunk.strip():
                    documents.append(current_chunk.strip())
                    metadatas.append(
                        {"url": url, "title": data.get("title", "Unknown")}
                    )
                    ids.append(str(uuid.uuid4()))

            pages_scraped += 1

            # Find links for next depth
            if depth < max_depth:
                links = self.scraper.get_links(html, url)
                for link in links:
                    if link not in visited:
                        queue.append((link, depth + 1))

        if documents:
            logger.info(f"Adding {len(documents)} chunks to vector store...")
            self.vector_store.add_documents(documents, metadatas, ids)
            return len(documents)

        return 0

    def query(self, text, n=3):
        return self.vector_store.query(text, n_results=n)

    def reset_db(self):
        self.vector_store.reset()
