import os
from typing import Any

import instructor
import litellm
import mlflow
from litellm import acompletion

from adt_press.utils.logging import configure_litellm_logging

# Configure logging to suppress known LiteLLM bugs
configure_litellm_logging()

# if langfuse is configured, set up callbacks for litellm
if os.getenv("LANGFUSE_HOST"):
    # set callbacks
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

# if mlflow is configured, set up autologging
if os.getenv("MLFLOW_TRACKING_URI"):
    # Enable auto-tracing for LiteLLM
    mlflow.litellm.autolog()


def get_instructor_client(**kwargs: Any):
    """
    Return an Instructor-wrapped LiteLLM client that prefers JSON-schema modes.

    We try newer response-format modes first and gracefully fall back
    to the default Instructor behaviour if those are
    unavailable in the installed Instructor version.
    """
    mode_candidates = [
        "JSON_SCHEMA",
        "JSON",
        "OPENAI_RESPONSE_FORMAT",
    ]

    for attr in mode_candidates:
        mode = getattr(instructor.Mode, attr, None)
        if mode is not None:
            return instructor.from_litellm(acompletion, mode=mode, **kwargs)

    return instructor.from_litellm(acompletion, **kwargs)
