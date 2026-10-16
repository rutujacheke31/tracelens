
# TraceLens

TraceLens is a multimodal GenAI bug-investigation agent that analyzes screenshots, application logs, source code, and technical documentation to identify likely root causes and recommend fixes.

## Planned Workflow

1. Accept a bug screenshot and application logs.
2. Analyze the visual and textual evidence.
3. Retrieve relevant source code and documentation using RAG.
4. Coordinate the investigation through a LangGraph agent workflow.
5. Generate a root-cause analysis and proposed fix.
6. Use Playwright to reproduce the bug and verify the correction.
7. Store investigation history and results in PostgreSQL.

## Technology Stack

- Python and FastAPI
- LangGraph and multimodal language models
- React and TypeScript
- PostgreSQL
- Playwright
- Docker

## Status

Active development.