class Message(dict):
    """Represents a message in the agent's conversation history.

    Inherits from dict for compatibility with LLM API message format,
    while also supporting attribute-style access.
    """

    def __init__(self, role, content):
        super().__init__(role=role, content=content)
        self.role = role
        self.content = content

    def __repr__(self):
        return f"Message(role='{self.role}', content='{self.content[:50]}...')" if len(self.content) > 50 else f"Message(role='{self.role}', content='{self.content}')"
