# Instrumentation documentation

This folder describes observable lifecycle events and the current MFAR instrumentation boundary.

- [Trace schema](MFAR_TRACE_SCHEMA.md)
- [Notebook instrumentation map](MFAR_NOTEBOOK_INSTRUMENTATION_MAP.md)
- [Real-backend instrumentation](MFAR_REAL_BACKEND_INSTRUMENTATION.md)
- [Retention-trace adapter](MFAR_RETENTION_TRACE_ADAPTER.md)
- [Retention audit methodology](MFAR_RETENTION_AUDIT.md)

Current evidence is retention-only unless a report explicitly documents a real, independently observed later-stage event. Do not infer compression, retrieval or answer failures from missing instrumentation.
