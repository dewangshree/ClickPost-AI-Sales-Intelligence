import json
import logging
import time

from groq import Groq

from config import GROQ_API_KEY
from models import SignalExtractionResult

logger = logging.getLogger(__name__)


class SignalService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"

        with open("prompts/signal_prompt.txt", "r") as f:
            self.system_prompt = f.read()

    def extract_signals(
        self,
        company: str,
        search_results: str,
    ) -> SignalExtractionResult:

        if not search_results:
            return SignalExtractionResult(
                company=company,
                signals=[],
                confidence=0.0,
                reasoning="No search results",
                sources=[],
            )

        prompt = f"""Company: {company}

Search Results:
{search_results}
"""

        for attempt in range(3):
            try:
                chat_completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self.system_prompt,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )

                response_content = chat_completion.choices[0].message.content
                data = json.loads(response_content)

                # Small delay to avoid Groq rate limiting
                time.sleep(10)

                return SignalExtractionResult(**data)

            except Exception as e:
                logger.warning(
                    f"Groq extraction attempt {attempt + 1} failed for {company}: {e}"
                )

                if attempt == 2:
                    logger.error(
                        f"Failed to extract signals for {company} after 3 attempts."
                    )

                    return SignalExtractionResult(
                        company=company,
                        signals=[],
                        confidence=0.0,
                        reasoning=f"Error: {e}",
                        sources=[],
                    )

                wait_time = 10 * (attempt + 1)

                logger.info(f"Waiting {wait_time} seconds before retry...")

                time.sleep(wait_time)