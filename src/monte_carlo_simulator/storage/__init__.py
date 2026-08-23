"""Local persistence for the per-desk installation."""

from monte_carlo_simulator.storage.database import (
    connect,
    data_directory,
    database_path,
    session_scope,
)
from monte_carlo_simulator.storage.projects import (
    ProjectError,
    StoredRegister,
    StoredRun,
    delete_register,
    get_register,
    get_run,
    list_registers,
    list_runs,
    save_register,
    save_run,
)

__all__ = [
    "ProjectError",
    "StoredRegister",
    "StoredRun",
    "connect",
    "data_directory",
    "database_path",
    "delete_register",
    "get_register",
    "get_run",
    "list_registers",
    "list_runs",
    "save_register",
    "save_run",
    "session_scope",
]
