from abc import ABC, abstractmethod


class BaseLLMService(ABC):
    @abstractmethod
    def generate_text(self, prompt: str) -> str:
        """Send a prompt and return the generated text response."""
        ...
