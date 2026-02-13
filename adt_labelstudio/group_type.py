
from typing import Dict, List
import pandas as pd
from adt_labelstudio.base import BaseTask
from adt_eval.utils.transcript_cleaner import standardize_transcript, normalize_transcript

class GroupTypeTask(BaseTask):

    def get_single_annotation(self, gs_annotations:pd.DataFrame, book_id:str, page_id:int) -> Dict:
        '''Retrieve a single annotation from a dataframe of annotations.
        In this case lookup is done by book ID and page ID as this defines the annotation task.'''
        
        gs_annotation = gs_annotations[(gs_annotations['book_id'] == book_id) & (gs_annotations['page_id'] == page_id)]
 
        if gs_annotation.shape[0] == 0:
            raise ValueError(f"No annotation found for book '{book_id}', page ID {page_id}")
        if gs_annotation.shape[0] > 1:
            raise ValueError(f"Multiple annotations found for book '{book_id}', page ID {page_id}")
        
        return gs_annotation.iloc[0].to_dict()
    
    def populate_task_data(self, gs_annotation:Dict) -> Dict:
        ''' Define the data used to render the task in LabelStudio '''

        text = "\n\n".join([i.strip() for i in gs_annotation['page_text_all_corrected'].split("\n\n")])

        data = {
                    "book_id": gs_annotation['book_id'],
                    "page_id": gs_annotation['page_id'],
                    "page_image": f"azure-blob://adt-pipeline/evaluation/gold_standard/pages/{gs_annotation['book_id']}__page_{gs_annotation['page_id']+1}.png",
                    "page_text_all": text,
                }
        
        return data
    
    def load_llm_log_to_df(self, llm_log:Dict) -> pd.DataFrame:
        ''' Converts json log from an LLM run to a dataframe that can be used'''

        # Construct dataframe
        llm_data = pd.DataFrame(columns=["text_id", "book_id", "page_number", "page_id", "reasoning", "group_id", "group_type", "llm_text", "text_type", "is_pruned"])

        ##############
        # Add columns from input data
        page_id = llm_log['inputs']['page']['page_id']
        book_id = llm_log['inputs']['page']['book_id']
        page_number = llm_log['inputs']['page']['page_number']

        ##############
        # Add columns from output data
        reasoning = llm_log['output']['reasoning']

        # Group level data
        for g in llm_log['output']['groups']:
            group_id = g['group_id']
            group_type = g['group_type']

            # Text level data
            for t in g['texts']:
                text_id = t['text_id']
                text = t['text'] 
                text_type = t['text_type']
                is_pruned = t['is_pruned']
                    
                llm_data.loc[text_id] = [text_id, book_id, page_number, page_id, reasoning, group_id, group_type, text, text_type, is_pruned]

        llm_data['group_number'] = llm_data['group_id'].apply(lambda x: int(x.split('_g')[-1]))

        return llm_data
    def load_gs_annotation_to_df(self, gs_annotation:Dict) -> pd.DataFrame:
        ''' Converts Gold Standard annotation from LabelStudio to a dataframe that can be used '''

        # Get GS transcript from LabelStudio 
        gs_data = pd.DataFrame(gs_annotation['page_text_all_corrected'].split("\n\n"), columns = ["gs_text"])

        # Add details for calculating start and end indices
        gs_data['gs_text'] = gs_data['gs_text'].str.strip()
        gs_data['gs_text_length'] = gs_data['gs_text'].str.len()

        gs_data['gs_start_index'] = gs_data['gs_text_length'].cumsum().shift().fillna(0).astype(int)

        # Add spacing between text segments (right now, this is 2 because "\n\n" is 2 characters)
        gs_data['gs_start_index'] += (
                2 * gs_data.index.get_level_values(0)
            ) 

        gs_data['gs_end_index'] = gs_data['gs_start_index'] + gs_data['gs_text_length']

        gs_data.drop(columns=['gs_text_length'], inplace=True)

        return gs_data
    
    def merge_gs_with_llm(self, gs_df: pd.DataFrame, llm_df: pd.DataFrame) -> pd.DataFrame:
        ''' Merge Gold Standard dataframe with LLM dataframe based on exact text matches after normalization '''

        # Normalized text for matching
        gs_df['gs_text'] = gs_df['gs_text'].apply(lambda x: standardize_transcript(normalize_transcript(x)))
        llm_df['llm_text'] = llm_df['llm_text'].apply(lambda x: standardize_transcript(normalize_transcript(x)))

        llm_text_list = [xy for xy in zip(llm_df['llm_text'], llm_df['text_id'])]

        # Seek exact match
        gs_df['text_id'] = ''

        for i, row in gs_df.iterrows():
            for j in llm_text_list:
                if row['gs_text'] == j[0]:
                    gs_df.loc[i, 'text_id'] = j[1]
                    llm_text_list.remove(j)
                    break

        full_df = gs_df.merge(llm_df, on='text_id', how='left')
        full_df = full_df.fillna("")

        return full_df

    def populate_task_predictions(self, matched_df: pd.DataFrame) -> List[Dict]:
        ''' Define the predictions (pre-annotations) used to render the task in LabelStudio '''
    
        result = []
        if self.check_validity_of_groupings(matched_df):
            group_spans = self.get_group_spans(matched_df)
            for k, v in group_spans.items():
                result.append({
                    "value": {
                        "text": v['gs_text'],
                        "taxonomy": [[v['group_type']]],
                        "start": v['gs_start_index'],
                        "end": v['gs_end_index']
                    },
                    "from_name": "group_type_annotations",
                    "to_name": "page_text_all",
                    "type": "taxonomy"
                })
        predictions = [{"result": result}]
        return predictions
    
    def check_validity_of_groupings(self, matched_df: pd.DataFrame) -> bool:
        ''' Check that group numbers are non-decreasing and that groups are not shuffled together '''

        # Consider only rows with group numbers
        matched_df = matched_df[matched_df['group_number']!=''].copy()
        matched_df['group_number'] = matched_df['group_number'].astype(int)
        if matched_df.shape[0] == 0:
            print("No group numbers found in the data. No pre-annotations added.")
            return False
        
        # Check that group numbers are non-decreasing
        #matched_df['is_monotonic'] = (matched_df['group_number'].diff().fillna(0) >= 0) 

        # Check that groups are not split - i.e. lines from different groups are not shuffled together
        matched_df['previous_groups'] = matched_df.apply(lambda row: list(set(matched_df.loc[:row.name-1, 'group_number'].tolist())) if row.name > 0 else [], axis=1)
        matched_df['is_in_previous_groups'] = matched_df.apply(lambda row: row['group_number'] in row.previous_groups, axis=1)
        matched_df['is_shuffled'] = ((matched_df['group_number']!=matched_df['group_number'].shift()) & matched_df['is_in_previous_groups']) #  "Group numbers must be non-decreasing"

        if (~matched_df['is_shuffled'] #& matched_df['is_monotonic']
            ).all():
            return True
        else:
            print("Groupings are invalid: groups are shuffled together. No pre-annotations added.")
                # either groups are out of order or " \
            return False
    
    def get_group_spans(self, matched_df: pd.DataFrame) -> Dict:
        '''Get spans of valid groups'''

        
        # Consider only rows with group numbers
        matched_df = matched_df[matched_df['group_id']!=''].copy()

        #matched_df['llm_group_start_index'] = matched_df.groupby('group_number', as_index=False)['gs_start_index'].transform('min')
        #matched_df['llm_group_end_index'] = matched_df.groupby('group_number', as_index=False)['gs_end_index'].transform('max')
        group_spans = matched_df.groupby(['group_id']).agg({'gs_start_index':'min', 
                                                            'gs_end_index':'max',
                                                            'group_type':'unique',
                                                            'gs_text':'\n\n'.join,
                                                            })
        
        assert (group_spans['group_type'].apply(lambda x: len(x))==1).all()
        group_spans['group_type'] = group_spans['group_type'].apply(lambda x: list(x)[0])
        group_spans = group_spans.to_dict(orient='index')
        return group_spans