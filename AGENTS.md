# Repository Guidelines

## Project Structure & Module Organization

`laylay.py` is the composition root; keep domain behavior out of it. New capabilities belong in `mente_laylay/`: `especialistas/` owns domain runtimes and the capability map, `cognicao/` interprets turns, `memoria_mental/` owns shared context and learning, `autonomia/` routes and executes actions, `percepcao/` observes input, and `integracao/` wires components. Clients live in `cliente/`, including the Xbox Game Bar widget. Persistent user state belongs in `memoria/`; never commit credentials from environment or Tuya/Gmail data. Tests mirror behavior in `tests/`.

## Build, Test, and Development Commands

- `python laylay.py` starts the assistant from source.
- `.\.venv314\Scripts\python.exe -m pytest -q` runs the complete suite with the project environment.
- `.\.venv314\Scripts\python.exe -m pytest tests\test_area_transferencia_inteligente.py -q` runs one module.
- `powershell -ExecutionPolicy Bypass -File .\empacotamento\build_portatil.ps1` builds the portable distribution.

## Mandatory Capability Integration Contract

Before implementing a capability, inventory existing shared services and reuse them. Do not create local substitutes for mechanisms already present. A capability is not complete until tests prove all applicable pillars:

1. **Context:** reads and publishes only necessary state through the shared mind.
2. **Memory:** distinguishes temporary context from durable, sourced memory.
3. **Learning:** sends acceptance, refusal, correction, repetition, and qualified silence to the shared learning engine.
4. **Natural language:** reuses the canonical turn/confirmation interpreters; domain code adds entities and verbs, not private yes/no phrase lists.
5. **Continuity:** supports natural references and repetition through the canonical pending-action channel.
6. **Safety:** separates discussion, suggestion, authorization, execution, and observed confirmation.
7. **Diagnostics:** reports health, failures, and verified results to the existing observability and capability maps.
8. **Capability awareness:** registers the capability in the live capability catalog so Laylay knows what it can do, how to invoke it naturally, what authorization it needs, what evidence confirms success, and what its limits are. The relevant entry must reach the LLM through contextual retrieval without bloating the permanent personality prompt. Laylay must answer natural questions about the capability truthfully and must never claim access that is unavailable at runtime.
9. **Cooperative orchestration:** when a useful result depends on more than one capability or data source, publishes the relationship to the canonical cooperation board and reuses the existing cooperative coordinator. Each participating capability keeps its own validation, authorization and confirmation; cooperation must not create a shortcut around an executor, duplicate private state or turn perception into permission. Tests must cover the combined path and prove that a partial failure cannot be reported as full success.

Add unit tests, a real composition-path regression test, a negative safety test, a cooperative-path test when the ninth pillar applies, and a capability-awareness test covering the live catalog and natural questions about the new ability. Mocks must not replace the shared component whose integration is being verified. Update `ROADMAP_NOVAS_HABILIDADES.md` only after those tests pass.

## Coding and Testing Conventions

Use Portuguese domain names consistently with surrounding code, type hints on new public APIs, and small runtime factories named `criar_*_runtime`. Preserve user changes in the dirty worktree. Use `apply_patch` for edits. Pytest is the project test runner; every bug fix needs a regression reproducing the user’s wording, plus nearby natural variants.
