from src.core.audit import AuditLogger
from src.layers.rate_limiter import RateLimiterLayer
from src.layers.cost_guard import CostGuardLayer
from src.layers.input_guardrails import InputGuardLayer
from src.layers.toxicity_classifier import ToxicityClassifierLayer
from src.layers.output_guardrails import OutputGuardLayer
from src.agent.chatbot import AsyncBankingAgent

class DefensePipeline:
    """
    Advanced async Defense-in-depth pipeline.
    Flow: RateLimiter -> Fast Regex Input Guardrails -> Toxicity Classifier -> LLM Agent (Async) -> LLM-as-Judge & PII Filter (Async) -> Audit
    """
    def __init__(self):
        self.rate_limiter = RateLimiterLayer(max_requests=10, window_seconds=60)
        self.cost_guard = CostGuardLayer(max_tokens_per_user=5000)
        self.input_guard = InputGuardLayer()
        self.toxicity_classifier = ToxicityClassifierLayer()
        self.output_guard = OutputGuardLayer()
        self.audit_logger = AuditLogger()
        self.agent = AsyncBankingAgent()

    async def process(self, user_id: str, user_input: str) -> str:
        """
        Processes a user request through the complete async defense pipeline.
        """
        self.audit_logger.start_request(user_id=user_id, input_text=user_input)

        # 1. Rate Limiter Layer
        blocked, reason = self.rate_limiter.check(user_id)
        if blocked:
            self.audit_logger.record_layer_block(layer_name="RateLimiter", reason=reason)
            self.audit_logger.finish_request()
            return reason
        self.audit_logger.record_layer_pass("RateLimiter")

        # 1.5. Cost Guard Layer (Token Budget Check)
        blocked, reason = self.cost_guard.check(user_id)
        if blocked:
            self.audit_logger.record_layer_block(layer_name="CostGuard", reason=reason)
            self.audit_logger.finish_request()
            return "Transaction declined. System interaction budget exceeded."
        self.audit_logger.record_layer_pass("CostGuard")

        # 2. Fast Input Guardrails Layer (Regex/Whitelist)
        blocked, block_msg = self.input_guard.check(user_input)
        if blocked:
            self.audit_logger.record_layer_block(layer_name="InputGuardrails_Fast", reason=block_msg)
            self.audit_logger.finish_request()
            return block_msg
        self.audit_logger.record_layer_pass("InputGuardrails_Fast")
        
        # 3. Toxicity Classifier Layer (OpenAI Moderation API)
        blocked, block_msg = await self.toxicity_classifier.check(user_input)
        if blocked:
            self.audit_logger.record_layer_block(layer_name="Toxicity_Classifier", reason=block_msg)
            self.audit_logger.finish_request()
            return "This content violates our safe usage policy."
        self.audit_logger.record_layer_pass("Toxicity_Classifier")

        # 4. LLM Generation (Async)
        raw_response, agent_tokens = await self.agent.generate_response(user_input)
        
        # Log Tokens
        self.audit_logger.record_tokens(agent_tokens)
        self.cost_guard.add_usage(user_id, agent_tokens)

        # 5. Output Guardrails Layer (Async PII Redact & LLM Multi-Criteria Judge)
        blocked, safe_response, reason, meta, judge_tokens = await self.output_guard.check(raw_response, use_judge=True)
        
        # Log Judge Tokens
        self.audit_logger.record_tokens(judge_tokens)
        self.cost_guard.add_usage(user_id, judge_tokens)
        
        if blocked:
            self.audit_logger.record_layer_block(layer_name="OutputGuardrails_LLM_Judge", reason=reason)
            self.audit_logger.finish_request()
            return safe_response # Returning the filtered/blocked response message
            
        self.audit_logger.record_layer_pass(layer_name="OutputGuardrails_Pass", meta=meta)
        
        # 5. Output response and finish trace
        self.audit_logger.record_output(safe_response)
        self.audit_logger.finish_request()
        
        return safe_response
