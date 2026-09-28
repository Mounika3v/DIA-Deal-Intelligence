import json
from pathlib import Path
from typing import Any
from src.config.settings import settings

class MemoryService:
    """Hindsight-first memory service with a deterministic local fallback."""
    def __init__(self, fallback_path="data/synthetic/runtime_memories.json"):
        self.fallback_path = Path(fallback_path)
        self.client = None
        self.mode = "LOCAL FALLBACK"
        if settings.hindsight_api_key:
            try:
                from hindsight_client import Hindsight
                self.client = Hindsight(base_url=settings.hindsight_api_url, api_key=settings.hindsight_api_key, timeout=20.0)
                try:
                    self.client.create_bank(bank_id=settings.hindsight_bank_id, name="DIA Sales Memory")
                except Exception:
                    pass
                self.mode = "HINDSIGHT CLOUD"
            except Exception:
                self.client = None
        self.fallback_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.fallback_path.exists():
            self.fallback_path.write_text("[]", encoding="utf-8")

    def _load(self):
        try:
            return json.loads(self.fallback_path.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, rows):
        self.fallback_path.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    def retain(self, memory: dict[str, Any]) -> dict[str, Any]:
        content = (f"Deal experience for {memory.get('account')} ({memory.get('opportunity_id')}). "
                   f"Stakeholder: {memory.get('stakeholder_role')}. "
                   f"Objection: {memory.get('objection_category')} — {memory.get('objection_detail')}. "
                   f"Response: {memory.get('sales_response')}. "
                   f"Reaction: {memory.get('customer_reaction')}. "
                   f"Outcome: {memory.get('deal_outcome')}. "
                   f"Learning: {memory.get('distilled_learning')}")
        local = self._load()
        if not any(x.get("interaction_id") == memory.get("interaction_id") for x in local):
            local.append(memory); self._save(local)
        cloud = False
        error = None
        if self.client:
            try:
                self.client.retain(bank_id=settings.hindsight_bank_id, content=content, context="DIA synthetic sales experience", metadata={"opportunity_id": memory.get("opportunity_id"), "account": memory.get("account")})
                cloud = True
            except Exception as exc:
                error = str(exc)
        return {"cloud": cloud, "local": True, "error": error}

    def recall(self, query: str, limit=5):
        if self.client:
            try:
                result = self.client.recall(bank_id=settings.hindsight_bank_id, query=query, max_tokens=2500, budget="mid")
                rows = [{"text": r.text, "type": getattr(r, "type", "memory")} for r in result.results[:limit]]
                if rows:
                    return rows, "HINDSIGHT CLOUD"
            except Exception:
                pass
        q = query.lower()
        rows = self._load()
        scored = []
        terms = set(q.replace("?", " ").split())
        for m in rows:
            blob = json.dumps(m).lower()
            score = sum(1 for t in terms if len(t) > 3 and t in blob)
            if score:
                scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"text": self._render(m), "type": "experience"} for _, m in scored[:limit]], "LOCAL FALLBACK"

    @staticmethod
    def _render(m):
        return f"{m.get('account')}: {m.get('stakeholder_role')} raised {m.get('objection_category')}. Response: {m.get('sales_response')} Outcome: {m.get('deal_outcome')}. Learning: {m.get('distilled_learning')}"
