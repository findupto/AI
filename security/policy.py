class Policy:
    def __init__(self, config: dict):
        self.security = config.get("security", {})

    def network_allowed(self) -> bool:
        return bool(self.security.get("allow_network", False))

    def shell_allowed(self) -> bool:
        return bool(self.security.get("allow_shell", False))

    def tool_confirmation_required(self) -> bool:
        return bool(self.security.get("require_confirmation_for_tools", True))

    def python_timeout(self) -> int:
        return int(self.security.get("python_timeout_seconds", 8))
