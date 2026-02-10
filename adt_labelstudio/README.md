# Adding tasks to LabelStudio

## Overview

This folder describes how to add projects and tasks to LabelStudio for human annotations.  Currently we have defined the following projects:

ID | Name | Description
---|---|---
AO | Validation-test split |
A1 | Text transcription | Ensure all text properly extracted from PDF
A2 | Text type | Assign each line of text to a `text_type`
A3 | Group type | Assign lines of text to groups with `group_type`
A4 | Section type | Assign lines of text to sections with `section_type`
A5 | ELI5 | Explain a paragraph like I'm 5.
A6 | Easy Read | Convert a paragraph of text to easy read style.
B2 | Image relevance | Determine if an image is relevant or not
B4 | Image captioning | Write a caption for the image

B1 was reserved for image extraction and B3 was reserved for image cropping. However, these were assumed to be working well and so do not have human evaluations. Furthermore, translation is currently not human evaluated.

## Defining LabelStudio project structure

`task_instructions` refer the instructions that pop up to annotators when they first open a task in the project. They align with the prompts that are given to the LLM in the pipeline (as the annotator is doing the same task we are assigning to the LLM). In the GUI for each LabelStudio project, they should be entered under `Settings > Annotation > Labeling Instructions`.

`task_definitions` refers to the HTML code that defines the labeling interface for the tasks in a project. In the GUI for each LabelStudio project, they should be entered under `Settings > Labeling Interface > Code`.

To get page images to render in LabelStudio you must set up cloud storage. The steps are as follows.

1. Go to `Settings > Cloud Storage > Add Source Storage`
2. Click `Azure Blob Storage`
3. Set title: `Azure`
4. Set container name: `adt-pipeline`
5. Copy `AZURE_STORAGE_ACCOUNT_NAME` and `AZURE_STORAGE_ACCOUNT_KEY` from the `.env` file.
6. Disable `Use pre-signed URLs`
7. Click through and test.

Once you are done with this, you need to load actual tasks into the projects for the annotators to complete.

## Defining individual tasks

LabelStudio tasks are passed to projects as a list of dictionaries, with one dictionary per task. The task definition consists of two main components:
- `data`: This is data that you want to be associated with the task. 
  - Often it contains fields that are used in rendering the task (for example, for the `text_type` task, it would include the text that needs to be categorized by type)
  - It can also include additional metatada for the task (such as `book_id` or `page_id`).
- `predictions`: These are pre-annotations that can be loaded to help speed up the work of the annotator. In our case, we use the LLM to predict the annotation, and have the user correct the candidate annotation.
  - These predictions have a field called `value` that defines what the predicted annotation is. Depending on the task, this must be structured in a specific way.
  - The `from_name` has the name of the field where the annotation will be stored.
  - The `to_name` is the field with the content being annotated.
  - The `type` field refers to the task type.

Tasks can be loaded to LabelStudio via the Python API, or uploaded in the Labelstudio GUI as a JSON file.

## Code structure
The notebooks `add_to_ls_...` implement the workflow for pushing tasks from the LLM logs to LabelStudio. They rely on a `BaseTask` class implemented in `base.py` and then task-specific subclasses (`GroupTypeTask`, `TextTypeTask`, etc.) which inherit from it. There is also a `utils.py` file with LabelStudio specific functions.

**Big picture:** Some tasks (the first in their respective workflow -- e.g. `validation_test_split`, `text_transcription`, `image_relevance`) pull directly from the LLM log output _only_ to create the new task. However tasks at later steps in the workflow also need to pull from Gold Standard, human-created annotations completed in the _previous_ task. For example, the `text_type` task needs to draw on the Gold Standard, human-corrected _text transcripts_, and create candidate annotations for text type from the LLM log output. Thus the Gold Standard transcripts need to be matched with the candidate annotations from the LLM to define the task.

Thus the basic workflow is as follows:

1. We define the source project for Gold Standard annotations, and the target project we're trying to annotate. 
2. We get existing annotations for the target project and test if the task we're trying to create already exists in LabelStudio. If so, we don't create the task again (so as not to overwrite annotations that have already been entered).
3. If not, we get the Gold Standard annotations (where applicable) as well as the LLM logs, and merge the two together.
4. Then, we structure the data and predictions needed to populate the task dictionary.
5. Finally, we load the list of tasks to LabelStudio and also download the JSON to disk for inspection.
	
## ToDo:
- Add task instructions for grouping