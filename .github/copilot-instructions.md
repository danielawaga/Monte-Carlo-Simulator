# Copilot instructions

- Preserve the layered architecture (models/distributions/engine/analysis/io/visualization/application).
- Do not put business logic directly in the React interface or the HTTP adapter.
- Use NumPy for vectorized calculations.
- Avoid Python loops for 10,000 simulations when vectorization is possible.
- Add tests for each newly implemented distribution.
- Never add confidential data to the repository.
- Preserve reproducibility with `numpy.random.Generator` and explicit seeds.
- Document important mathematical decisions.
- Keep API compatibility when adding advanced features.
