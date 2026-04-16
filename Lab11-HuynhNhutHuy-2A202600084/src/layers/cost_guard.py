from typing import Tuple, Dict

class CostGuardLayer:
    """
    7th Safety Layer: Cost Guard
    Tracks total token usage per user across the session. Blocks requests if projected cost exceeds budget.
    Prevents 'Denial of Wallet' attacks.
    """
    def __init__(self, max_tokens_per_user: int = 5000):
        self.max_tokens_per_user = max_tokens_per_user
        self.user_token_usage: Dict[str, int] = {}
        
    def add_usage(self, user_id: str, tokens: int):
        """Records tokens spent by the user."""
        if user_id not in self.user_token_usage:
            self.user_token_usage[user_id] = 0
        self.user_token_usage[user_id] += tokens
        
    def get_usage(self, user_id: str) -> int:
        return self.user_token_usage.get(user_id, 0)
        
    def check(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if the user has exceeded their token budget.
        Returns:
            (blocked: bool, reason: str)
        """
        current_usage = self.get_usage(user_id)
        if current_usage >= self.max_tokens_per_user:
            return True, f"Cost Guard block: You have exceeded your session budget of {self.max_tokens_per_user} tokens."
        return False, ""
