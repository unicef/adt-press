"""Data types and models specific to evaluation."""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class EvaluationMatch(BaseModel):
    """A single evaluation match between expected and actual results."""

    text: str
    expected: Optional[str]
    actual: Optional[str]


class EvaluationResult(BaseModel):
    """Result for a single test case."""

    id: str
    page_text: str
    page_image_path: str
    page_score: float
    step: int
    matches: list[Dict[str, Any]]
    page_texts: Optional[Dict[str, Any]] = None


class EvaluationConfig(BaseModel):
    """Configuration for evaluation runs."""

    limit: int = 10
    rate_limit: int = 5


class LabelStudioConfig(BaseModel):
    """Configuration for Label Studio integration."""

    url: str
    api_key: str


class AzureStorageConfig(BaseModel):
    """Configuration for Azure Storage integration."""

    account_name: str
    account_key: str
