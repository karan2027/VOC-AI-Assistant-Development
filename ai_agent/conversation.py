from typing import List, Dict

class ConversationContext:
    def __init__(self, max_history: int = 15):
        self.messages: List[Dict[str, str]] = []
        self.max_history = max_history

    def add_user_message(self, text: str):
        self.messages.append({"role": "user", "content": text})
        self._trim_history()

    def add_assistant_message(self, text: str):
        self.messages.append({"role": "assistant", "content": text})
        self._trim_history()

    def get_messages(self, system_prompt: str) -> List[Dict[str, str]]:
        """Returns the system prompt combined with conversation history."""
        return [{"role": "system", "content": system_prompt}] + self.messages

    def clear(self):
        self.messages.clear()

    def _trim_history(self):
        """Keeps conversation history within limit to manage context length."""
        if len(self.messages) > self.max_history * 2: # 15 turns = 30 messages (user + assistant)
            # Remove early user/assistant pairs
            self.messages = self.messages[-self.max_history * 2:]
