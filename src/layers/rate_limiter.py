from collections import defaultdict, deque
import time
from typing import Tuple

class RateLimiterLayer:
    """
    Prevents abuse by limiting the number of requests a user can make within a time window.
    """
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.user_windows = defaultdict(deque)

    def check(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if the user has exceeded the rate limit.
        Returns:
            (blocked: bool, reason: str)
            blocked is True if rate limit is exceeded.
        """
        now = time.time()
        window = self.user_windows[user_id]
        
        # Remove expired timestamps from the front of the deque
        while window and window[0] < now - self.window_seconds:
            window.popleft()
            
        if len(window) >= self.max_requests:
            wait_time = int(self.window_seconds - (now - window[0]))
            return True, f"Rate limit exceeded. Please wait {wait_time} seconds before trying again."
            
        window.append(now)
        return False, ""
