import json
import time
from typing import Dict, Any, List

class AuditLogger:
    def __init__(self):
        self.logs: List[Dict[str, Any]] = []
        self._current_request_start_time = 0

    def start_request(self, user_id: str, input_text: str):
        self._current_request_start_time = time.time()
        self.current_log = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_id": user_id,
            "input": input_text,
            "status": "processing",
            "blocked_by": None,
            "latency_ms": 0,
            "tokens_used": 0,
            "details": {}
        }
    
    def record_tokens(self, tokens: int):
        if self.current_log:
            self.current_log["tokens_used"] += tokens

    def record_layer_block(self, layer_name: str, reason: str):
        self.current_log["status"] = "blocked"
        self.current_log["blocked_by"] = layer_name
        self.current_log["details"]["block_reason"] = reason

    def record_layer_pass(self, layer_name: str, meta: Dict[str, Any] = None):
        if "passed_layers" not in self.current_log["details"]:
            self.current_log["details"]["passed_layers"] = []
        
        layer_meta = {"layer": layer_name}
        if meta:
            layer_meta.update(meta)
        self.current_log["details"]["passed_layers"].append(layer_meta)

    def record_output(self, output_text: str):
        self.current_log["output"] = output_text

    def finish_request(self):
        end_time = time.time()
        latency_ms = int((end_time - self._current_request_start_time) * 1000)
        self.current_log["latency_ms"] = latency_ms
        if self.current_log["status"] == "processing":
            self.current_log["status"] = "success"
            
        self.logs.append(self.current_log)
        self.current_log = None
        
    def export_json(self, filepath: str = "security_audit.json"):
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.logs, f, indent=2, ensure_ascii=False)

    def check_alerts(self, block_threshold: float = 0.4, rate_limit_threshold: int = 3):
        """
        Check for system anomalies based on logs.
        Alerts if block rate > threshold or if frequent rate limits happen.
        """
        if not self.logs:
            return
            
        total = len(self.logs)
        blocked = sum(1 for log in self.logs if log["status"] == "blocked")
        total_tokens = sum(log.get("tokens_used", 0) for log in self.logs)
        
        block_rate = blocked / total
        print("\n" + "="*80)
        print("MONITORING & ALERTS REPORT")
        print("="*80)
        print(f"Total Requests: {total} | Blocked: {blocked} | Block Rate: {block_rate*100:.1f}%")
        print(f"Total Session Tokens Expended: {total_tokens}")
        
        if block_rate >= block_threshold:
            print(f"⚠️  [ALERT] High block rate detected ({block_rate*100:.1f}% >= threshold {block_threshold*100:.1f}%). Possible coordinated attack campaign underway!")
            
        rate_limit_hits = sum(1 for log in self.logs if log.get("blocked_by") == "RateLimiter")
        if rate_limit_hits >= rate_limit_threshold:
            print(f"⚠️  [ALERT] Unusual number of Rate Limit hits ({rate_limit_hits} >= {rate_limit_threshold}). Potential DoS/spam attack.")
