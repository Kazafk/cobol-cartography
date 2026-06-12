from collections import defaultdict
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..graph.store import GraphStore

router = APIRouter(prefix="/api/ai", tags=["ai"])

_graph_store: GraphStore | None = None

_CALL_RELATIONS = {
    "CALLS_PROGRAM": "CALL",
    "CICS_LINKS_PROGRAM": "CICS LINK",
    "CICS_XCTLS_PROGRAM": "CICS XCTL",
}
_TABLE_RELATIONS = {
    "READS_TABLE": "READ",
    "WRITES_TABLE": "WRITE",
    "UPDATES_TABLE": "UPDATE",
    "DELETES_FROM_TABLE": "DELETE",
}
_ACCESS_RULE = {
    "READ":   ("Consultation de la table {table}", 0.75),
    "WRITE":  ("Création d'entrées dans la table {table}", 0.80),
    "UPDATE": ("Mise à jour de la table {table}", 0.80),
    "DELETE": ("Suppression d'entrées de la table {table}", 0.80),
}


def set_graph_store(store: GraphStore) -> None:
    global _graph_store
    _graph_store = store


def _require_store() -> GraphStore:
    if _graph_store is None:
        raise HTTPException(status_code=503, detail="Graph store not initialised.")
    return _graph_store


# --- Request / Response models ---

class ExplainProgramRequest(BaseModel):
    programId: str
    detailLevel: str = "standard"
    includeBusinessRules: bool = True


class ComplexityIndicators(BaseModel):
    copybooks_included: int
    programs_called: int
    tables_accessed: int
    called_by_count: int
    executed_by_jobs: int


class ProgramSummary(BaseModel):
    role: str
    complexity_indicators: ComplexityIndicators


class CallInteraction(BaseModel):
    target: str
    mechanism: str


class TableInteraction(BaseModel):
    table: str
    operations: list[str]


class Interactions(BaseModel):
    copybooks: list[str]
    outgoing_calls: list[CallInteraction]
    table_accesses: list[TableInteraction]
    executed_by_jobs: list[str]


class BusinessRuleCandidate(BaseModel):
    description: str
    confidence: float
    evidence: str


class ProgramExplanation(BaseModel):
    program_id: str
    detail_level: str
    mode: str = "local_strict"
    summary: ProgramSummary
    interactions: Interactions
    business_rule_candidates: list[BusinessRuleCandidate]
    uncertainties: list[str]
    ai_mode: str = "local_strict"


# --- Helpers ---

def _role_sentence(name: str, ci: ComplexityIndicators) -> str:
    parts: list[str] = []
    if ci.copybooks_included:
        parts.append(f"inclut {ci.copybooks_included} copybook(s) de définition de données")
    if ci.programs_called:
        parts.append(f"appelle {ci.programs_called} programme(s)")
    if ci.tables_accessed:
        parts.append(f"accède à {ci.tables_accessed} table(s) DB2")
    if ci.called_by_count:
        parts.append(f"est appelé par {ci.called_by_count} programme(s)")
    if ci.executed_by_jobs:
        parts.append(f"est exécuté par {ci.executed_by_jobs} job(s) JCL")
    if not parts:
        return f"{name} est un programme COBOL sans dépendances connues dans le graphe."
    return f"{name} est un programme COBOL qui " + ", ".join(parts) + "."


# --- Endpoint ---

@router.post("/explain/program", response_model=ProgramExplanation)
async def explain_program(req: ExplainProgramRequest) -> ProgramExplanation:
    store = _require_store()
    node_id = f"program:{req.programId.upper()}"
    node = store.get_node(node_id)
    if node is None:
        raise HTTPException(status_code=404, detail=f"Program '{req.programId.upper()}' not found in graph.")

    outgoing = store.get_outgoing(node_id)
    incoming = store.get_incoming(node_id)

    copybooks = [
        e.to_id.split(":", 1)[1]
        for e in outgoing
        if e.relation == "INCLUDES_COPYBOOK"
    ]

    outgoing_calls = [
        CallInteraction(target=e.to_id.split(":", 1)[1], mechanism=_CALL_RELATIONS[e.relation])
        for e in outgoing
        if e.relation in _CALL_RELATIONS
    ]

    # Group table accesses by table name to merge multiple operations
    table_ops: dict[str, list[str]] = defaultdict(list)
    for e in outgoing:
        if e.relation in _TABLE_RELATIONS:
            table_ops[e.to_id.split(":", 1)[1]].append(_TABLE_RELATIONS[e.relation])
    table_accesses = [TableInteraction(table=t, operations=ops) for t, ops in table_ops.items()]

    called_by_count = sum(1 for e in incoming if e.relation in _CALL_RELATIONS)

    executed_by_jobs: list[str] = []
    seen_jobs: set[str] = set()
    for e in incoming:
        if e.relation == "EXECUTES_PROGRAM":
            parts = e.from_id.split(":")
            if len(parts) >= 3 and parts[1] not in seen_jobs:
                seen_jobs.add(parts[1])
                executed_by_jobs.append(parts[1])

    ci = ComplexityIndicators(
        copybooks_included=len(copybooks),
        programs_called=len(outgoing_calls),
        tables_accessed=len(table_accesses),
        called_by_count=called_by_count,
        executed_by_jobs=len(executed_by_jobs),
    )

    # Business rule candidates derived from deterministic graph patterns
    candidates: list[BusinessRuleCandidate] = []
    if req.includeBusinessRules:
        for ta in table_accesses:
            for op in ta.operations:
                if op in _ACCESS_RULE:
                    desc_tmpl, conf = _ACCESS_RULE[op]
                    candidates.append(BusinessRuleCandidate(
                        description=desc_tmpl.format(table=ta.table),
                        confidence=conf,
                        evidence=f"EXEC SQL {op} ... FROM/INTO {ta.table}",
                    ))
        for call in outgoing_calls:
            if "CICS" in call.mechanism:
                verb = call.mechanism.split()[-1]  # LINK or XCTL
                candidates.append(BusinessRuleCandidate(
                    description=f"Délégation du traitement au programme {call.target}",
                    confidence=0.70,
                    evidence=f"EXEC CICS {verb} PROGRAM({call.target})",
                ))

    # Explicit uncertainties
    uncertainties: list[str] = [
        "Les CALL dynamiques (cibles variables) ne sont pas tracés dans le graphe.",
    ]
    stub_names = []
    for e in outgoing:
        if e.relation in _CALL_RELATIONS:
            target_node = store.get_node(e.to_id)
            if target_node is not None and target_node.path is None:
                stub_names.append(target_node.name)
    if stub_names:
        uncertainties.append(
            f"Les programmes {', '.join(stub_names)} n'ont pas été trouvés dans le "
            "workspace scanné — leurs propres dépendances sont inconnues."
        )

    return ProgramExplanation(
        program_id=node.name,
        detail_level=req.detailLevel,
        summary=ProgramSummary(role=_role_sentence(node.name, ci), complexity_indicators=ci),
        interactions=Interactions(
            copybooks=copybooks,
            outgoing_calls=outgoing_calls,
            table_accesses=table_accesses,
            executed_by_jobs=executed_by_jobs,
        ),
        business_rule_candidates=candidates,
        uncertainties=uncertainties,
    )
