class DesmosTranslationError(Exception):
    def __init__(self, message: str, lineno: int | None = None, node_type: str | None = None):
        self.lineno = lineno
        self.node_type = node_type
        prefix = ""
        if lineno is not None:
            prefix = f"line {lineno}: "
        if node_type is not None:
            prefix += f"[{node_type}] "
        super().__init__(prefix + message)
