def jaccard(list1, list2):
    '''Calculate the Jaccard similarity between two lists.
    
    Args:
        list1 (list): First list of items.
        list2 (list): Second list of items. 
        
    Returns:
        float: Jaccard similarity score.
    '''

    s1 = set(list1)
    s2 = set(list2)

    intersection = s1.intersection(s2)
    union = s1.union(s2)

    jaccard_similarity = float(len(intersection) / len(union))

    return jaccard_similarity