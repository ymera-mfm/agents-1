# CONFIGURATION TEMPLATE FOR EXPANSIONS

expansion_config = {
    "plugin_settings": {
        "enabled": True,
        "auto_load": True,
        "plugin_directory": "plugins/"
    },
    "api_settings": {
        "current_version": "v1",
        "supported_versions": ["v1"],
        "deprecation_warnings": True
    },
    "feature_flags": {
        "experimental_features": False,
        "beta_features": False
    },
    "expansion_modules": {
        "analytics": {"enabled": False, "config": {}},
        "reporting": {"enabled": False, "config": {}},
        "integrations": {"enabled": False, "config": {}}
    }
}
