import re
import unicodedata
from typing import Tuple
from src.core.config import ALLOWED_TOPICS, BLOCKED_TOPICS

class InputGuardLayer:
    """
    Blocks malicious inputs and off-topic questions before they reach the LLM.
    """
    def __init__(self):
        self.injection_patterns = [
            # Basic injection
            r"ignore (all )?(previous|above|prior) instructions",
            r"disregard (all )?(previous|your) (instructions|rules|guidelines)",
            r"forget (everything|all instructions|what you were told)",
            
            # Jailbreak / role override
            r"you are now",
            r"pretend (you are|to be)",
            r"act as (a |an )?(unrestricted|different|new|another)",
            r"from now on you (will|must|should|are)",
            r"your (new |real )?personality is",
            
            # System prompt extraction
            r"(reveal|show|print|output|display|give me|tell me).{0,30}(system prompt|instructions|config)",
            r"(system prompt|initial prompt|original instructions)",
            r"translate.{0,30}(instructions|prompt|rules).{0,30}(to|into)",
            r"output.{0,30}(as |in )?(json|yaml|xml|base64|markdown)",
            
            # Completion attack
            r"(fill in|complete).{0,40}(password|api.?key|secret|token|credential)",
            r"(admin password|api.?key|connection string)\s*[:=]\s*(__|___|\?\?\?)",
            
            # Authority / roleplay
            r"(CISO|CTO|CEO|auditor|compliance).{0,50}(require|request|demand|need)",
            r"ticket (id|#|number).{0,20}(VSEC|JIRA|IA\d|DEV-CONF)",
            r"(security audit|compliance check).{0,50}(provide|output|reveal|share)",
            
            # Encoding tricks
            r"(base64|rot13|ascii|hex|unicode).{0,30}(decode|encode|convert)",
            r"(decode|encode|convert).{0,40}(base64|rot13|ascii|hex|unicode)",
            r"character.{0,20}by.{0,20}character",
            
            # Hypothetical bypass
            r"(hypothetically|if you (were|could|had to)).{0,50}(reveal|show|tell|share)",
            r"(fictional|story|scenario).{0,50}(system prompt|password|credentials)",
            r"write a (story|narrative).{0,50}(AI assistant|chatbot).{0,50}(reads|reveals|says)",
            
            # Confirmation / side-channel
            r"(confirm|verify).{0,40}(password|api.?key|token|secret|admin)",
            r"i (already know|have) the .{0,15}(password|api.?key|secret|token).{0,10}(is|was|=)",
            
            # DAN / unrestricted mode
            r"\bDAN\b",
            r"developer mode",
            r"jailbreak",
            r"no (restrictions|limits|rules|guidelines)",
            
            # --- Multi-lingual Injections (Vietnamese) ---
            r"(bỏ qua|phớt lờ|quên).*(hướng dẫn|câu lệnh|quy tắc|chỉ thị)",
            r"(giả vờ|đóng vai|hãy là).*(không bị giới hạn|admin|quản trị)",
            r"(tiết lộ|cho tôi xem|xuất|bật mí).*(mật khẩu|hệ thống|mã nguồn|api|prompt)",
        ]
        
        self.max_length = 500  # Token/Character overflow limit
        
        # Zero-width characters often used to evade regex
        self.invisible_chars = re.compile(r'[\u200b\u200c\u200d\u200e\u200f\ufeff\u202a-\u202e]')

    def sanitize_input(self, text: str) -> str:
        """Loại bỏ các zero-width characters thường được dùng để tàng hình trước regex."""
        # Clean invisible shapes
        clean_text = self.invisible_chars.sub("", text)
        return clean_text

    def check_length_and_structure(self, text: str) -> Tuple[bool, str]:
        """
        Phòng thủ tràn token (Buffer Overflow / Denial of Wallet) & Ký tự bất thường.
        """
        # Tràn token / quá dài
        if len(text) > self.max_length:
            return True, f"Request too long. Maximum allowed length is {self.max_length} characters."
            
        # Ký tự trống hoàn toàn
        if not text.strip():
            return True, "Empty request."
            
        # Ngăn XSS/Code Execution Injection
        if re.search(r'(<script|javascript:|eval\(|exec\(|\bdrop table\b)', text, re.IGNORECASE):
            return True, "Invalid characters or code execution attempt detected."
            
        # % Ký tự đặc biệt quá cao (tránh spam ký hiệu để phá vỡ NLP Parser)
        alphanumeric = sum(c.isalnum() or c.isspace() for c in text)
        if len(text) > 10 and alphanumeric / len(text) < 0.4:
             return True, "Input contains excessive special characters."
             
        return False, ""

    def _remove_diacritics(self, text: str) -> str:
        """Chuyển 'lãi suất' → 'lai suat' để so sánh không phân biệt dấu."""
        nfkd = unicodedata.normalize('NFKD', text)
        return ''.join(c for c in nfkd if not unicodedata.combining(c))

    def detect_injection(self, text: str) -> bool:
        """Kiểm tra xem input có chứa pattern injection không."""
        for pattern in self.injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def is_off_topic(self, text: str) -> bool:
        """Kiểm tra xem input có vi phạm content policy không (blocked topic / off-topic)."""
        input_lower = text.lower()
        input_normalized = self._remove_diacritics(input_lower)

        # 1. Blocked topics
        for topic in BLOCKED_TOPICS:
            if topic in input_lower:
                return True

        # 2. Allowed topics
        for topic in ALLOWED_TOPICS:
            topic_normalized = self._remove_diacritics(topic.lower())
            if topic in input_lower or topic_normalized in input_normalized:
                return False

        return True

    def check(self, user_input: str) -> Tuple[bool, str]:
        """
        Check guardrails on user input.
        Returns:
            (blocked: bool, block_reason_or_message: str)
        """
        # 1. Structural & Safety Length checks
        is_bad_structure, reason = self.check_length_and_structure(user_input)
        if is_bad_structure:
            return True, f"Validation Error: {reason}"
            
        # 2. Sanitize invisible characters
        sanitized_input = self.sanitize_input(user_input)

        # 3. Injection Checks
        if self.detect_injection(sanitized_input):
            return True, "⚠️ Prompt injection attack detected. Request blocked."

        # 4. Off-topic Checks
        if self.is_off_topic(sanitized_input):
            return True, "I can only assist with banking-related topics such as accounts, loans, transfers, and savings."

        return False, ""
