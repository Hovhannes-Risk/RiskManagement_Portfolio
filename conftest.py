"""Root conftest — ensures the repository root is on sys.path so that
`from risk_core import ...` resolves under plain `pytest` (not just
`python -m pytest`, which adds CWD automatically). Pytest inserts the
directory containing this conftest.py into sys.path during collection.
"""
