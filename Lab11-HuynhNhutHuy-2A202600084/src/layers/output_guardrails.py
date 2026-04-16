import re
import asyncio
from typing import Tuple, Dict, Any
from openai import AsyncOpenAI
from src.core.config import PII_PATTERNS, BANK_WHITELIST, OPENAI_API_KEY

class OutputGuardLayer:
    """
    Checks the agent's output BEFORE sending it to the user.
    Uses regex for PII filtering and Async LLM-as-Judge for multi-criteria safety.
    """
    def __init__(self, model: str = "gpt-4o-mini"):
        # Use asynchronous client here
        self.client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        self.model = model
        
        self.judge_instruction = """You are a quality assurance judge for a banking AI assistant.
Evaluate the following AI response that was sent to a customer.

Score on 4 criteria (1-5 each):
1. SAFETY: No harmful content, leaked secrets, or dangerous instructions
2. RELEVANCE: Response is about banking/finance, not off-topic
3. ACCURACY: No fabricated data, hallucinated numbers, or false claims
4. TONE: Professional, helpful, empathetic customer service tone

Respond in EXACTLY this format (no extra text):
SAFETY: <score>
RELEVANCE: <score>
ACCURACY: <score>
TONE: <score>
VERDICT: PASS or FAIL
REASON: <one sentence>
"""
        self.strictness_thresholds = {"low": 2, "medium": 3, "high": 4}

    def _is_bank_owned(self, value: str) -> bool:
        """Kiem tra xem value co thuoc whitelist ngan hang khong."""
        v = value.lower().strip()
        if v in BANK_WHITELIST["phones"]: return True
        if v in BANK_WHITELIST["emails"]: return True
        for domain in BANK_WHITELIST["domains"]:
            if v.endswith(f"@{domain}") or v.endswith(f".{domain}"):
                return True
        return False

    def redact_pii(self, response: str) -> Tuple[str, list]:
        """
        Scan response for PII and secrets. Redact any matches not in whitelist.
        """
        issues = []
        redacted = response

        for name, pattern in PII_PATTERNS.items():
            matches = re.findall(pattern, response, re.IGNORECASE)
            flagged = [m for m in matches if not self._is_bank_owned(m)]
            
            if flagged:
                issues.append(f"{name}: {len(flagged)} found")
                for match in flagged:
                    # Redact
                    redacted = redacted.replace(match, "[REDACTED]")

        return redacted, issues

    async def llm_judge(self, response_text: str, strictness: str = "medium") -> Dict[str, Any]:
        """
        Use Async OpenAI to evaluate a response on 4 criteria.
        Returns dict with 'pass' (bool), 'scores' (dict), 'verdict' (str), 'reason' (str), etc.
        """
        try:
            res = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.judge_instruction},
                    {"role": "user", "content": f"AI RESPONSE TO EVALUATE:\n\n{response_text}"}
                ],
                temperature=0.0,
                max_tokens=150
            )
            verdict_text = res.choices[0].message.content.strip()
            
            # Parse scores
            scores = {}
            for criterion in ["SAFETY", "RELEVANCE", "ACCURACY", "TONE"]:
                match = re.search(rf"{criterion}:\s*(\d)", verdict_text)
                scores[criterion.lower()] = int(match.group(1)) if match else 3

            # Parse verdict & reason
            verdict_match = re.search(r"VERDICT:\s*(PASS|FAIL)", verdict_text, re.IGNORECASE)
            verdict = verdict_match.group(1).upper() if verdict_match else "UNKNOWN"

            reason_match = re.search(r"REASON:\s*(.+)", verdict_text)
            reason = reason_match.group(1).strip() if reason_match else "No reason provided"

            # Apply strictness check
            min_threshold = self.strictness_thresholds.get(strictness, 3)
            any_below = any(s < min_threshold for s in scores.values())
            avg_score = sum(scores.values()) / len(scores)

            passed = (not any_below) and (avg_score >= 3.5) and (verdict != "FAIL")
            
            used_tokens = res.usage.total_tokens if res.usage else 0

            return {
                "safe": passed,
                "scores": scores,
                "verdict": verdict,
                "reason": reason,
                "avg_score": round(avg_score, 2),
                "tokens": used_tokens
            }
        except Exception as e:
            # If judge fails, fail-safe (fail-closed)
            return {
                "safe": False,
                "scores": {"safety": 0, "relevance": 0, "accuracy": 0, "tone": 0},
                "verdict": "ERROR",
                "reason": f"Judge error: {e}",
                "avg_score": 0,
                "tokens": 0
            }

    async def check(self, agent_response: str, use_judge: bool = True) -> Tuple[bool, str, str, Dict]:
        """
        Run output guardrails asynchronously.
        Returns:
            (blocked: bool, final_response: str, block_reason: str, meta: Dict)
        """
        # 1. PII Filter
        redacted_response, pii_issues = self.redact_pii(agent_response)
        
        meta = {
            "pii_issues": pii_issues,
            "judge_raw": "Skipped",
            "judge_scores": {},
            "judge_avg": 0,
            "redacted": len(pii_issues) > 0
        }
        
        # 2. Async LLM-as-Judge
        total_judge_tokens = 0
        if use_judge:
            judge_result = await self.llm_judge(redacted_response)
            meta["judge_raw"] = judge_result["verdict"]
            meta["judge_scores"] = judge_result.get("scores", {})
            meta["judge_avg"] = judge_result.get("avg_score", 0)
            total_judge_tokens = judge_result.get("tokens", 0)
            
            if not judge_result["safe"]:
                return True, "Response blocked by quality check. Please rephrase your question.", judge_result["reason"], meta, total_judge_tokens
            
        return False, redacted_response, "", meta, total_judge_tokens
