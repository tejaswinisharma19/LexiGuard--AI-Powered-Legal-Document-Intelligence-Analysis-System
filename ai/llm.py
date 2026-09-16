from google import genai

from config import Config


class LexiGuardLLM:
    """
    Gemini-powered language model interface for LexiGuard.
    """

    def __init__(self):
        if not Config.GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY is not configured."
            )

        self.client = genai.Client(
            api_key=Config.GEMINI_API_KEY
        )

    def generate(self, prompt):
        """
        Generate a response from the Gemini model.
        """

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text