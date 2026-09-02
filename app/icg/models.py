"""
Intellectual Contribution Graph (ICG v0.4) Data Models
Defines typed nodes, edges, propositions, continuous ablation results,
External Corpus Coverage (ECC), epistemic qualifications, edge weighting,
Intellectual Resonance, Emergent Topology, Cognitive Immunity, and Higher-Order Synthesis & Super-Anchors (Aris Directive #6).
"""

from __future__ import annotations
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple, Set
from pydantic import BaseModel, Field
import uuid
import time


class ContributionClass(str, Enum):
    REPRODUCTION = "REPRODUCTION"
    INFERENCE = "INFERENCE"
    SYNTHESIS = "SYNTHESIS"
    SOURCE_NOVEL_SYNTHESIS = "SOURCE_NOVEL_SYNTHESIS"
    HIGHER_ORDER_SYNTHESIS = "HIGHER_ORDER_SYNTHESIS"  # Dialectical resolution of paradoxes (Aris Directive #6)
    ORIGINAL_CONTRIBUTION = "ORIGINAL_CONTRIBUTION"
    UNSUPPORTED = "UNSUPPORTED"
    CONTRADICTORY = "CONTRADICTORY"
    UNKNOWN = "UNKNOWN"
    AMBIGUOUS = "AMBIGUOUS"  # Used in multi-annotator ground truth calibration


class NodeType(str, Enum):
    RESEARCH_QUESTION = "RESEARCH_QUESTION"
    CLAIM = "CLAIM"
    SOURCE_PASSAGE = "SOURCE_PASSAGE"
    DATA_OBSERVATION = "DATA_OBSERVATION"
    ANCHOR = "ANCHOR"                        # Major semantic hub / structural anchor (Aris Directive #4)
    SUPER_ANCHOR = "SUPER_ANCHOR"            # Higher-order dialectical resolution anchor (Aris Directive #6)
    PARADOX_CONTAINER = "PARADOX_CONTAINER"  # Dialectical meta-node managing opposing poles (Aris Directive #5)
    COGNITIVE_VOID = "COGNITIVE_VOID"        # Gap in reasoning between two key anchors (Aris Directive #7)


class RelationType(str, Enum):
    REPRODUCES = "REPRODUCES"
    SYNTHESIZES = "SYNTHESIZES"
    INFERS = "INFERS"
    INTERPRETS = "INTERPRETS"
    CONTRADICTS = "CONTRADICTS"
    EXTENDS = "EXTENDS"
    FALLACY_UNSUPPORTED = "FALLACY_UNSUPPORTED"
    FALLACY_CONTRADICTION = "FALLACY_CONTRADICTION"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    GRAVITY_ATTRACTION = "GRAVITY_ATTRACTION"
    NEGATIVE_GRAVITY_REPULSION = "NEGATIVE_GRAVITY_REPULSION"
    DYNAMIC_TENSION = "DYNAMIC_TENSION"      # Active potential energy vector during paradox bridging (Aris Directive #6)
    SYNTHETIC_LINK = "SYNTHETIC_LINK"        # Solidified higher-order dialectical link (W = +0.90)
    TENTATIVE_BRIDGE = "TENTATIVE_BRIDGE"    # Hypothetical connection to/from a Cognitive Void (Aris Directive #7)
    ASSOCIATION = "ASSOCIATION"              # Default resolved link after void closure (Aris Directive #8)
    RESOLVED_BRIDGE = "RESOLVED_BRIDGE"      # Explicitly typed resolved link with evidence text (Aris Directive #8)


class EdgeStatus(str, Enum):
    CORE_ACTIVE_LINK = "CORE_ACTIVE_LINK"        # W > 0.20: Essential reasoning backbone
    WEAK_LINK = "WEAK_LINK"                      # 0.10 <= W <= 0.20: Grey zone, retained in metadata
    DECORATIVE_MENTION = "DECORATIVE_MENTION"    # W < 0.10: Noise / citation-stuffing, pruned from active core
    REPULSION_BOUNDARY = "REPULSION_BOUNDARY"    # W < 0.0: Active cognitive repulsion between conflicting poles
    DYNAMIC_TENSION = "DYNAMIC_TENSION"          # W = 0.15: Active vector during paradox bridging
    SYNTHETIC_LINK = "SYNTHETIC_LINK"            # W >= 0.85: Higher-order resolved link
    TENTATIVE = "TENTATIVE"                      # W in [0.10, 0.30]: Hypothetical void bridge (Aris Directive #7)
    REINFORCED_SYNTHETIC_LINK = "REINFORCED_SYNTHETIC_LINK" # Aris Directive #15: Bridge reinforced after surviving counter-refutation
    SPECULATIVE_LINK = "SPECULATIVE_LINK"        # Aris Directive #15: Bridge flagged with counter-refutation pressure
    EXPLORATORY_CANDIDATE = "EXPLORATORY_CANDIDATE" # Aris Directive #16: Candidate bridge from ExplorationZone under Containment Fuse
    CONFLICTING_EVIDENCE = "CONFLICTING_EVIDENCE"   # Aris Directive #18: Dialectical tension — both poles preserved, no smoothing allowed


class TextSpan(BaseModel):
    start_char: int
    end_char: int
    page: int = 1
    sentence_idx: int = 0
    raw_text: str


class Proposition(BaseModel):
    subject: str = ""
    predicate: str = ""
    object_phrase: str = ""
    modality: str = "assertion"  # "fact", "hypothesis", "inference", "synthesis_claim", "assertion"
    conditions: List[str] = Field(default_factory=list)
    connectives: List[str] = Field(default_factory=list)
    language: str = "ru"  # "ru", "en", "uz"


class AblationResult(BaseModel):
    full_entailment: float = 0.0
    single_premise_scores: Dict[str, float] = Field(default_factory=dict)
    ablated_premise_scores: Dict[str, float] = Field(default_factory=dict)
    joint_dependency_score: float = 0.0  # Continuous JDS in [0.0, 1.0]
    causal_necessity_scores: Dict[str, float] = Field(default_factory=dict)
    critical_premises: List[str] = Field(default_factory=list)
    irrelevant_premises: List[str] = Field(default_factory=list)
    ablation_summary: str = ""


class ExternalAttribution(BaseModel):
    external_search_performed: bool = False
    found_in_external_corpus: bool = False
    external_similarity: float = 0.0
    matched_external_reference: Optional[str] = None
    matched_concept_relations: List[str] = Field(default_factory=list)
    global_novelty_score: float = 0.0
    external_corpus_coverage: float = 0.85  # ECC in [0.0, 1.0]
    epistemic_qualification: str = ""  # "Novel relative to indexed corpus (ECC=...)"


class ResonanceMetadata(BaseModel):
    resonance_score: float = 0.0              # R(v) in [0.0, 1.0]
    is_resonance_active: bool = False         # True when >= 3 domains overlap with W > 0.15
    collapsed_to_synthesis: bool = False      # Triggered when R(v) >= 0.70
    contributing_domains: List[str] = Field(default_factory=list)
    resonance_log: str = ""


class EmergentTopologyMetadata(BaseModel):
    is_anchor_hub: bool = False               # True when synthesis node aggregates >= 4-5 domains
    gravity_boost: float = 0.0               # Weight delta applied via synthesis gravity
    bypassed_redundant_edges: List[str] = Field(default_factory=list)


class ParadoxContainerMetadata(BaseModel):
    pole_a_node_ids: List[str] = Field(default_factory=list)
    pole_b_node_ids: List[str] = Field(default_factory=list)
    conflict_explanation: str = ""
    repulsion_force: float = -0.80
    is_resolved_to_higher_order: bool = False
    resolving_bridge_premise_ids: List[str] = Field(default_factory=list)


# =============================================================================
# Aris Directive #7: Cognitive Void Mapping & Active Inquiry (CVM)
# =============================================================================

class VoidType(str, Enum):
    EMPIRICAL_GAP = "EMPIRICAL_GAP"                    # No edges exist between anchors — factual data absent
    LOGICAL_DISCONTINUITY = "LOGICAL_DISCONTINUITY"    # Edges exist but coverage < T_void — logic chain broken
    CONTRADICTORY_SILENCE = "CONTRADICTORY_SILENCE"    # Repulsion boundary blocks any bridge — synthesis impossible


class VoidStatus(str, Enum):
    OPEN = "OPEN"            # Gap is unresolved, awaiting inquiry answer or new data
    RESOLVED = "RESOLVED"    # Gap was filled in a subsequent analysis pass


class InquiryResult(BaseModel):
    """
    Structured inquiry generated by InquiryGenerator for a COGNITIVE_VOID.
    Contains a specific bridging hypothesis and a list of required facts.
    """
    void_node_id: str
    pole_a_anchor_id: str
    pole_b_anchor_id: str
    inquiry_question: str           # "For closure at void X between A and B, hypothesis H requires confirmation"
    hypotheses: List[str] = Field(default_factory=list)  # Specific facts that would close the void
    void_type: VoidType = VoidType.EMPIRICAL_GAP
    tentative_edge_ids: List[str] = Field(default_factory=list)


class CognitiveVoidMetadata(BaseModel):
    """
    Metadata embedded in COGNITIVE_VOID ClaimNodes.
    Tracks the structural gap, its classification, and the active inquiry.
    When resolved, archival fields are populated and void_status → RESOLVED.
    """
    void_type: VoidType = VoidType.EMPIRICAL_GAP
    void_status: VoidStatus = VoidStatus.OPEN
    pole_a_anchor_id: str = ""
    pole_b_anchor_id: str = ""
    gap_coverage_score: float = 0.0          # Stem overlap coverage between the two anchor poles
    max_path_weight: float = 0.0             # Max edge weight of any existing path A → B
    inquiry: Optional[InquiryResult] = None
    # Resolution archival (Aris Directive #8: history is preserved, not deleted)
    resolved_evidence_text: Optional[str] = None    # Evidence text that closed the void
    resolved_confidence: float = 0.0                # Confidence score at resolution time
    resolved_edge_id: Optional[str] = None          # ID of the new bridging edge replacing TENTATIVE_BRIDGE
    # Epistemic Synthesis Loop (Aris Directive #10)
    proposals_history: List[ProposedResolution] = Field(default_factory=list)


# =============================================================================
# Aris Directive #10: Epistemic Synthesis Loop & Verification Models
# =============================================================================

class ResolutionStatus(str, Enum):
    PROPOSED = "PROPOSED"                       # Proposal submitted for verification
    VERIFIED = "VERIFIED"                       # Dual-pole NLI verification passed
    CONFLICT = "CONFLICT"                       # Contradiction detected with one/both poles
    REJECTED_UNSUPPORTED = "REJECTED_UNSUPPORTED" # Neutral / unrelated text without evidence


class ConflictResolutionStrategy(str, Enum):
    NONE = "NONE"                                       # No conflict
    REVISE_POLES = "REVISE_POLES"                       # Re-examine formulations of anchor poles
    TRIANGULATE_THIRD_POLE = "TRIANGULATE_THIRD_POLE"   # Introduce intermediate mediating concept
    ARBITRATE_EXTERNAL_SOURCE = "ARBITRATE_EXTERNAL_SOURCE" # Require authoritative benchmark/source


class ConflictDetail(BaseModel):
    """
    Structured explanation of a verification conflict (Aris Directive #10).
    Provides machine and human-readable diagnostics.
    """
    pole_id: str
    pole_label: str                                     # "A" or "B"
    contradiction_score: float
    entailment_score: float
    snippet_pole: str = ""
    snippet_evidence: str = ""
    reason: str = ""


class ProposedResolution(BaseModel):
    """
    Structured proposal for resolving a Cognitive Void (Aris Directive #10).
    Tracks the full lifecycle from submission to verification and integration.
    """
    proposal_id: str = Field(default_factory=lambda: f"prop_{uuid.uuid4().hex[:8]}")
    void_id: str
    evidence_text: str
    evidence_source: str = ""
    confidence_score: float = 0.0
    status: ResolutionStatus = ResolutionStatus.PROPOSED
    pole_a_entailment: float = 0.0
    pole_a_contradiction: float = 0.0
    pole_b_entailment: float = 0.0
    pole_b_contradiction: float = 0.0
    conflict_details: Optional[ConflictDetail] = None
    conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.NONE
    created_edge_id: Optional[str] = None
    created_at_epoch: float = 0.0


# =============================================================================
# Aris Directive #11: Cognitive Topology & Dynamic Clustering Models
# =============================================================================

class DomainZoneType(str, Enum):
    CRYSTALLIZED_KNOWLEDGE = "CRYSTALLIZED_KNOWLEDGE" # High density, low conflict, high epistemic confidence
    TURBULENCE_ZONE = "TURBULENCE_ZONE"               # High density, high conflict (repulsion ratio >= 0.30)
    PARADOX_CORE = "PARADOX_CORE"                     # High density + high conflict + high epistemic confidence (dialectical crucible)
    COGNITIVE_WASTELAND = "COGNITIVE_WASTELAND"       # Low density, high void density
    EMERGING_FRONTIER = "EMERGING_FRONTIER"           # Moderate density, transitional active synthesis
    EXPLORATION_ZONE = "EXPLORATION_ZONE"             # Aris Directive #16: Heuristic exploration zone with attenuated threshold


class DomainStabilityState(str, Enum):
    STABLE = "STABLE"               # Stability >= 0.65 and 0 critical core voids
    UNSTABLE = "UNSTABLE"           # Stability < 0.35 or ContradictionRatio >= 0.30 or critical void presence
    TRANSITIONAL = "TRANSITIONAL"   # 0.35 <= Stability < 0.65


class CognitiveDomain(BaseModel):
    """
    A clustered macro-community of reasoning nodes (Aris Directive #11).
    Quantifies cluster epistemic health, stability, and turbulence.
    """
    domain_id: str
    label: str                                        # Primary dominant concept / anchor
    member_node_ids: List[str] = Field(default_factory=list)
    zone_type: DomainZoneType = DomainZoneType.EMERGING_FRONTIER
    stability_state: DomainStabilityState = DomainStabilityState.TRANSITIONAL
    stability_score: float = 0.0                      # [0.0, 1.0] with exponential contradiction penalty
    internal_density: float = 0.0
    contradiction_ratio: float = 0.0
    avg_epistemic_confidence: float = 0.0
    void_count: int = 0
    is_overheated: bool = False                       # High activity + high contradiction trigger
    contradiction_alert_required: bool = False        # Actionable alert for analyst/agent
    super_node_id: Optional[str] = None


class MacroSuperNode(BaseModel):
    """
    Abstracted representation of an entire stable cognitive domain (Aris Directive #11).
    Collapses internal detail while preserving boundary bridges and entropy diagnostics.
    """
    super_node_id: str = Field(default_factory=lambda: f"snode_{uuid.uuid4().hex[:8]}")
    domain_id: str
    label: str
    aggregated_epistemic_confidence: float = 0.0
    internal_entropy: float = 0.0                     # Shannon/Variance entropy of member nodes (Aris requirement)
    member_count: int = 0
    boundary_edge_count: int = 0
    strongest_boundary_weights: Dict[str, float] = Field(default_factory=dict) # target_domain -> max_weight
    zone_type: DomainZoneType = DomainZoneType.CRYSTALLIZED_KNOWLEDGE


class TopologyReport(BaseModel):
    """
    Complete topological survey of the Intellectual Contribution Graph.
    """
    domains: List[CognitiveDomain] = Field(default_factory=list)
    crystallized_count: int = 0
    turbulence_count: int = 0
    paradox_core_count: int = 0
    wasteland_count: int = 0
    overheated_domains: List[str] = Field(default_factory=list)
    super_nodes: List[MacroSuperNode] = Field(default_factory=list)
    global_modularity_score: float = 0.0


# =============================================================================
# Aris Directive #12: Cognitive Steering & Resource Allocation Models
# =============================================================================

class SteeringAction(str, Enum):
    SYNTHESIS_CRUCIBLE = "SYNTHESIS_CRUCIBLE"               # Deep dialectical synthesis in PARADOX_CORE
    CONTRADICTION_RESOLUTION = "CONTRADICTION_RESOLUTION"   # Conflict arbitration in TURBULENCE_ZONE
    VOID_SETTLEMENT = "VOID_SETTLEMENT"                     # Inquiry / Void resolution in WASTELAND
    FRONTIER_EXPANSION = "FRONTIER_EXPANSION"               # Expansion and crystallization in EMERGING_FRONTIER
    ARCHIVE_MONITORING = "ARCHIVE_MONITORING"               # Background monitoring in CRYSTALLIZED_KNOWLEDGE


class SteeringTarget(BaseModel):
    """
    High-value target for directed synthesis and cognitive attention (Aris Directive #12).
    """
    target_id: str
    label: str
    zone_type: DomainZoneType
    value_score: float                                      # Computed target value with damping
    allocated_compute_units: int = 0                        # Budget allocated out of total budget
    budget_percentage: float = 0.0                          # Percentage of total compute (e.g. 85.0%)
    recommended_action: SteeringAction = SteeringAction.FRONTIER_EXPANSION
    iteration_count: int = 0                                # Number of prior steering passes (for damping)
    member_node_ids: List[str] = Field(default_factory=list)


class SteeringReport(BaseModel):
    """
    Cognitive resource allocation and attention distribution plan.
    """
    targets: List[SteeringTarget] = Field(default_factory=list)
    total_compute_budget: int = 1000
    top_priority_target_id: Optional[str] = None
    paradox_allocation_percentage: float = 0.0
    archive_allocation_percentage: float = 0.0
    feedback_recomputed: bool = False


# =============================================================================
# Aris Directive #14: Dynamic Knowledge Harvesting & Cross-Domain Models
# =============================================================================

class ProposedCrossDomainBridge(BaseModel):
    """
    Candidate semantic bridge connecting disparate cognitive domains (Aris Directive #14 / #15 / #16).
    """
    bridge_id: str = Field(default_factory=lambda: f"bridge_{uuid.uuid4().hex[:8]}")
    source_node_id: str
    target_node_id: str
    source_domain_id: str
    target_domain_id: str
    semantic_similarity: float = 0.0
    topological_isomorphism: float = 0.0
    resonance_score: float = 0.0
    proposed_hypothesis: str
    is_validated: bool = False
    refutation_pressure: float = 0.0                        # Aris Directive #15: Measured counter-refutation score
    refutation_node_id: Optional[str] = None                # Aris Directive #15: Node that generated contradiction
    refutation_evidence_text: Optional[str] = None          # Aris Directive #15: Text trace of counter-evidence
    reinforcement_state: str = "UNVERIFIED"                 # "REINFORCED", "SPECULATIVE", "UNVERIFIED"
    is_exploratory: bool = False                            # Aris Directive #16: Born inside ExplorationZone
    exploration_timestamp: float = Field(default_factory=lambda: time.time()) # Aris Directive #16: Time audit
    tunneling_hops: List[str] = Field(default_factory=list) # Aris Directive #16: Intermediate lemma trajectory
    tunneling_potential: float = 0.0                        # Aris Directive #16: Structural tunneling score


class SynthesisThesis(BaseModel):
    """
    Structured semantic thesis and intellectual gain resulting from verified synthetic bridges (Aris Directive #17).
    """
    thesis_id: str = Field(default_factory=lambda: f"thesis_{uuid.uuid4().hex[:8]}")
    bridge_id: str
    source_node_id: str
    target_node_id: str
    synthesis_claim: str
    novelty_score: float = 0.0
    explanatory_power: float = 0.0
    verifiability_score: float = 0.0
    tautology_score: float = 0.0
    utility_gain: float = 0.0
    is_circular: bool = False
    is_tautological: bool = False
    created_at_epoch: float = Field(default_factory=lambda: time.time())


class SynthesisVectorScore(BaseModel):
    """
    Vectorized Synthesis Coefficient K_synth: Quantity vs Quality (Aris Directive #14).
    """
    k_quant: float = 0.0            # Structural cross-domain expansion metric
    k_qual: float = 0.0             # Epistemic confidence and NLI validation quality
    k_composite: float = 0.0        # Combined geometric synthesis coefficient
    active_bridges_count: int = 0
    open_voids_count: int = 0
    epistemic_stability: float = 0.0


class IngestionBatchResult(BaseModel):
    """
    Summary report of mass batch ingestion through quarantine layer.
    """
    total_submitted: int = 0
    promoted_to_active: int = 0
    quarantined_to_wasteland: int = 0
    rejected_contradictions: int = 0
    active_claim_node_ids: List[str] = Field(default_factory=list)
    quarantined_node_ids: List[str] = Field(default_factory=list)


class CrossDomainDiscoveryReport(BaseModel):
    """
    Complete survey of latent cross-domain bridges and synthesis consolidation.
    """
    proposed_bridges: List[ProposedCrossDomainBridge] = Field(default_factory=list)
    validated_bridges: List[ProposedCrossDomainBridge] = Field(default_factory=list)
    synthesis_coefficient: SynthesisVectorScore = Field(default_factory=SynthesisVectorScore)






class SynthesisMetadata(BaseModel):
    parent_premise_ids: List[str] = Field(default_factory=list)
    novel_relational_contribution: bool = False
    source_novelty_score: float = 0.0
    ablation: Optional[AblationResult] = None
    external_attribution: Optional[ExternalAttribution] = None
    is_missing_required_premise: bool = False
    resonance: Optional[ResonanceMetadata] = None
    emergent_topology: Optional[EmergentTopologyMetadata] = None
    paradox_container: Optional[ParadoxContainerMetadata] = None
    cognitive_void: Optional[CognitiveVoidMetadata] = None   # Aris Directive #7: CVM


class LayerSignals(BaseModel):
    ai_probability: Optional[float] = None
    ai_confidence_interval: Optional[Tuple[float, float]] = None
    plagiarism_match_id: Optional[str] = None
    plagiarism_similarity: Optional[float] = None
    author_style_z_score: Optional[float] = None


class ClaimNode(BaseModel):
    id: str
    type: NodeType = NodeType.CLAIM
    contribution_class: ContributionClass = ContributionClass.UNKNOWN
    span: TextSpan
    proposition: Optional[Proposition] = None
    synthesis_metadata: Optional[SynthesisMetadata] = None
    layer_signals: LayerSignals = Field(default_factory=LayerSignals)
    confidence: float = 0.0
    epistemic_confidence: float = 0.0  # confidence * sqrt(ECC)
    sources_cited: List[str] = Field(default_factory=list)
    section_title: Optional[str] = None
    discipline_domain: Optional[str] = None
    is_anchor: bool = False
    is_super_anchor: bool = False
    resonance_frequency: float = 1.0                            # Dialectical frequency (2.5 for Super-Anchors)
    is_contested: bool = False                                 # True when under unresolved dialectical conflict
    is_quarantined: bool = False                              # Isolated in quarantine bubble
    support_to_conflict_ratio: float = 0.0                     # Evidence escalation ratio (requires > 3.0 to exit)
    contested_reasons: List[str] = Field(default_factory=list)


class EdgeWeightDetails(BaseModel):
    semantic_similarity: float = 0.0     # alpha * Sim
    causal_necessity: float = 0.0        # beta * Necessity
    discourse_role_weight: float = 0.0   # gamma * Role
    raw_score: float = 0.0
    gravity_bonus: float = 0.0           # Added via synthesis gravity
    repulsion_force: float = 0.0         # Negative gravity force (Aris Directive #5)
    tension_force: float = 0.0           # Dynamic tension force during bridging
    final_weight: float = 0.0            # Normalized in [-1.0, 1.0]
    status: EdgeStatus = EdgeStatus.CORE_ACTIVE_LINK
    is_protected_synthesis_bridge: bool = False
    is_bypassed_redundant: bool = False
    resonance_amplifier: float = 1.0      # Amplifies resonance in cross-domain bridges (Aris Directive #14-16)


class EdgeEvidence(BaseModel):
    edge_id: str = Field(default_factory=lambda: f"edge_{uuid.uuid4().hex[:8]}")
    source_node_id: str
    target_node_id: str
    relation_type: RelationType
    entailment_score: float = 0.0
    contradiction_score: float = 0.0
    counterfactual_passed: bool = True
    fallacy_type: Optional[str] = None
    evidence_excerpt: str = ""
    weight: float = 1.0
    status: EdgeStatus = EdgeStatus.CORE_ACTIVE_LINK
    weight_details: Optional[EdgeWeightDetails] = None


class MetricsSummary(BaseModel):
    reproduction_ratio: float = 0.0
    synthesis_ratio: float = 0.0
    source_novel_synthesis_ratio: float = 0.0
    higher_order_synthesis_ratio: float = 0.0
    original_contribution_ratio: float = 0.0
    inference_ratio: float = 0.0
    unsupported_ratio: float = 0.0
    contradictory_ratio: float = 0.0
    unknown_ratio: float = 0.0
    
    # Core ICG Structural Indices
    novelty_score: float = 0.0
    synthesis_depth: float = 0.0
    inference_depth: float = 0.0
    source_integration: float = 0.0
    evidence_coverage: float = 0.0
    reasoning_coherence: float = 0.0
    
    # ICG v0.4 Corpus & Epistemic Metrics
    external_corpus_coverage: float = 0.85  # ECC
    global_epistemic_confidence: float = 0.0
    
    # Graph Density & Edge Filtering Metrics (Aris Directive #2)
    graph_density_raw: float = 0.0
    graph_density_filtered: float = 0.0
    core_edges_count: int = 0
    weak_edges_count: int = 0
    decorative_edges_count: int = 0
    
    # Intellectual Resonance & Emergent Topology (Aris Directives #3 & #4)
    active_resonance_nodes_count: int = 0
    max_resonance_score: float = 0.0
    anchor_nodes_count: int = 0
    super_anchor_nodes_count: int = 0
    pruned_redundant_edges_count: int = 0
    
    # Cognitive Immunity & Higher-Order Synthesis (Aris Directives #5 & #6)
    paradox_containers_count: int = 0
    resolved_paradoxes_count: int = 0
    quarantined_nodes_count: int = 0
    repulsion_edges_count: int = 0
    dynamic_tension_edges_count: int = 0
    synthetic_link_edges_count: int = 0

    # Cognitive Void Mapping & Active Inquiry (Aris Directive #7)
    cognitive_voids_count: int = 0          # Total COGNITIVE_VOID nodes created
    tentative_edges_count: int = 0          # Total TENTATIVE edges created
    void_map_json: str = "[]"               # JSON-serialized list of InquiryResult dicts

    # Unified Intellectual Contribution Score
    intellectual_contribution_score: float = 0.0


class ICGGraph(BaseModel):
    graph_id: str = Field(default_factory=lambda: f"icg_{uuid.uuid4().hex[:8]}")
    document_id: str
    nodes: List[ClaimNode] = Field(default_factory=list)
    edges: List[EdgeEvidence] = Field(default_factory=list)
    metrics_summary: MetricsSummary = Field(default_factory=MetricsSummary)
    research_questions: List[str] = Field(default_factory=list)


# -----------------------------------------------------------------------------
# Multi-Annotator Ground Truth & Reality Benchmark Models
# -----------------------------------------------------------------------------

class AnnotatorRecord(BaseModel):
    annotator_id: str
    assigned_class: ContributionClass
    confidence: float = 1.0
    notes: Optional[str] = None


class BenchmarkItem(BaseModel):
    id: str
    discipline: str
    language: str
    text: str
    expected_classes: List[ContributionClass]
    annotators: List[List[AnnotatorRecord]] = Field(default_factory=list)
    agreement_score: float = 1.0
    is_ambiguous: bool = False
    hidden_sources: List[Dict[str, str]] = Field(default_factory=list)
    perturbation_stage: str = "original"
