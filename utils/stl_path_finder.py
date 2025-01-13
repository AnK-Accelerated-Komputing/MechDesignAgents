import re

def stl_path_finder(chat_history):
    """
    Finds the path to an STL file mentioned in the chat history.

    Args:
        chat_history (list): A list of dictionaries representing the chat history. 
                             Each dictionary should have 'name' and 'content' keys.

    Returns:
        str: The full path to the STL file if found, otherwise None.
    """
    stl_filename = None
    for entry in chat_history:
        if entry['name'] == 'CadQuery_Code_Writer' and 'stl' in entry['content']:
            # Find the filename (e.g., plate_with_hole.stl)
            stl_filename_match = re.search(r'\"([^\"]+\.stl)\"', entry['content'])
            if stl_filename_match:
                stl_filename = stl_filename_match.group(1)

    # Define the base path
    base_path = './NewCADs'

    # Append the filename to the path
    if stl_filename:
        full_path = f"{base_path}/{stl_filename}"
        return full_path
    else:
        return None