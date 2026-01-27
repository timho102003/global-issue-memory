# GIM Development Roadmap

This document tracks the implementation progress of Global Issue Memory (GIM).

## MVP Timeline: 12 Weeks

---

## Phase 1: Foundation (Weeks 1-4) - **IN PROGRESS**

### Week 1-2: Core Infrastructure **COMPLETED**

| Task | Status | Notes |
|------|--------|-------|
| Project setup & structure | Done | Python 3.12+, uv package manager |
| Pydantic data models | Done | MasterIssue, ChildIssue, FixBundle, Analytics, Environment |
| Configuration management | Done | pydantic-settings with .env support |
| MCP server skeleton | Done | stdio-based MCP server |
| Basic tool definitions | Done | 5 MCP tools defined |

### Week 3-4: Sanitization Pipeline **COMPLETED**

| Task | Status | Notes |
|------|--------|-------|
| Secret detection (regex) | Done | 20+ patterns for API keys, tokens |
| Secret detection (entropy) | Done | Shannon entropy analysis |
| PII scrubber | Done | Email, paths, names, IPs |
| MRE synthesizer | Done | Minimal reproducible example extraction |
| LLM sanitizer | Done | Google Gemini integration |
| Pipeline orchestrator | Done | Two-layer architecture with confidence scoring |
| Unit tests | Done | Comprehensive test coverage |

---

## Phase 2: Database & Search (Weeks 5-8) - **NEXT**

### Week 5-6: Database Setup

| Task | Status | Notes |
|------|--------|-------|
| Supabase schema design | Pending | Tables: master_issues, child_issues, usage_events |
| Run migrations | Pending | Via Supabase MCP |
| CRUD operations | Partial | Client implemented, needs schema |
| Qdrant collection setup | Done | Auto-creates on startup |
| Embedding storage | Done | Multi-vector per issue |

### Week 5-6: Remote MCP Transport & Authentication

| Task | Status | Notes |
|------|--------|-------|
| Migrate to FastMCP | Pending | Replace low-level Server with FastMCP |
| Streamable HTTP transport | Pending | Endpoint: `POST /mcp` |
| OAuth2.0 integration | Pending | Bearer token authentication |
| Dual transport support | Pending | stdio (local) + HTTP (remote) |
| Auth settings configuration | Pending | issuer_url, scopes, JWKS validation |
| Transport security | Pending | HTTPS, CORS, DNS rebinding protection |
| Rate limiting | Pending | Per client_id limits |
| Integration tests | Pending | Test both transports with auth |

### Week 7-8: Canonicalization Engine

| Task | Status | Notes |
|------|--------|-------|
| Root cause taxonomy | Pending | See PRD Appendix B |
| Issue clustering | Pending | Vector similarity-based |
| Merge suggestion logic | Pending | Threshold: >0.85 similarity |
| Confidence score updates | Pending | Based on confirmations |

---

## Phase 3: Search & Ranking (Weeks 9-10)

### Week 9: Search Implementation

| Task | Status | Notes |
|------|--------|-------|
| Multi-vector search | Pending | error_signature + root_cause + fix_summary |
| Filter by model/provider | Pending | Qdrant payload filters |
| Filter by environment | Pending | Language, framework, OS |
| Result ranking algorithm | Pending | similarity * confidence * recency |

### Week 10: Tool Completion

| Task | Status | Notes |
|------|--------|-------|
| Complete gim_search_issues | Partial | Needs DB integration |
| Complete gim_get_fix_bundle | Partial | Needs DB integration |
| Complete gim_submit_issue | Partial | Needs full pipeline |
| Complete gim_confirm_fix | Partial | Needs analytics storage |
| Complete gim_report_usage | Partial | Needs event logging |
| End-to-end integration tests | Pending | With real services |

---

## Phase 4: Dashboard & Polish (Weeks 11-12)

### Week 11: Dashboard UI

| Task | Status | Notes |
|------|--------|-------|
| Dashboard design | Pending | Read-only web interface |
| Issue browsing | Pending | List, search, filter |
| Issue detail view | Pending | Fix bundle, trust signals |
| Usage analytics display | Pending | Charts, metrics |

### Week 12: Final Polish

| Task | Status | Notes |
|------|--------|-------|
| Performance optimization | Pending | Caching, batch operations |
| Rate limiting | Pending | Per-session limits |
| Error handling improvements | Pending | Better error messages |
| Documentation finalization | Pending | Final review |
| Security audit | Pending | OWASP checklist |

---

## Post-MVP (Future)

| Feature | Priority | Notes |
|---------|----------|-------|
| Private workspaces | High | Team-specific issues |
| Sandbox execution | Medium | Verify fixes in containers |
| IDE plugins | Medium | Cursor, VS Code extensions |
| Community moderation | Low | Voting, flagging |
| Automated fix application | Low | AI applies fix directly |

---

## Current Focus

**Phase 1 Complete - Moving to Phase 2**

Next immediate tasks:
1. **Migrate to FastMCP with dual transport support**
   - Refactor server.py to use FastMCP
   - Add streamable HTTP transport (`POST /mcp`)
   - Implement OAuth2.0 authentication for remote access
2. Create Supabase database schema
3. Run migrations
4. Wire up tool implementations to database
5. Begin canonicalization engine

---

## Milestones

| Milestone | Target | Status |
|-----------|--------|--------|
| Core models complete | Week 2 | **Done** |
| Sanitization pipeline complete | Week 4 | **Done** |
| Dual transport (stdio + HTTP) | Week 6 | Pending |
| OAuth2.0 authentication | Week 6 | Pending |
| Database operational | Week 6 | Pending |
| Search working E2E | Week 10 | Pending |
| Dashboard MVP | Week 12 | Pending |
| Public beta | Week 12 | Pending |

---

## Success Metrics (MVP)

| Metric | Target | Current |
|--------|--------|---------|
| Master issues created | 100+ | 0 |
| Fix resolution rate | >70% | N/A |
| Search latency p95 | <500ms | N/A |
| Sanitization confidence | >95% | N/A |
| Test coverage | >80% | ~75% |

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Sanitization misses secrets | High | Two-layer approach + manual review option |
| Low adoption | Medium | Focus on high-quality fixes over quantity |
| Vector search latency | Medium | Qdrant tuning, caching |
| LLM costs | Medium | Efficient batching, caching embeddings |

---

## References

- [Product Requirements Document](PRD_Global_Issue_Memory.md)
- [Architecture Guide](ARCHITECTURE.md)
- [Setup Guide](SETUP.md)
- [API Reference](API.md)

---

*Last updated: 2026-01-27*
