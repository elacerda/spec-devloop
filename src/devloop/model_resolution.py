"""Shared helpers for model/role resolution across backend commands."""

from __future__ import annotations

from typing import Any, Callable


def resolve_role_model_key(
    role_name: str,
    roles: Any,
    add_finding: Callable[[str, str, str | None, str | None], None],
    severity_error: str,
) -> str | None:
    """Resolve a role (with alias chasing) to a model key.

    Parameters
    ----------
    role_name
        Role name to resolve from the `roles` mapping.
    roles
        Raw `roles` section loaded from model config.
    add_finding
        Callback used to report validation findings while preserving each
        command's finding dataclass and rendering behavior.
    severity_error
        Error severity token used by the caller's finding model.

    Returns
    -------
    str | None
        Resolved model key when successful, else `None`.
    """

    if not isinstance(roles, dict) or role_name not in roles:
        add_finding(severity_error, f"unknown role: {role_name}", None, "role_unknown")
        return None

    visited: set[str] = set()
    current = role_name
    while True:
        if current in visited:
            add_finding(
                severity_error,
                f"role alias cycle detected at role: {current}",
                f"roles.{current}.same_as",
                "role_cycle",
            )
            return None
        visited.add(current)

        role_data = roles.get(current)
        if not isinstance(role_data, dict):
            add_finding(severity_error, f"invalid role entry: {current}", None, "role_invalid")
            return None

        model_name = role_data.get("model")
        if isinstance(model_name, str):
            return model_name

        same_as = role_data.get("same_as")
        if isinstance(same_as, str):
            if same_as not in roles:
                add_finding(
                    severity_error,
                    f"unknown role alias target: {same_as}",
                    f"roles.{current}.same_as",
                    "role_alias_missing",
                )
                return None
            current = same_as
            continue

        add_finding(
            severity_error,
            f"role does not resolve to a model: {current}",
            f"roles.{current}",
            "role_unresolved",
        )
        return None
