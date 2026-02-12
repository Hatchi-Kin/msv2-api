from typing import Dict, List

import asyncpg

from api.repositories.database import DatabaseClient


class DiscoveryRepository:
    """Repository for discovery-related operations, like fetching centroids."""

    def __init__(self, pool: asyncpg.Pool):
        self.db = DatabaseClient(pool)
        self.table = "discovery_centroids"

    async def get_all_centroids(self) -> Dict[str, List[float]]:
        """Fetch all calculated centroids into a dictionary for quick math."""
        query = f"SELECT name, embedding FROM {self.table};"
        rows = await self.db.fetch(query)

        # Convert pgvector strings/lists into float lists
        centroids = {}
        for row in rows:
            emb = row["embedding"]
            if isinstance(emb, str):
                emb = [float(x) for x in emb.strip("[]").split(",")]
            centroids[row["name"]] = emb

        return centroids
