from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

PROMPT = {
    "id": "pmpt_6a4c03086f2081939978a699ca50ad7d0fe8ed8ab07bf32a",
    "version": "3"
}


class OpenAIService:
    def __init__(self):
        self.client = OpenAI()
        self.model = "gpt-5.4-nano"

    def generate_response(self, messages: list) -> str:
        response = self.client.responses.create(
            model=self.model,
            prompt=PROMPT,
            input=messages
        )

        return response.output_text


openai_service = OpenAIService()