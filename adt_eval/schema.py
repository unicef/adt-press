from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict, conint, confloat


# =========================
# 1) Pydantic Output Schema
# =========================

class RootCause(BaseModel):
    id: conint(ge=1) = Field(
        ...,
        description="Stable ID for this root cause (start at 1 and increment by 1).",
    )
    area: str = Field(
        ...,
        description=(
            "Area of the template/problem "
            "(e.g., 'role_and_objective', 'output_schema', 'ambiguity', "
            "'examples', 'tool_usage', 'reasoning_guidance', 'guardrails', "
            "'routing_logic', 'metric_alignment')."
        ),
    )
    explanation: str = Field(
        ...,
        description=(
            "Detailed, actionable explanation of what is wrong or missing in the "
            "prompt_template (not in model weights), written so a prompt engineer can act on it."
        ),
    )
    pattern_across_cases: Optional[str] = Field(
        None,
        description=(
            "Summary of how this issue manifests across multiple cases "
            "(e.g., recurring formatting errors, systematic confusion between two intents)."
        ),
    )
    affected_cases: List[int] = Field(
        default_factory=list,
        description="List of case_no values where this root cause appears.",
    )


class Fix(BaseModel):
    id: conint(ge=1) = Field(
        ...,
        description="Stable ID for this fix (start at 1 and increment by 1).",
    )
    type: str = Field(
        ...,
        description=(
            "Type of fix (e.g., 'add_constraint', 'clarify_objective', 'format_schema', "
            "'negative_guidance', 'improve_examples', 'tool_instruction', "
            "'reasoning_guidance', 'metric_alignment')."
        ),
    )
    target_section: str = Field(
        ...,
        description=(
            "Which part of the prompt/template this fix applies to "
            "(e.g., 'system_instructions', 'output_schema', 'examples', 'tool_choice', "
            "'reasoning_section', 'guardrails_and_refusals')."
        ),
    )
    text: str = Field(
        ...,
        description=(
            "Concrete, copy-pasteable instruction/snippet to insert or modify in the "
            "prompt_template. This should be ready to drop into the prompt."
        ),
    )
    rationale: str = Field(
        ...,
        description=(
            "Why this fix should improve behavior and metrics, referencing the observed "
            "patterns and root causes."
        ),
    )
    addresses_root_causes: List[int] = Field(
        ...,
        description="List of RootCause.id values this fix is designed to mitigate.",
    )


class Evidence(BaseModel):
    prompt_quotes: List[str] = Field(
        default_factory=list,
        description=(
            "Relevant snippets from the prompt_template (verbatim or near-verbatim) that "
            "show problematic instructions, gaps, or ambiguities."
        ),
    )
    response_quotes: List[str] = Field(
        default_factory=list,
        description=(
            "Relevant snippets from model responses that illustrate failures or "
            "suboptimal behavior (e.g., hallucinations, schema violations, weak reasoning, style issues)."
        ),
    )
    request_features: List[str] = Field(
        default_factory=list,
        description=(
            "Salient patterns or features in the requests that interact with prompt "
            "weaknesses (e.g., length, ambiguity, domain-specific jargon, multi-step tasks)."
        ),
    )
    case_ids: List[int] = Field(
        default_factory=list,
        description="case_no values that the above evidence is drawn from.",
    )


class PerCaseAnalysis(BaseModel):
    case_no: int = Field(
        ...,
        description="Identifier for the case, as provided in the prompt_analysis_job_order.",
    )
    short_summary: str = Field(
        ...,
        description=(
            "1–3 sentence description of what the agent was supposed to do, what it "
            "actually did, and why this behavior is failing or suboptimal."
        ),
    )
    outcome_severity: Literal[
        "hard_failure",
        "borderline",
        "acceptable_but_improvable",
    ] = Field(
        ...,
        description=(
            "How severe the issue is for this case: "
            "'hard_failure' (clearly wrong/unsafe), "
            "'borderline' (partially acceptable but with notable issues), or "
            "'acceptable_but_improvable' (meets minimum bar but metrics/quality could be improved)."
        ),
    )
    expected_label_from_rationale: Optional[str] = Field(
        None,
        description=(
            "Expected label/route for this case (if applicable), inferred from the "
            "prompt_template and/or reason_for_optimization. Useful for routing or classification prompts."
        ),
    )
    predicted_label_if_known: Optional[str] = Field(
        None,
        description=(
            "Label/route that the model appears to have used, if it can be inferred "
            "from the response (for routing/classification scenarios)."
        ),
    )
    expected_behavior: Optional[str] = Field(
        None,
        description=(
            "Optional explicit description of the ideal behavior/output for this case, "
            "in plain language."
        ),
    )
    actual_behavior: Optional[str] = Field(
        None,
        description=(
            "Optional explicit description of the observed behavior/output for this case, "
            "in plain language."
        ),
    )
    issue_type: Optional[str] = Field(
        None,
        description=(
            "Categorization of the main issue for this case, "
            "e.g., 'schema_violation', 'metric_below_threshold', "
            "'hallucination', 'over_refusal', 'style_mismatch'."
        ),
    )
    metric_signals: List[str] = Field(
        default_factory=list,
        description=(
            "Free-text notes summarizing key metric-related signals for this case "
            "(e.g., 'LaBSE score 0.55 < 0.60 threshold', 'low adequacy', 'fluency good, adequacy weak')."
        ),
    )
    contributing_root_causes: List[int] = Field(
        default_factory=list,
        description="List of RootCause.id values that explain this specific case's issues.",
    )


class PromptAnalystOutput(BaseModel):
    """
    JSON schema for the Prompt Analyst & Optimizer Agent output for multiple cases
    requiring optimization (failures and suboptimal behaviors).
    """
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(
        ...,
        description=(
            "One-paragraph overview of how effective the current prompt_template is, "
            "highlighting key weaknesses, systemic issues, and optimization goals."
        ),
    )
    global_behavior_patterns: List[str] = Field(
        default_factory=list,
        description=(
            "High-level patterns that show up across multiple cases, including failures "
            "and suboptimal-but-acceptable outputs (e.g., 'translations preserve meaning "
            "but omit numeric ranges', 'router confuses FAQ vs escalation')."
        ),
    )
    per_case_analysis: List[PerCaseAnalysis] = Field(
        ...,
        description=(
            "Per-case breakdown of issues, with severity, metric signals, and links to root causes."
        ),
    )
    root_causes: List[RootCause] = Field(
        ...,
        description="List of identified root causes with IDs, explanations, and affected cases.",
    )
    evidence: Evidence = Field(
        default_factory=Evidence,
        description="Supporting quotes/evidence aggregated across the analyzed cases.",
    )
    fixes: List[Fix] = Field(
        ...,
        description=(
            "Actionable fixes tied to root causes and target sections of the prompt_template."
        ),
    )
    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description=(
            "Explicit, implementation-ready criteria that the revised prompt must satisfy "
            "(e.g., 'All outputs strictly follow the JSON schema', "
            "'Ambiguous requests default to clarification questions rather than hallucination')."
        ),
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        "medium",
        description=(
            "Overall risk rating for the current prompt/template in terms of correctness, "
            "safety, robustness, or business impact."
        ),
    )
    confidence: confloat(ge=0.0, le=1.0) = Field(
        0.7,
        description=(
            "Confidence score (0.0–1.0) for this analysis and the proposed fixes, "
            "based on pattern clarity, evidence strength, and coverage."
        ),
    )



class ChangeLogEntry(BaseModel):
    """
    Optional helper model for internal logging/debugging of changes.
    NOTE: This is NOT a top-level field in PromptOptimizerOutput anymore.
    """
    description: str = Field(
        ...,
        description="Human-readable description of a change made to the prompt.",
    )
    target_section: str = Field(
        ...,
        description=(
            "Which part of the prompt was changed "
            "(e.g., 'system_instructions', 'output_schema', 'examples', "
            "'tool_choice', 'reasoning_section', 'guardrails_and_refusals')."
        ),
    )
    related_root_causes: List[conint(ge=1)] = Field(
        default_factory=list,
        description="IDs of RootCause items (from analyst_output) that this change addresses.",
    )
    related_fixes: List[conint(ge=1)] = Field(
        default_factory=list,
        description="IDs of Fix items (from analyst_output) that informed this change.",
    )


class UserFeedbackDecision(BaseModel):
    """
    Optional helper model describing how individual user feedback items were treated.
    Can be used to construct the incorporated_user_feedback strings.
    """
    feedback_item: str = Field(
        ...,
        description="The user-requested improvement or instruction.",
    )
    applied: bool = Field(
        ...,
        description="True if the feedback was applied, False if it was not applied.",
    )
    reason: str = Field(
        ...,
        description="Short explanation for why it was applied or not applied.",
    )


class PromptOptimizerOutput(BaseModel):
    """
    Output of the Prompt Optimizer step.

    This schema is aligned with the new PROMPT_OPTIMIZER_SYSTEM_PROMPT:
    the LLM must return ONLY these fields, with no extras.
    """
    model_config = ConfigDict(extra="forbid")

    prompt_name: str = Field(
        ...,
        description=(
            "Name of the revised prompt."
        ),
    )

    revised_prompt_template: str = Field(
        ...,
        description=(
            "Full, production-ready prompt template in the same templating style as "
            "the original (e.g., banks-style chat blocks + Jinja placeholders)."
        ),
    )

    improvement_summary: str = Field(
        ...,
        description=(
            "1–3 paragraphs summarizing the main changes, the root causes they address, "
            "and how these changes are expected to improve relevant metrics on the cases."
        ),
    )

    incorporated_user_feedback: List[str] = Field(
        default_factory=list,
        description=(
            "Bullet-style list (as plain strings) describing how user feedback was "
            "handled: which items were applied and how, and optionally which were not "
            "applied and why."
        ),
    )

    acceptance_criteria: List[str] = Field(
        default_factory=list,
        description=(
            "Final acceptance criteria that the revised prompt is designed to satisfy. "
            "Derived from analyst_output.acceptance_criteria, possibly tightened or clarified, "
            "and aligned with metrics and test_cases."
        ),
    )


class TranslationEvalOutput(BaseModel):
    is_translation_acceptable: bool
    rationale: str