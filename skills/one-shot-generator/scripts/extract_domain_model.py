#!/usr/bin/env python3
"""
Domain Model Extractor — v0.8.0

Replaces the old keyword-based ``detect_resource_from_description`` with a
multi-entity extractor that understands phrases like::

    "shopping cart with line items, discounts, and inventory holds"
    "user signup flow with email verification and password reset tokens"
    "order management API with payments, refunds, and shipment tracking"

Produces a structured ``DomainModel`` describing every entity it can find
plus the relationships and inferred attributes between them. It is rule
based (no LLM call, no external dependencies) so it runs inside the plugin
runtime, but it is dramatically richer than the previous "first non-keyword
word wins" heuristic.

Output schema (JSON-serialisable):

    {
        "primary_entity": "cart",
        "entities": [
            {"name": "cart", "plural": "carts", "attributes": [...]},
            {"name": "line_item", "plural": "line_items", "attributes": [...]},
            ...
        ],
        "relationships": [
            {"from": "cart", "to": "line_item", "kind": "has_many"},
            {"from": "cart", "to": "discount", "kind": "has_many"},
        ],
        "intent": "feature",       # feature | api | batch | refactor
        "confidence": 0.83,
        "raw": "shopping cart with line items, discounts, and inventory holds"
    }

CLI:
    python extract_domain_model.py "shopping cart with line items"
    python extract_domain_model.py --json "user signup with email verification"
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple

from lib.base_script import bootstrap_runtime, setup_logging
bootstrap_runtime()

logger = setup_logging(__name__)


# ─── Vocabulary ──────────────────────────────────────────────────────────────

# Action verbs that signal "the user wants me to build this"; stripped from
# entity candidates but used to detect ``intent``.
ACTION_VERBS = {
    "add", "create", "build", "generate", "implement", "make", "produce",
    "scaffold", "design", "draft", "set", "setup", "wire", "ship",
    "extend", "expand", "develop",
}

# Words that decorate descriptions but are never themselves entities.
STOP_WORDS = {
    "a", "an", "the", "and", "or", "with", "for", "to", "of", "in", "on",
    "at", "from", "by", "as", "via", "using", "between", "into", "onto",
    "that", "which", "who", "whose", "where", "when", "while", "should",
    "must", "can", "could", "would", "will", "may", "might", "shall",
    "be", "is", "are", "was", "were", "been", "being", "have", "has", "had",
    "this", "these", "those", "their", "them", "they", "it", "its",
    "system", "feature", "module", "service", "component", "thing",
    "complete", "full", "proper", "production", "ready", "scalable",
    "modern", "robust", "clean", "simple", "secure", "fast",
}

# Tokens that look like entities but are really architectural noise.
# (We keep this list small — too aggressive a filter erases real domain words.)
ARCHITECTURAL_TOKENS = {
    "api", "rest", "crud", "endpoint", "endpoints", "route", "routes",
    "router", "handler", "handlers", "controller", "controllers",
    "model", "models", "schema", "schemas", "table", "tables",
    "database", "db", "backend", "frontend", "fullstack",
    "request", "response", "payload", "json", "xml",
    "test", "tests", "testing", "spec", "specs",
    "doc", "docs", "documentation", "readme",
    "configuration", "config", "setting", "settings",
    "logging", "logger", "log", "logs",
}

# Words that signal the *intent* (which generator phase to route to).
INTENT_SIGNALS: Dict[str, List[str]] = {
    "api": ["api", "rest", "endpoint", "endpoints", "crud", "graphql",
            "http", "controller", "route", "routes"],
    "batch": ["batch", "job", "jobs", "queue", "worker", "background",
              "scheduled", "cron", "celery", "rq", "bull"],
    "auth": ["auth", "authentication", "authorization", "login", "signup",
             "signin", "logout", "jwt", "oauth", "session"],
    "realtime": ["websocket", "websockets", "realtime", "stream",
                 "streaming", "subscription", "pubsub"],
    "refactor": ["refactor", "migrate", "modernize", "rewrite", "extract"],
}

# Phrases that strongly indicate a multi-entity relationship.
RELATIONSHIP_MARKERS = {
    "has_many": ["with", "containing", "including", "having", "made of",
                 "composed of"],
    "belongs_to": ["belongs to", "owned by", "under", "part of"],
    "many_to_many": ["between", "linking", "associating"],
}


# ─── Data types ──────────────────────────────────────────────────────────────

@dataclass
class Attribute:
    name: str
    type_hint: str = "str"
    required: bool = True

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Entity:
    name: str                       # snake_case singular
    plural: str                     # snake_case plural
    pascal: str                     # PascalCase singular (class name)
    attributes: List[Attribute] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "plural": self.plural,
            "pascal": self.pascal,
            "attributes": [a.to_dict() for a in self.attributes],
        }


@dataclass
class Relationship:
    from_entity: str
    to_entity: str
    kind: str                       # has_many | belongs_to | many_to_many

    def to_dict(self) -> Dict:
        return {"from": self.from_entity, "to": self.to_entity, "kind": self.kind}


@dataclass
class DomainModel:
    raw: str
    intent: str
    primary_entity: Optional[str]
    entities: List[Entity]
    relationships: List[Relationship]
    confidence: float

    def to_dict(self) -> Dict:
        return {
            "raw": self.raw,
            "intent": self.intent,
            "primary_entity": self.primary_entity,
            "entities": [e.to_dict() for e in self.entities],
            "relationships": [r.to_dict() for r in self.relationships],
            "confidence": round(self.confidence, 3),
        }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _singularize(word: str) -> str:
    """Best-effort English singularisation (avoids over-aggressive trimming)."""
    if not word:
        return word
    lower = word.lower()
    # Irregulars first
    irregular = {
        "people": "person", "men": "man", "women": "woman", "children": "child",
        "teeth": "tooth", "feet": "foot", "mice": "mouse", "geese": "goose",
        "data": "data", "media": "media",
    }
    if lower in irregular:
        return irregular[lower]
    if lower.endswith("ies") and len(lower) > 3:
        return lower[:-3] + "y"
    if lower.endswith("ses") or lower.endswith("xes") or lower.endswith("zes") \
            or lower.endswith("ches") or lower.endswith("shes"):
        return lower[:-2]
    if lower.endswith("s") and not lower.endswith("ss") and len(lower) > 3:
        return lower[:-1]
    return lower


def _pluralize(word: str) -> str:
    if not word:
        return word
    lower = word.lower()
    if lower.endswith("y") and not lower.endswith(("ay", "ey", "iy", "oy", "uy")):
        return lower[:-1] + "ies"
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return lower + "es"
    return lower + "s"


def _snake_case(phrase: str) -> str:
    """Convert space-separated phrase to snake_case."""
    cleaned = re.sub(r"[^a-zA-Z0-9 ]+", " ", phrase).strip().lower()
    return re.sub(r"\s+", "_", cleaned)


def _pascal_case(phrase: str) -> str:
    parts = re.sub(r"[^a-zA-Z0-9 ]+", " ", phrase).strip().split()
    return "".join(p.capitalize() for p in parts)


# ─── Intent detection ────────────────────────────────────────────────────────

def detect_intent(text: str) -> Tuple[str, float]:
    """Return (intent, confidence). Defaults to 'feature' with low confidence."""
    lower = text.lower()
    scores: Dict[str, int] = {k: 0 for k in INTENT_SIGNALS}
    for intent, markers in INTENT_SIGNALS.items():
        for marker in markers:
            if re.search(rf"\b{re.escape(marker)}\b", lower):
                scores[intent] += 1
    best_intent, best_score = max(scores.items(), key=lambda kv: kv[1])
    if best_score == 0:
        return "feature", 0.4
    # Confidence scales with marker count, capped at 0.95
    confidence = min(0.55 + 0.15 * best_score, 0.95)
    return best_intent, confidence


# ─── Entity extraction ───────────────────────────────────────────────────────

def _tokenize_phrase(text: str) -> List[str]:
    """Split into significant tokens (lowercase words, no punctuation)."""
    return re.findall(r"[a-zA-Z][a-zA-Z\-]*", text.lower())


def _candidate_noun_phrases(text: str) -> List[str]:
    """Pull noun phrases by splitting on commas / 'and' / 'with'.

    Each phrase is a maximal run of non-separator tokens. Multi-word phrases
    like 'line items' or 'inventory holds' stay together.
    """
    lower = text.lower()
    # Normalise separators to a single delimiter so we can split once
    separators = [
        r"\band\b", r",", r"\bor\b", r"\bwith\b", r"\bcontaining\b",
        r"\bincluding\b", r"\bplus\b", r"\bas well as\b", r"\bbetween\b",
    ]
    splitter = re.compile("|".join(separators))
    raw_phrases = splitter.split(lower)
    cleaned = []
    for phrase in raw_phrases:
        # Strip action verbs and stop words from the front and back; keep
        # internal tokens (so 'line items' survives intact).
        tokens = _tokenize_phrase(phrase)
        # Trim leading verbs/stop words
        while tokens and (tokens[0] in ACTION_VERBS
                          or tokens[0] in STOP_WORDS):
            tokens.pop(0)
        # Trim trailing stop words
        while tokens and tokens[-1] in STOP_WORDS:
            tokens.pop()
        # Drop architectural noise that appears as a complete phrase
        if not tokens or all(t in ARCHITECTURAL_TOKENS for t in tokens):
            continue
        # Drop pure stop-word residue
        if all(t in STOP_WORDS for t in tokens):
            continue
        cleaned.append(" ".join(tokens))
    # De-duplicate while preserving order
    seen = set()
    unique = []
    for phrase in cleaned:
        if phrase and phrase not in seen:
            seen.add(phrase)
            unique.append(phrase)
    return unique


def _phrase_to_entity(phrase: str) -> Optional[Entity]:
    """Convert a noun phrase like 'line items' into an Entity."""
    tokens = phrase.split()
    if not tokens:
        return None
    # Drop trailing architectural words ('user CRUD' → 'user')
    while tokens and tokens[-1] in ARCHITECTURAL_TOKENS:
        tokens.pop()
    if not tokens:
        return None
    last = tokens[-1]
    singular_last = _singularize(last)
    plural_last = _pluralize(singular_last)
    singular_tokens = tokens[:-1] + [singular_last]
    plural_tokens = tokens[:-1] + [plural_last]
    name = "_".join(singular_tokens)
    plural = "_".join(plural_tokens)
    pascal = "".join(t.capitalize() for t in singular_tokens)
    return Entity(name=name, plural=plural, pascal=pascal,
                  attributes=_default_attributes_for(name))


def _default_attributes_for(entity_name: str) -> List[Attribute]:
    """Seed each entity with a sensible default attribute set.

    The shipped generators expect at least ``id``, ``name``, ``created_at``,
    ``updated_at``. Specific entity names get a couple of typed extras so
    the generated code looks domain-aware rather than generic.
    """
    base = [
        Attribute("id", "int", required=True),
        Attribute("name", "str", required=True),
        Attribute("description", "Optional[str]", required=False),
        Attribute("created_at", "datetime", required=True),
        Attribute("updated_at", "datetime", required=True),
    ]
    specific = {
        "cart":         [Attribute("user_id", "int", required=True),
                         Attribute("status", "str", required=True),
                         Attribute("total", "Decimal", required=True)],
        "line_item":    [Attribute("cart_id", "int", required=True),
                         Attribute("product_id", "int", required=True),
                         Attribute("quantity", "int", required=True),
                         Attribute("unit_price", "Decimal", required=True)],
        "discount":     [Attribute("code", "str", required=True),
                         Attribute("percent_off", "Decimal", required=False),
                         Attribute("amount_off", "Decimal", required=False),
                         Attribute("valid_until", "Optional[datetime]", required=False)],
        "inventory_hold": [Attribute("product_id", "int", required=True),
                           Attribute("quantity", "int", required=True),
                           Attribute("expires_at", "datetime", required=True)],
        "order":        [Attribute("user_id", "int", required=True),
                         Attribute("status", "str", required=True),
                         Attribute("total", "Decimal", required=True)],
        "payment":      [Attribute("order_id", "int", required=True),
                         Attribute("amount", "Decimal", required=True),
                         Attribute("currency", "str", required=True),
                         Attribute("status", "str", required=True)],
        "refund":       [Attribute("payment_id", "int", required=True),
                         Attribute("amount", "Decimal", required=True),
                         Attribute("reason", "str", required=False)],
        "user":         [Attribute("email", "str", required=True),
                         Attribute("password_hash", "str", required=True),
                         Attribute("is_active", "bool", required=True)],
        "product":      [Attribute("sku", "str", required=True),
                         Attribute("price", "Decimal", required=True),
                         Attribute("stock", "int", required=True)],
    }
    extras = specific.get(entity_name, [])
    # Merge, avoiding duplicate names
    seen = {a.name for a in extras}
    return extras + [a for a in base if a.name not in seen]


# ─── Relationship inference ──────────────────────────────────────────────────

def infer_relationships(text: str, entities: List[Entity]) -> List[Relationship]:
    """Infer relationships from connective phrases between entities.

    Heuristic: the FIRST entity in the sentence is usually the aggregate
    root; entities introduced by 'with' / 'containing' / 'including' are
    typically ``has_many`` children of it.
    """
    if len(entities) < 2:
        return []
    lower = text.lower()
    root = entities[0]
    relationships: List[Relationship] = []
    for child in entities[1:]:
        kind = "has_many"  # default for child entities
        # Tighten: if 'belongs to' appears near this entity, flip direction
        if re.search(rf"{re.escape(child.name)}.{{0,20}}belongs to", lower):
            relationships.append(Relationship(child.name, root.name, "belongs_to"))
            continue
        # Many-to-many marker
        if re.search(rf"between\s+{re.escape(root.plural)}\s+and\s+{re.escape(child.plural)}",
                     lower):
            relationships.append(Relationship(root.name, child.name, "many_to_many"))
            continue
        relationships.append(Relationship(root.name, child.name, kind))
    return relationships


# ─── Main extraction ─────────────────────────────────────────────────────────

def extract(text: str) -> DomainModel:
    """Public entry point: text → DomainModel."""
    from lib.telemetry import span
    with span("extract_domain_model",
              attrs={"text_length": len(text)}) as tspan:
        intent, intent_confidence = detect_intent(text)

        phrases = _candidate_noun_phrases(text)
        entities: List[Entity] = []
        seen_names = set()
        for phrase in phrases:
            ent = _phrase_to_entity(phrase)
            if ent is None or ent.name in seen_names:
                continue
            entities.append(ent)
            seen_names.add(ent.name)

        primary = entities[0].name if entities else None
        relationships = infer_relationships(text, entities)

        # Confidence: high when we found multiple entities + a clear intent.
        entity_factor = min(len(entities) / 3.0, 1.0)
        confidence = round(0.4 + 0.4 * entity_factor + 0.2 * (intent_confidence - 0.4),
                           3)
        confidence = max(0.1, min(confidence, 0.97))

        tspan.set_attr("entities_count", len(entities))
        tspan.set_attr("relationships_count", len(relationships))
        tspan.set_attr("confidence", confidence)
        tspan.set_attr("intent", intent)

        return DomainModel(
            raw=text,
            intent=intent,
            primary_entity=primary,
            entities=entities,
            relationships=relationships,
            confidence=confidence,
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _strip_at_path(args_str: str) -> str:
    """Drop @/path tokens and -- flags so the extractor sees the task only."""
    cleaned = re.sub(r"@\S+", "", args_str)
    cleaned = re.sub(r"--\S+(?:=\S+)?", "", cleaned)
    return cleaned.strip()


def main():
    parser = argparse.ArgumentParser(
        description="Extract a domain model from a natural language feature request"
    )
    parser.add_argument("request", nargs="+", help="Feature description")
    parser.add_argument("--json", action="store_true",
                        help="Emit JSON only (no markdown summary)")
    args = parser.parse_args()

    text = _strip_at_path(" ".join(args.request))
    model = extract(text)

    if args.json:
        print(json.dumps(model.to_dict(), indent=2))
        return

    print("DOMAIN MODEL")
    print("─" * 60)
    print(f"  Request:  {model.raw}")
    print(f"  Intent:   {model.intent}    (confidence {model.confidence:.2f})")
    print(f"  Primary:  {model.primary_entity}")
    print()
    print("ENTITIES")
    for ent in model.entities:
        attrs = ", ".join(a.name for a in ent.attributes[:6])
        if len(ent.attributes) > 6:
            attrs += f", … (+{len(ent.attributes) - 6})"
        print(f"  • {ent.pascal:<20} attrs: {attrs}")
    if model.relationships:
        print()
        print("RELATIONSHIPS")
        for rel in model.relationships:
            print(f"  • {rel.from_entity} ── {rel.kind} ──▶ {rel.to_entity}")

    # Always emit the structured JSON below the human summary so generators
    # can grep / parse it without re-running the script.
    print()
    print("---JSON---")
    print(json.dumps(model.to_dict(), indent=2))


if __name__ == "__main__":
    main()
