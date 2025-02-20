# Helper routines that are not finalized or are being tested

from collections import OrderedDict
from collections.abc import MutableMapping
from .helpers import filter_dict_to_target_model

"""
remove_fields()     this looks like one to add
sanitize_uuid_value_one()   this may be better than jels because it covers lists
sql_query_wrapper           jkhrons wrapper fro SQL
compare_dicts()             straight compare functions (possible add)
"""

# this is working and is being used in clickuf
# candidate for final helper.py
# jels did this differently.  His AXLDATA model had a .filter(model) method built-in
#       that woudl automatically filter out fields between RName and XName
#       by calling filter_dict_to_target_model().  That method ALSO performed
#       a sanitize for uuid/_value_1 first so it was all inclusive.
#       we could look at doing that as the model is rebuilt OR we could add
#       some other helper functions to auto-generate the fields_to_remove values
#       so you don't have to just know them.

def remove_fields(data, fields_to_remove=[], depth=1):
    """
    Remove fields from a list, dict, or OrderedDict.  
    
    data:               list, dict, or OrderedDict to be cleaned
    fields_to_remove:   list of fields to be removed
    depth:              how deep into data object to go. There is no 'infinite' setting
     
    returns:    cleaned  data (TODO: determine if things are changed from dict/OrderedDict
    """
    if depth <= 0:
        return data

    if isinstance(data, (OrderedDict, dict)):
        for key, value in list(data.items()):
            if key in fields_to_remove:
                del data[key]
            else:
                remove_fields(value, fields_to_remove, depth-1)

    elif isinstance(data, list):
        for idx, item in enumerate(data):
            data[idx] = remove_fields(item, fields_to_remove, depth-1)
    
    return data

# utility function copied from AXL Helper (long-term call it from helper)
# JRE NOTE this may get deleted in favor of remove_fields() which works a greater depth
#       and handles more types.  This is only for dictionary
def remove_fields_1(input_dict, fields_to_remove=[]):
    """
    Filter out fields from a dictionary to a depth of 1
     
    :param input_dict: input dictionary 
    :parma fields_to_remove: list object of fields to remove
    :return: new dictionary with fields removed
    """
    # this can be used to remove uuid, ctiid, dialPlanWizardId, etc
    new_dict = {k: v for k, v in input_dict.items() if k not in fields_to_remove}

    return new_dict

# utility function copied from AXL Helper (long-term call it from helper)
# update of jels sanitize_model_dict()
# CANDIDATE for helper.py
# NOTE: THIS HAS BEEN COPIED TO HELPERS.PY AND IS NOW sanitize_model_dict()
#       References to this method should now be removed.
def sanitize_uuid_value_one(data):
    """Sanitize zeep output dict with `_value_N` references.

    Sanitize output of {'FIELDNAME':{'uuid':'','__value_1': 'VALUE'}} to {'FIELDNAME':'VALUE'}
    Set to work with dict/OrderedDict/list
    """
    if isinstance(data, (dict, OrderedDict)):
        for key, value in data.items():
            if isinstance(value, (dict, OrderedDict, list)):
                sanitize_uuid_value_one(value)
                if len(value) == 2 and 'uuid' in value and '_value_1' in value:
                    new_key = key
                    new_value = value['_value_1']
                    data[new_key] = new_value
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, OrderedDict, list)):
                data[idx] = sanitize_uuid_value_one(item)
    return data

# not used yet
def sql_query_wrapper():
    # testing a SQL query wrapper
    """
    If going to incorporate this, it will require editing the BaseAXLAPI/query method
    fault messages would go in 'message' and we can decide if there is a 'status_code' or not
    length is -1 if an error and is length of list otherwise
    return holds the output list
    success is True only if 0 or more entries returned
    """
    wrapper = {}
    wrapper['success'] = False
    wrapper['return'] = None
    wrapper['message'] = ''
    #wrapper['status_code'] = 0
    wrapper['length'] = -1
    return wrapper



# JRE evolving
def compare_two_dicts(dict1, dict2):
    unique_keys_dict1 = []
    unique_keys_dict2 = []
    
    # check items in dict1
    for key in dict1.keys():
        if key not in dict2:
            unique_keys_dict1.append(key)

    # check items in dict2
    for key in dict2.keys():
        if key not in dict1:
            unique_keys_dict2.append(key)
    return unique_keys_dict1, unique_keys_dict2

# JRE evolving 
def compare_dicts(dict1, dict2):
    """Compare 2 dictionaries to find unique fields, 
    # DEPTH OF 1 for now
    This utility can be used to compare an "add model" and an "update model" to see what fields
    need to be POPPED when using the same object data.  It is leveraged by the
    "add_update" method.
    dict1:  model to find unique items
    dict2:  model to see if it is matched
    returns:    a list of fields that are unique to dict1
    """
    unique_keys_dict1= []
    
    # check items in dict1
    for key in dict1.keys():
        if key not in dict2:
            unique_keys_dict1.append(key)

    return unique_keys_dict1
