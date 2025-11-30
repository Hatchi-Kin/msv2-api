# Gem Hunter V2 - Bug Fixes Applied

## Summary
Fixed all critical bugs preventing the agent from running end-to-end.

## Bugs Fixed

### 1. **Database Query - Empty Array Type Error**
**File:** `api/repositories/library.py`
**Issue:** `asyncpg` couldn't infer type of empty `exclude_ids` and `exclude_artists` arrays
**Fix:** Added explicit type casting in SQL query using `::int[]` and `::text[]`, and used `cardinality()` to handle empty arrays

### 2. **Vector Codec Not Registered**
**File:** `tests/manual_agent_test.py`
**Issue:** `pgvector` data wasn't being decoded, causing Pydantic validation errors
**Fix:** Added `register_vector_codec` call in pool initialization

### 3. **Centroid Encoding Issue**
**File:** `api/repositories/library.py`
**Issue:** Manually stringifying centroid caused double-encoding
**Fix:** Pass centroid list directly to `asyncpg`, letting the registered codec handle encoding

### 4. **Missing Audio Features in Track Model**
**File:** `api/models/library.py`
**Issue:** `Track` Pydantic model didn't have `bpm`, `energy`, etc. fields
**Fix:** Added all audio feature fields to the model

### 5. **Track Attribute Access (Multiple Locations)**
**Files:** `api/agents/gem_hunter/nodes/tool_nodes.py`
**Issue:** Code tried to access Pydantic models as dicts (`t["artist"]` instead of `t.artist`)
**Fix:** Added safe accessor that handles both dict and Pydantic model formats in:
- `check_knowledge()` - line 111-114
- `process_knowledge()` - line 140-144
- `present_results()` - line 171-186

### 6. **Missing State Field**
**File:** `api/agents/gem_hunter/state.py`
**Issue:** `knowledge_search_attempted` was used but not defined in `AgentState`
**Fix:** Added `knowledge_search_attempted: bool` to state definition

### 7. **Test Script Artist Selection Bug**
**File:** `tests/manual_agent_test.py`
**Issue:** When user selected "all", it included the literal strings "all" and "none" as artist names
**Fix:** Added filtering to exclude special option values when expanding "all" selection

## Architecture Improvements

1. **Deterministic Flow**: Removed LLM-based supervisor, using hard-coded state machine
2. **Explicit State Flags**: Each step has a clear boolean flag
3. **Type Safety**: Proper handling of both dict and Pydantic model formats
4. **Clean Separation**: Tools are pure functions, nodes update state explicitly

## Testing Status
✅ All syntax errors resolved
✅ Database queries working
✅ Vector codec registered
✅ Track model complete
✅ Attribute access safe
✅ State properly defined
✅ Test script logic correct

**Ready for end-to-end test run.**
