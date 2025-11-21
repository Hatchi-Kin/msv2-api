import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logger = logging.getLogger("uvicorn")


# ----------------------------------------------- #

### Logging Guidelines

## Logging Levels

## `logger.info()` - State Changes - Log when data is created, updated, or deleted:
##    - User registration, login, logout
##    - Creating/updating/deleting playlists
##    - Adding/removing favorites
##    - Any write operation that changes system state
## **Example:**
##  ```python
##  logger.info(f"User {user_id} created playlist: {name}")
##  logger.info(f"User {user_id} added track {track_id} to favorites")
##  ```

## `logger.debug()` - Operational Details - Log operational details useful for debugging:
##    - Query results (counts, IDs)
##    - Processing steps
##    - Successful reads with context
## **Example:**
##    ```python
##    logger.debug(f"Found {len(results)} similar tracks for track {track_id}")
##    logger.debug(f"Streaming track {track_id} (range: {start}-{end})")
##    ```

## `logger.warning()` - Recoverable Issues - Log when something unexpected happens but the request can continue:
##    - Failed authentication attempts
##    - Invalid tokens
##    - Requests for non-existent resources (before raising exception)
## **Example:**
##    ```python
##    logger.warning(f"Failed login attempt for: {email}")
##    logger.warning(f"Similarity search requested for non-existent track: {track_id}")
##    ```

## `logger.error()` - Errors - Log when something fails:
##    - Database errors (already handled in DatabaseClient)
##    - Storage errors (MinIO failures)
##    - Unexpected exceptions
## **Example:**
##    ```python
##    logger.error(f"Audio file not found in storage: {path}")
###    logger.error(f"MinIO error while streaming track {track_id}: {str(e)}")
##    ```

## What NOT to Log
## - **Don't log reads**: Simple GET operations that return data (too noisy)
## - **Don't log passwords or tokens**: Security risk
## - **Don't log in routers**: Keep routers thin, log in handlers/repositories
## - **Don't log every query**: Only log significant operations or errors

## # ❌ DON'T: Log sensitive data
## ```python
## # logger.info(f"User logged in with password: {password}")  # Security risk
## ```
