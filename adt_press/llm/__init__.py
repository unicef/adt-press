import os

import litellm
import mlflow

# if langfuse is configured, set up callbacks for litellm
if os.getenv("LANGFUSE_HOST"):
    # set callbacks
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

# if mlflow is configured, set up autologging
if os.getenv("MLFLOW_TRACKING_URI"):
    # Enable auto-tracing for LiteLLM
    mlflow.litellm.autolog()
