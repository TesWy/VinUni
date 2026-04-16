from openai import AsyncOpenAI
from typing import Tuple
from src.core.config import OPENAI_API_KEY

class ToxicityClassifierLayer:
    """
    6th Safety Layer: Toxicity Classifier using OpenAI Moderation API.
    Flags and blocks inputs containing hate speech, harassment, sexual content, self-harm, or violence.
    """
    def __init__(self):
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        
    async def check(self, user_input: str) -> Tuple[bool, str]:
        """
        Check user input against OpenAI's Moderation endpoint.
        Returns:
            (blocked: bool, block_reason_or_message: str)
        """
        try:
            # The Moderation API is free and specifically designed for safety layers
            response = await self.client.moderations.create(input=user_input)
            result = response.results[0]
            
            if result.flagged:
                # Extract which specific harmful categories triggered the block
                categories_dict = result.categories.model_dump()
                flagged_categories = [cat for cat, is_flagged in categories_dict.items() if is_flagged]
                
                reason = f"Toxicity Classifier block. Harmful content detected: {', '.join(flagged_categories)}"
                return True, reason
                
            return False, ""
        except Exception as e:
            # Fail-open strategy if the moderation API is down, so legitimate users aren't locked out
            # Alternatively could fail-closed, but typically fallback to other layers
            print(f"[ToxicityClassifier] Warning: Evaluation failed - {str(e)}")
            return False, ""
