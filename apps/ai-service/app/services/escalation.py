from app.models.schemas import EscalationResult

ESCALATION_KEYWORDS = [
    "denied", "denial",
    "rfe", "request for evidence",
    "removal", "removed",
    "deportation", "deported", "deport",
    "asylum",
    "appeal", "appealed",
    "noid", "notice of intent to deny",
    "court", "immigration court",
    "ice", "detention",
    "unlawful presence",
    "overstay",
    "criminal", "arrest", "convicted",
    "fraud",
    "ban", "barred",
]

# Same keywords in Spanish
ESCALATION_KEYWORDS_ES = [
    "negado", "negada", "denegado",
    "rfe", "solicitud de evidencia",
    "remocion", "removido",
    "deportacion", "deportado", "deportar",
    "asilo",
    "apelacion", "apelar",
    "noid",
    "corte", "tribunal de inmigracion",
    "ice", "detencion",
    "presencia ilegal",
    "permanencia excesiva",
    "criminal", "arresto", "condenado",
    "fraude",
    "prohibicion",
]

ALL_KEYWORDS = ESCALATION_KEYWORDS + ESCALATION_KEYWORDS_ES


def detect_escalation(message: str) -> EscalationResult:
    message_lower = message.lower()
    found = [kw for kw in ALL_KEYWORDS if kw in message_lower]
    return EscalationResult(
        is_escalation=len(found) > 0,
        keywords_found=found,
    )
