"""Injector tools — dependency-aware tools using RunContext."""

from agno.run.base import RunContext
from agno.tools import tool


@tool
def get_config(run_context: RunContext, key: str) -> str:
    """Look up an application configuration value by key.

    Args:
        key: The configuration key to look up (e.g., 'region', 'max_retries').
    """
    deps = run_context.dependencies or {}
    config = deps.get("config", {})
    if key in config:
        return f"config['{key}'] = {config[key]}"
    available = ", ".join(config.keys())
    return f"Key '{key}' not found. Available keys: {available}"


@tool
def check_feature_flag(run_context: RunContext, flag_name: str) -> str:
    """Check whether a feature flag is enabled or disabled.

    Args:
        flag_name: The feature flag name (e.g., 'dark_mode', 'beta_features').
    """
    deps = run_context.dependencies or {}
    flags = deps.get("feature_flags", {})
    enabled = flags.get(flag_name)
    if enabled is None:
        available = ", ".join(flags.keys())
        return f"Feature flag '{flag_name}' not found. Available flags: {available}"
    status = "ENABLED" if enabled else "DISABLED"
    return f"Feature flag '{flag_name}' is {status}"


@tool
def get_user_preference(run_context: RunContext, preference: str) -> str:
    """Get a user preference value from injected dependencies.

    Args:
        preference: The preference key (e.g., 'theme', 'language', 'timezone').
    """
    deps = run_context.dependencies or {}
    prefs = deps.get("user_preferences", {})
    if preference in prefs:
        return f"user_preferences['{preference}'] = {prefs[preference]}"
    available = ", ".join(prefs.keys())
    return f"Preference '{preference}' not found. Available: {available}"
