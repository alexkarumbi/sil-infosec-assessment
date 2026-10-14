"""AI input/output guardrails for the SIL lab.

Order of checks on the way IN (cheapest first):
  1. prompt-injection heuristics (regex, English + Swahili phrases)
  2. prompt-injection classifier (optional, INJECTION_MODEL_ENABLED): the open
     protectai/deberta-v3-base-prompt-injection-v2 model, run with Hugging Face transformers
  3. secrets (connection strings, cloud keys, private keys, tokens, password assignments)
  4. hard identifiers (MRN, National ID, KRA PIN, card numbers) -> BLOCK, PHI never leaves
  5. softer personal data (names, phones, emails, places) -> MASK before the prompt leaves
On the way OUT: mask personal data in the model's answer.

Dependency note (found by pip-audit in CI): LLM Guard 0.3.16 pins presidio-anonymizer 2.2.358,
which pins cryptography<44.1 (10 known vulnerabilities). We therefore use Presidio's analyzer only,
do the masking ourselves (_mask below), and call the same injection model directly.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

INJECTION_MODEL_ENABLED = os.environ.get("INJECTION_MODEL_ENABLED", "true").lower() == "true"
INJECTION_MODEL = os.environ.get("INJECTION_MODEL", "protectai/deberta-v3-base-prompt-injection-v2")
INJECTION_THRESHOLD = float(os.environ.get("INJECTION_THRESHOLD", "0.9"))
# en_core_web_lg finds names far better (the small model tagged "Summarise" as a PERSON in testing).
# The full image uses lg; the light CI image uses sm to save ~500 MB.
SPACY_MODEL = os.environ.get("SPACY_MODEL", "en_core_web_lg")
SCORE_THRESHOLD = 0.5   # an 8-digit number alone (0.3) is not enough; with "ID"/"national" nearby it is

INJECTION_HEURISTICS = re.compile(
    r"ignore\s+(all\s+|any\s+)?(previous|prior|above|earlier)?\s*(instructions|rules|prompts?)"
    r"|(reveal|print|show|repeat)\s+(your|the)\s+(system\s+prompt|instructions)"
    r"|system\s+prompt"
    r"|you\s+are\s+now\s+(dan|in\s+developer\s+mode)"
    r"|developer\s+mode|jailbreak|do\s+anything\s+now"
    r"|puuza\s+maagizo",                 # Swahili: "ignore the instructions"
    re.IGNORECASE,
)

SECRET_PATTERNS = re.compile(
    r"(?i)(postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|mssql)://[^:\s/]+:[^@\s]+@\S+"   # DB connection strings
    r"|AKIA[0-9A-Z]{16}"                                                            # AWS access key ID
    r"|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
    r"|gh[pousr]_[A-Za-z0-9]{36}"                                                   # GitHub tokens
    r"|xox[abpr]-[A-Za-z0-9-]{10,}"                                                 # Slack tokens
    r"|(?:password|passwd|pwd|secret|api[_-]?key)\s*[:=]\s*\S{6,}"
)

BLOCK_ENTITIES = {"MEDICAL_RECORD_NUMBER", "KE_NATIONAL_ID", "KRA_PIN", "CREDIT_CARD", "US_SSN", "IBAN_CODE"}
MASK_ENTITIES = {"PERSON", "PHONE_NUMBER", "KE_PHONE", "EMAIL_ADDRESS", "LOCATION"}

_analyzer = None
_classifier = None


def _engines():
    """Build the engines once: spaCy + Presidio analyzer, and the injection classifier when enabled."""
    global _analyzer, _classifier
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer
        from presidio_analyzer.nlp_engine import NlpEngineProvider

        nlp = NlpEngineProvider(
            nlp_configuration={
                "nlp_engine_name": "spacy",
                "models": [{"lang_code": "en", "model_name": SPACY_MODEL}],
            }
        ).create_engine()
        analyzer = AnalyzerEngine(nlp_engine=nlp, supported_languages=["en"])
        custom = [
            ("KE_PHONE", r"(?:\+254|\b0)(?:7|1)\d{8}\b", 0.7, []),
            ("KE_NATIONAL_ID", r"\b\d{7,8}\b", 0.3, ["id", "national", "idno", "identity"]),
            ("KRA_PIN", r"\b[AP]\d{9}[A-Z]\b", 0.8, []),
            ("MEDICAL_RECORD_NUMBER", r"\bMRN[-:\s]?\d{5,10}\b", 0.85, []),
        ]
        for entity, regex, score, context in custom:
            analyzer.registry.add_recognizer(
                PatternRecognizer(
                    supported_entity=entity,
                    patterns=[Pattern(name=entity.lower(), regex=regex, score=score)],
                    context=context,
                )
            )
        _analyzer = analyzer
    if INJECTION_MODEL_ENABLED and _classifier is None:
        from transformers import pipeline

        _classifier = pipeline(
            "text-classification", model=INJECTION_MODEL, truncation=True, max_length=512, device=-1
        )
    return _analyzer


def _model_says_injection(text: str) -> bool:
    if _classifier is None:
        return False
    result = _classifier(text)[0]          # e.g. {"label": "INJECTION", "score": 0.998}
    return result["label"].upper() == "INJECTION" and result["score"] >= INJECTION_THRESHOLD


def _mask(text: str, findings) -> str:
    """Replace each detected span with <ENTITY_TYPE>. Overlaps: keep the earliest, then longest span."""
    spans = sorted(findings, key=lambda f: (f.start, -(f.end - f.start)))
    out, cursor = [], 0
    for f in spans:
        if f.start < cursor:               # overlaps a span already masked
            continue
        out.append(text[cursor:f.start])
        out.append(f"<{f.entity_type}>")
        cursor = f.end
    out.append(text[cursor:])
    return "".join(out)


def warm_up() -> None:
    """Called at image build time so models are downloaded into the image, not at runtime."""
    _engines()
    check_input("warm up the guardrails")


@dataclass
class Verdict:
    allowed: bool
    reason: str | None = None
    entities: list[str] = field(default_factory=list)
    text: str = ""
    masked: int = 0


def check_input(prompt: str) -> Verdict:
    analyzer = _engines()

    if INJECTION_HEURISTICS.search(prompt) or _model_says_injection(prompt):
        return Verdict(False, "prompt_injection")

    if SECRET_PATTERNS.search(prompt):
        return Verdict(False, "secret_detected")

    findings = analyzer.analyze(text=prompt, language="en", score_threshold=SCORE_THRESHOLD)
    hard = sorted({f.entity_type for f in findings if f.entity_type in BLOCK_ENTITIES})
    if hard:
        return Verdict(False, "phi_detected", entities=hard)

    soft = [f for f in findings if f.entity_type in MASK_ENTITIES]
    masked = _mask(prompt, soft) if soft else prompt
    return Verdict(True, text=masked, masked=len(soft), entities=sorted({f.entity_type for f in soft}))


def clean_output(answer: str) -> tuple[str, int]:
    analyzer = _engines()
    found = [
        f
        for f in analyzer.analyze(text=answer, language="en", score_threshold=SCORE_THRESHOLD)
        if f.entity_type in MASK_ENTITIES | BLOCK_ENTITIES
    ]
    if not found:
        return answer, 0
    return _mask(answer, found), len(found)
