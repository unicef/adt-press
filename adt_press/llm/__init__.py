import litellm

# set callbacks
litellm.success_callback = ["langfuse"]
litellm.failure_callback = ["langfuse"]
