# Current Chatbot Demo Agent

This directory is a reference agent project shape for the current chatbot demo.
It shows how a concrete agent can follow the platform scaffold while remaining
separate from framework packages.

The graph files are placeholders. They document future behavior only:

```text
input -> safety -> intent routing -> RAG/tool/direct branch -> answer formatting
```

No real Qdrant retrieval, real production API call, real LLM call, or runtime
registration is implemented here.

