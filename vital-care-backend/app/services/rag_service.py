import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_SEED_FILE = Path(__file__).parent.parent / "data" / "trusted_sources_seed.json"


class RAGService:
    """
    Retrieval-Augmented Generation service backed by trusted medical sources.

    Currently returns placeholder context from the seed file.
    TODO: Integrate ChromaDB or FAISS for real vector search when documents are ingested.
    TODO: Scrape and index MedlinePlus, CDC, WHO, NIH, NHS, SAMHSA content.
    """

    def __init__(self):
        self._sources: list[dict] = []
        self._load_seed()

    def _load_seed(self):
        try:
            with open(_SEED_FILE, "r") as f:
                self._sources = json.load(f)
        except Exception as e:
            logger.warning("Could not load trusted sources seed: %s", e)
            self._sources = []

    def search_trusted_sources(self, query: str) -> list[dict]:
        """
        Search trusted sources for relevant snippets.
        Returns a list of source dicts with name, url, and matching snippets.

        TODO: Replace with real vector similarity search using ChromaDB/FAISS.
        """
        # Placeholder: return all sources with their sample snippets
        results = []
        query_lower = query.lower()
        for source in self._sources:
            matched_snippets = [
                snippet for snippet in source.get("sample_snippets", [])
                if any(word in snippet.lower() for word in query_lower.split())
            ]
            if matched_snippets or len(results) < 2:
                results.append({
                    "name": source["name"],
                    "url": source["url"],
                    "organization": source["organization"],
                    "snippets": matched_snippets or source.get("sample_snippets", [])[:1],
                })
        return results[:3]

    def get_context_for_query(self, query: str) -> str:
        """
        Return a formatted context string from trusted sources for LLM augmentation.

        TODO: Replace with real retrieved document chunks from vector store.
        """
        sources = self.search_trusted_sources(query)
        if not sources:
            return "No trusted source context available for this query."

        lines = ["Trusted medical source context:"]
        for s in sources:
            lines.append(f"\n[{s['name']} — {s['url']}]")
            for snippet in s["snippets"]:
                lines.append(f"  - {snippet}")
        return "\n".join(lines)


_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
