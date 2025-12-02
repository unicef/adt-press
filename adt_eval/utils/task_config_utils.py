

def get_experiment_dataset_name(task_config, experiment_name, position=0):
    experiments = task_config.get("experiments", [])

    for exp in experiments:
        if exp.get("name") == experiment_name:
            datasets = exp.get("datasets", [])
            if datasets:
                return datasets[position]['name']   # first dataset
            else:
                return None          # experiment found but datasets empty

    return None  # experiment not found

def get_experiment_prompt_name(task_config, experiment_name, position=0):
    experiments = task_config.get("experiments", [])

    for exp in experiments:
        if exp.get("name") == experiment_name:
            prompts = exp.get("prompts", [])
            if prompts:
                return prompts[position]['name']   # first prompt entry
            else:
                return None         # experiment found but no prompts

    return None  # experiment not found
