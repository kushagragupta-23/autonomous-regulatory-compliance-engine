"""
Ten-Signal Hybrid Scoring & Explainability Engine.
Transplanted & enhanced from the Personalised Tax Intelligence Feed architecture.

Blends 10 discrete mathematical and semantic signals:
1. SectionScorer (weight 1.00) - Tax statute section matches client recurring profile
2. UserScorer (weight 0.95) - Assigned tax professional interest match
3. IndustryScorer (weight 0.85) - Direct client industry/sector alignment
4. ClientScorer (weight 0.70) - Client historical dispute/issue tag match
5. LexicalScorer (weight 0.60) - BM25 keyword relevance with non-linear saturation
6. UrgencyScorer (weight 0.55) - Mandatory statutory deadlines & penalty triggers
7. AuthorityScorer (weight 0.45) - Official issuer prestige & doc-type weight
8. FreshnessScorer (weight 0.40) - Exponential recency decay (14-day half-life)
9. TopicScorer (weight 0.35) - Jaccard thematic breadth across desk specializations
10. SemanticScorer (blended 60:40 client:user) - TF-IDF cosine meaning similarity
"""

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple


@dataclass
class SignalResult:
    name: str
    kind: str          # UI badge type (section, sector, issue, urgency, etc.)
    value: float       # Normalized [0.0, 1.0]
    reason: Optional[str] = None
    detail: Optional[Dict[str, Any]] = None


class ScoringConfig:
    def __init__(self):
        self.signal_weights = {
            "section": 1.00,
            "user": 0.95,
            "industry": 0.85,
            "client": 0.70,
            "lexical": 0.60,
            "urgency": 0.55,
            "authority": 0.45,
            "freshness": 0.40,
            "topic": 0.35,
        }
        self.weight_rule = 0.65
        self.weight_semantic = 0.35
        self.semantic_client_weight = 0.60
        self.semantic_user_weight = 0.40
        self.freshness_half_life_days = 14.0
        self.freshness_max_days = 180.0
        self.min_reason_value = 0.15
        self.authoritative_sources = [
            "cbic", "cbdt", "rbi", "sebi", "dgft", "pib", "gst council", "ministry of finance"
        ]
        self.doc_type_authority = {
            "Notification": 0.95,
            "Circular": 0.90,
            "Order": 0.85,
            "Instruction": 0.80,
            "Gazette": 0.95,
            "Press Release": 0.60,
            "Advisory": 0.50
        }


def _norm_str(s: str) -> str:
    return re.sub(r"[\s\-_]+", "", s.lower())


def _overlap(a: List[str], b: List[str]) -> List[str]:
    bnorm = {_norm_str(x) for x in b if x}
    return sorted({x for x in a if _norm_str(x) in bnorm})


def _tokenize(text: str) -> List[str]:
    return [w.lower() for w in re.findall(r"\b[a-zA-Z0-9_\-\.]{2,}\b", text)]


class SimpleTfidfCosine:
    """Lightweight TF-IDF term vector builder for pure-Python cosine similarity."""
    
    @staticmethod
    def vectorize(text: str) -> Dict[str, float]:
        tokens = _tokenize(text)
        if not tokens:
            return {}
        counts: Dict[str, int] = {}
        for t in tokens:
            counts[t] = counts.get(t, 0) + 1
        total = len(tokens)
        vec: Dict[str, float] = {}
        norm_sq = 0.0
        for t, c in counts.items():
            tf = (c / total) * math.log(1.0 + 10.0 / (1.0 + len(t)))
            vec[t] = tf
            norm_sq += tf * tf
        norm = math.sqrt(norm_sq) or 1.0
        return {t: v / norm for t, v in vec.items()}

    @staticmethod
    def cosine_similarity(v1: Dict[str, float], v2: Dict[str, float]) -> float:
        if not v1 or not v2:
            return 0.0
        dot = sum(v1[k] * v2[k] for k in v1 if k in v2)
        return max(0.0, min(1.0, dot))


class ScoringContext:
    """Encapsulates the update, client, and tax practitioner profile during ranking."""

    def __init__(self, update: Dict[str, Any], client: Dict[str, Any], user: Optional[Dict[str, Any]] = None, config: Optional[ScoringConfig] = None):
        self.update = update
        self.client = client
        self.user = user or {
            "name": "Kushagra Gupta (Lead Partner)",
            "desk": "Enterprise Tax & Regulatory Practice",
            "topics": ["Transfer Pricing", "Input Tax Credit (ITC)", "TDS / TCS Withholding", "Corporate Compliance", "FEMA & Cross-Border"]
        }
        self.config = config or ScoringConfig()
        
        # Precompute text representations
        upd_text = f"{update.get('title', '')} {update.get('summary', '')} {update.get('full_text', '')}"
        self.update_tokens = set(_tokenize(upd_text))
        self.update_vec = SimpleTfidfCosine.vectorize(upd_text)
        
        client_text = f"{client.get('name', '')} {client.get('sector', '')} {' '.join(client.get('focus_topics', []))} {' '.join(client.get('sections', []))} {' '.join(client.get('issue_tags', []))}"
        self.client_vec = SimpleTfidfCosine.vectorize(client_text)
        
        user_text = f"{self.user.get('name', '')} {self.user.get('desk', '')} {' '.join(self.user.get('topics', []))}"
        self.user_vec = SimpleTfidfCosine.vectorize(user_text)


# ---------------------------------------------------------------------------
# Individual Signal Scorers
# ---------------------------------------------------------------------------

class SectionScorer:
    name = "section"
    kind = "section"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        client_secs = {_norm_str(s) for s in ctx.client.get("sections", [])}
        hits = sorted({s for s in ctx.update.get("sections", []) if _norm_str(s) in client_secs})
        value = min(1.0, 0.85 + 0.15 * (len(hits) - 1)) if hits else 0.0
        reason = f"Statutory match: {', '.join(hits[:3])}" if hits else None
        return SignalResult(self.name, self.kind, value, reason, {"hits": hits})


class IndustryScorer:
    name = "industry"
    kind = "sector"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        client_sector = ctx.client.get("sector", "")
        circ_sectors = ctx.update.get("sectors", [])
        hits = _overlap(circ_sectors, [client_sector] + ctx.client.get("secondary_sectors", []))
        
        if hits:
            value = min(1.0, 0.85 + 0.15 * (len(hits) - 1))
            reason = f"Direct sector hit: {hits[0]}"
        elif any(_norm_str(s) in _norm_str(ctx.update.get("title", "") + ctx.update.get("summary", "")) for s in [client_sector]):
            value = 0.70
            reason = f"Sub-sector relevance: {client_sector}"
        else:
            value = 0.10
            reason = None
        return SignalResult(self.name, self.kind, value, reason, {"hits": hits})


class ClientScorer:
    name = "client"
    kind = "issue"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        hits = _overlap(ctx.update.get("topics", []), ctx.client.get("issue_tags", []) + ctx.client.get("focus_topics", []))
        value = min(1.0, 0.75 + 0.15 * (len(hits) - 1)) if hits else 0.0
        reason = f"Priority issue: {', '.join(hits[:2])}" if hits else None
        return SignalResult(self.name, self.kind, value, reason, {"hits": hits})


class UserScorer:
    name = "user"
    kind = "interest"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        hits = _overlap(ctx.update.get("topics", []), ctx.user.get("topics", []))
        value = min(1.0, 0.75 + 0.15 * (len(hits) - 1)) if hits else 0.0
        reason = f"Lead practitioner focus: {', '.join(hits[:2])}" if hits else None
        return SignalResult(self.name, self.kind, value, reason, {"hits": hits})


class TopicScorer:
    name = "topic"
    kind = "topic"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        upd = {_norm_str(t) for t in ctx.update.get("topics", []) if t}
        interests = {_norm_str(t) for t in list(ctx.user.get("topics", [])) + list(ctx.client.get("focus_topics", [])) if t}
        if not upd or not interests:
            return SignalResult(self.name, self.kind, 0.20)
        inter = upd & interests
        union = upd | interests
        val = len(inter) / len(union) if union else 0.0
        value = min(1.0, 0.30 + val * 0.70)
        reason = "Thematic alignment across practice desk" if value >= 0.4 else None
        return SignalResult(self.name, self.kind, value, reason)


class LexicalScorer:
    """BM25-style lexical keyword match with saturation curve 1 - e^(-raw / 4)."""
    name = "lexical"
    kind = "lexical"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        profile_keywords = set()
        for s in [ctx.client.get("sector", ""), ctx.client.get("name", "")]:
            profile_keywords.update(_tokenize(s))
        for t in ctx.client.get("focus_topics", []) + ctx.client.get("sections", []):
            profile_keywords.update(_tokenize(t))
        
        matches = ctx.update_tokens & profile_keywords
        raw_score = len(matches)
        saturated = 1.0 - math.exp(-raw_score / 4.0) if raw_score > 0 else 0.0
        reason = f"High keyword match ({len(matches)} terms)" if saturated >= 0.40 else None
        return SignalResult(self.name, self.kind, saturated, reason, {"matched_terms": list(matches)[:5]})


class AuthorityScorer:
    name = "authority"
    kind = "authority"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        doc_type = ctx.update.get("doc_type", "Circular")
        base = ctx.config.doc_type_authority.get(doc_type, 0.75)
        auth_text = f"{ctx.update.get('authority', '')} {ctx.update.get('source', '')}".lower()
        has_official = any(s in auth_text for s in ctx.config.authoritative_sources)
        bonus = 0.10 if has_official else 0.0
        value = min(1.0, base + bonus)
        issuer = ctx.update.get("authority", "Official Authority")
        reason = f"Binding statutory {doc_type} by {issuer}" if value >= 0.85 else None
        return SignalResult(self.name, self.kind, value, reason)


class FreshnessScorer:
    """Exponential half-life decay: 0.5^(days / 14)."""
    name = "freshness"
    kind = "freshness"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        raw_date = ctx.update.get("date") or ctx.update.get("notification_date") or ctx.update.get("published_date")
        now = datetime.now(timezone.utc)
        days = 1.0
        if raw_date:
            try:
                for fmt in ["%d %B %Y", "%Y-%m-%d", "%d-%m-%Y", "%Y-%m-%dT%H:%M:%SZ"]:
                    try:
                        dt = datetime.strptime(raw_date.strip()[:10], fmt[:len(raw_date.strip()[:10])])
                        dt = dt.replace(tzinfo=timezone.utc)
                        days = max(0.0, (now - dt).total_seconds() / 86400.0)
                        break
                    except Exception:
                        pass
            except Exception:
                days = 2.0
        
        value = 0.5 ** (days / ctx.config.freshness_half_life_days)
        reason = "Published within past 48 hours" if days <= 2.0 else ("Recent circular" if days <= 7.0 else None)
        return SignalResult(self.name, self.kind, value, reason, {"days_ago": round(days, 1)})


class UrgencyScorer:
    name = "urgency"
    kind = "urgency"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        urgency_raw = str(ctx.update.get("urgency", "")).lower()
        full_text = f"{ctx.update.get('title', '')} {ctx.update.get('summary', '')} {ctx.update.get('full_text', '')}".lower()
        
        deadline_keywords = ["due date", "deadline", "penalty", "w.e.f.", "with effect from", "mandatory", "compliance date", "last date"]
        triggered = [kw for kw in deadline_keywords if kw in full_text]
        
        if "high" in urgency_raw or "critical" in urgency_raw:
            value = 0.95
        elif triggered:
            value = min(1.0, 0.75 + 0.10 * len(triggered))
        elif "medium" in urgency_raw:
            value = 0.65
        else:
            value = 0.30
        
        reason = f"Statutory filing deadline triggered ({', '.join(triggered[:2])})" if triggered else ("Time-sensitive compliance obligation" if value >= 0.70 else None)
        return SignalResult(self.name, self.kind, value, reason, {"triggers": triggered})


class SemanticScorer:
    """TF-IDF Cosine similarity vector comparison (60% client profile, 40% user practitioner profile)."""
    name = "semantic"
    kind = "semantic"

    def evaluate(self, ctx: ScoringContext) -> SignalResult:
        sem_client = SimpleTfidfCosine.cosine_similarity(ctx.update_vec, ctx.client_vec)
        sem_user = SimpleTfidfCosine.cosine_similarity(ctx.update_vec, ctx.user_vec)
        blended = ctx.config.semantic_client_weight * sem_client + ctx.config.semantic_user_weight * sem_user
        # Give baseline semantic credit for relevant domain
        value = min(1.0, max(0.20, blended * 2.5))
        reason = f"Thematically grounded in {ctx.client.get('name', 'Client')}'s operational tax nexus" if value >= 0.35 else None
        return SignalResult(self.name, self.kind, value, reason, {"sem_client": round(sem_client, 4), "sem_user": round(sem_user, 4)})


# ---------------------------------------------------------------------------
# Explainability Engine & Hybrid Scorer
# ---------------------------------------------------------------------------

class ExplainabilityEngine:
    def __init__(self, config: ScoringConfig):
        self.config = config

    def build(self, results: List[SignalResult], weights: Dict[str, float], sem_result: SignalResult) -> Tuple[List[Dict[str, str]], str]:
        contributions = []
        for r in results:
            if r.reason and r.value >= self.config.min_reason_value:
                contributions.append((weights.get(r.name, 0.0) * r.value, r))
        if sem_result.reason and sem_result.value >= self.config.min_reason_value:
            contributions.append((sem_result.value * 0.8, sem_result))

        contributions.sort(key=lambda x: x[0], reverse=True)
        reasons = [{"kind": r.kind, "text": r.reason} for _, r in contributions]
        
        if not reasons:
            summary = "General regulatory update; standard periodic compliance schedule."
        else:
            summary = " | ".join(f"✓ {r['text']}" for r in reasons[:3])
            
        return reasons, summary


class TenSignalHybridScorer:
    """Production-grade scoring engine blending 10 signals into a 0-100 score."""

    def __init__(self, config: Optional[ScoringConfig] = None):
        self.config = config or ScoringConfig()
        self.signals = [
            SectionScorer(),
            IndustryScorer(),
            ClientScorer(),
            UserScorer(),
            TopicScorer(),
            LexicalScorer(),
            AuthorityScorer(),
            FreshnessScorer(),
            UrgencyScorer()
        ]
        self.semantic = SemanticScorer()
        self.explainer = ExplainabilityEngine(self.config)

    def score(self, update: Dict[str, Any], client: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        ctx = ScoringContext(update, client, user, self.config)
        weights = self.config.signal_weights

        # 1. Evaluate discrete signals
        results = [s.evaluate(ctx) for s in self.signals]
        wsum = sum(weights.get(r.name, 0.0) for r in results) or 1.0
        rule_composite = sum(weights.get(r.name, 0.0) * r.value for r in results) / wsum

        # 2. Evaluate semantic signal
        sem_res = self.semantic.evaluate(ctx)
        semantic_composite = sem_res.value

        # 3. Final blend
        final = max(0.0, min(1.0, self.config.weight_rule * rule_composite + self.config.weight_semantic * semantic_composite))
        score_100 = round(final * 100.0, 1)

        # 4. Explainability audit trail
        reasons, summary = self.explainer.build(results, weights, sem_res)

        # 5. Suggested task generation
        suggested_task = self._generate_suggested_task(update, client, score_100)

        return {
            "score_100": score_100,
            "rule_score": round(rule_composite, 4),
            "semantic_score": round(semantic_composite, 4),
            "sem_client": sem_res.detail.get("sem_client", 0.0),
            "sem_user": sem_res.detail.get("sem_user", 0.0),
            "signals": {r.name: round(r.value, 3) for r in results},
            "reasons": reasons,
            "explanation": summary,
            "suggested_task": suggested_task,
            "urgency_tier": "CRITICAL" if score_100 >= 75.0 else ("ELEVATED" if score_100 >= 55.0 else "INFORMATIONAL")
        }

    def _generate_suggested_task(self, update: Dict[str, Any], client: Dict[str, Any], score_100: float) -> Dict[str, Any]:
        title = update.get("title", "")
        authority = update.get("authority", "Tax Authority")
        client_name = client.get("name", "Client")

        if score_100 >= 75.0:
            action = f"Draft Statutory Action Memo for {client_name}"
            description = f"High statutory nexus ({score_100}%). Review ERP withholding configuration, update ledger entries, and schedule client briefing regarding '{title}'."
            priority = "P1 - Critical"
            due = "48 Hours"
        elif score_100 >= 55.0:
            action = f"Review Compliance Impact for {client_name}"
            description = f"Moderate nexus ({score_100}%). Verify whether existing contracts or return disclosures need amendment under {authority} guidelines."
            priority = "P2 - Elevated"
            due = "7 Days"
        else:
            action = f"Archive for Annual Tax Audit Docket"
            description = f"Standard notice. File in {client_name}'s regulatory reference archive for statutory audit year-end defense."
            priority = "P3 - Routine"
            due = "Next Quarter"

        return {
            "task_id": f"task_{abs(hash(title)) % 1000000:06d}",
            "action": action,
            "description": description,
            "priority": priority,
            "due_date": due,
            "status": "PENDING_APPROVAL"
        }
