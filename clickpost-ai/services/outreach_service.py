import json
import logging
import time

from groq import Groq

from config import GROQ_API_KEY
from models import RankedAccount, Outreach

logger = logging.getLogger(__name__)


class OutreachService:
    def __init__(self):
        self.client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"

        with open("prompts/outreach_prompt.txt", "r") as f:
            self.system_prompt = f.read()

    def generate_outreach(self, account: RankedAccount) -> Outreach:

        if not account.signals:
            return Outreach(
                company=account.company,
                linkedin_message="No signals found.",
                email_message="No signals found.",
            )

        signals_text = "\n".join(
            [
                f"- {signal.signal_type}: {signal.description}"
                for signal in account.signals
            ]
        )

        prompt = f"""Company: {account.company}
Industry: {account.industry}

Signals:
{signals_text}
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
                    temperature=0.7,
                )

                response_content = chat_completion.choices[0].message.content
                data = json.loads(response_content)

                # Delay between successful Groq requests
                time.sleep(10)

                return Outreach(
                    company=account.company,
                    linkedin_message=data.get("linkedin_message", ""),
                    email_message=data.get("email_message", ""),
                )

            except Exception as e:
                logger.warning(
                    f"Groq outreach attempt {attempt + 1} failed for {account.company}: {e}"
                )

                if attempt == 2:
                    logger.error(
                        f"Failed to generate outreach for {account.company} after 3 attempts."
                    )

                    return Outreach(
                        company=account.company,
                        linkedin_message="",
                        email_message="",
                    )

                wait_time = 10 * (attempt + 1)

                logger.info(f"Waiting {wait_time} seconds before retry...")

                time.sleep(wait_time)

        return Outreach(
            company=account.company,
            linkedin_message="",
            email_message="",
        )