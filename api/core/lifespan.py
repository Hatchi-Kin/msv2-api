from contextlib import asynccontextmanager

from fastapi import FastAPI

from api.connectors.postgres_connector import PostgresConnector


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_connector = PostgresConnector()
    await db_connector.connect()
    app.state.db_connector = db_connector
    print("Postgres Connector Connected")

    yield

    # Shutdown
    await app.state.db_connector.disconnect()
    print("Postgres Connector Disconnected")
