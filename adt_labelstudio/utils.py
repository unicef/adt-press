import pandas as pd
def get_ls_project_id_from_name(ls_client, project_name):
    ''' Retrieve LabelStudio Project ID corresponding to the Project Name'''
    
    response = ls_client.projects.list()
    project_ids = { i.title: i.id for i in response.items }
    project_id = project_ids[project_name]
    return project_id

def get_project_annotations(ls_client, project_name: str) -> pd.DataFrame:
    ''' 
    Retrieve LabelStudio Annotations for a given project.
    
    Args:
        ls_client: Label Studio client object
        project_name (str): Name of the Label Studio project, e.g. "A1: Text Extraction"

    Returns:
        pd.DataFrame: DataFrame containing the most recent annotations for each task in the project
    
    '''
    # Get the task_id / book and page id crosswalk
    project_id = get_ls_project_id_from_name(ls_client, project_name)

    # Retrieve project data from Label Studio
    project = ls_client.projects.get(id=project_id)
    ls_data = ls_client.projects.exports.as_pandas(project.id)

    # For a given task, keep only the latest annotation
    if ls_data.empty:
        return ls_data
    
    ls_data.sort_values(['id',"updated_at"], ascending=False, inplace=True)
    ls_data.drop_duplicates(subset=['id'], keep='first', inplace=True)

    ### ADD A LINE TO KEEP ONLY ANNOTATED TASKS?

    ls_data.set_index('id', inplace=True)

    return ls_data