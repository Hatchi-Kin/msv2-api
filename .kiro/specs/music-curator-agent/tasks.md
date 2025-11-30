# Music Curator Agent - Implementation Tasks

## Phase 1: Core State & Graph Structure

- [x] 1. Define AgentState TypedDict
  - Create state.py with complete AgentState definition
  - Include all fields from design: playlist_id, flags, data, supervisor control
  - Add Track TypedDict with all required fields
  - _Requirements: 7.1, 7.2_

- [x] 2. Create graph structure
  - Implement build_agent_graph() in graph.py
  - Add all 6 nodes (supervisor + 5 tools)
  - Define START → supervisor edge
  - Define supervisor conditional routing
  - Define tool → supervisor edges
  - Set interrupt_after for analyze_playlist and check_knowledge
  - _Requirements: 8.1-8.5, 9.1_

## Phase 2: Supervisor Node

- [x] 3. Implement supervisor node
  - Create supervisor_node.py
  - Implement execute() method that takes AgentState
  - Build LLM prompt with current state
  - Call LLM with structured output (SupervisorDecision)
  - Return next_action, reasoning, parameters
  - _Requirements: 9.2, 9.3_

- [x] 4. Add loop prevention
  - Track last 3 actions in action_history
  - Detect if same action called 3x in a row
  - Force different action or present_results
  - Add max iteration check (10 iterations)
  - _Requirements: 9.5_

- [x] 5. Add supervisor decision validation
  - Ensure next_action is valid tool name or END
  - Log reasoning to thought_process
  - Increment iteration_count
  - _Requirements: 5.1, 9.4_

## Phase 3: Tool Nodes

- [x] 6. Implement analyze_playlist tool
  - Create tool_nodes.py with ToolNodes class
  - Implement analyze_playlist() method
  - Fetch playlist stats from DB
  - Generate description with LLM
  - Create 4 vibe options
  - Return ui_state with message and options
  - Set playlist_analyzed = True
  - _Requirements: 1.1, 1.2, 8.1_

- [x] 7. Implement search_tracks tool
  - Implement search_tracks() method
  - Get playlist centroid from DB
  - Apply vibe-based constraints
  - Implement adaptive strategy based on iteration
  - Call vector search with constraints and exclusions
  - Return candidate_tracks
  - _Requirements: 2.1, 8.2_

- [x] 8. Implement evaluate_results tool
  - Implement evaluate_results() method
  - Calculate quantity_score (candidates / 50)
  - Calculate quality_score (1 - avg_distance)
  - Calculate diversity_score (unique_artists / 20)
  - Compute overall_score
  - Return quality_assessment with recommendation
  - _Requirements: 2.3, 4.3_

- [x] 9. Implement check_knowledge tool
  - Implement check_knowledge() method
  - Extract unique artists from top 20 candidates
  - Create options list with artists + "None" + "All"
  - Return ui_state with message and options
  - Set knowledge_checked = True
  - _Requirements: 3.1, 8.3_

- [x] 10. Implement present_results tool
  - Implement present_results() method
  - Filter candidates by known_artists
  - Select top 5 tracks (prioritize unknown)
  - Generate pitch for each track with LLM
  - Generate overall justification with LLM
  - Return ui_state with cards
  - Set results_presented = True
  - _Requirements: 4.1, 4.4, 5.2, 5.3, 8.4_

## Phase 4: Handler & API Integration

- [x] 11. Update agent handler
  - Modify handlers/agent.py
  - Update start_recommendation_handler to use new graph
  - Initialize state with all required fields
  - Handle LLM failures gracefully
  - _Requirements: 6.2, 7.1_

- [x] 12. Update resume handler
  - Handle "set_vibe" action
  - Handle "submit_knowledge" action
  - Handle special values: "none", "all"
  - Update state correctly before resuming
  - _Requirements: 1.3, 3.2, 7.4_

- [x] 13. Add error handling
  - Catch and log all exceptions
  - Return user-friendly error messages
  - Handle empty playlist case
  - Handle no results case
  - Handle LLM service failures
  - _Requirements: 6.1-6.5_

## Phase 5: Testing

- [x] 14. Write unit tests for supervisor
  - Test decision logic with various states
  - Test loop prevention mechanism
  - Test max iteration enforcement
  - _Requirements: 9.5_

- [x] 15. Write unit tests for tools
  - Test analyze_playlist with mock DB
  - Test search_tracks with different vibes
  - Test evaluate_results with various candidates
  - Test check_knowledge with different artist lists
  - Test present_results with known/unknown artists
  - _Requirements: 8.1-8.5_

- [x] 16. Write integration tests
  - Test full flow: analyze → search → evaluate → check → present
  - Test re-search flow: check (all known) → search → present
  - Test poor quality flow: search → evaluate → search → present
  - _Requirements: 2.2, 2.4, 3.4_

- [ ]* 17. Write property tests
  - **Property 1:** Supervisor never calls same tool 3x in a row
  - **Validates: Requirements 9.5**

- [ ]* 18. Write property tests
  - **Property 2:** User never interrupted more than 2 times
  - **Validates: Requirements 10.1-10.3**

- [ ]* 19. Write property tests
  - **Property 3:** Agent always reaches END within 10 iterations
  - **Validates: Requirements 9.5**

- [ ]* 20. Write property tests
  - **Property 4:** Final playlist has 1-5 tracks
  - **Validates: Requirements 4.1**

- [ ]* 21. Write property tests
  - **Property 5:** If user knows none, final tracks have 0 known artists
  - **Validates: Requirements 3.5**

## Phase 6: Documentation

- [x] 22. Update API documentation
  - Document new state structure
  - Document supervisor decision process
  - Update frontend integration guide
  - Add examples for each flow
  - _Requirements: 5.1-5.5_

## Checkpoint

- [x] 23. Manual testing
  - Test with real playlist
  - Verify 2 interrupts max
  - Verify supervisor makes good decisions
  - Verify loop prevention works
  - Verify graceful error handling
