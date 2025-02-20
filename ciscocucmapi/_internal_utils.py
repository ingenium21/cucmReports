"""Package helper functions and classes."""

from collections.abc import Iterable
from collections import OrderedDict
from inspect import signature


from zeep.xsd.elements.element import Element
from zeep.xsd.elements.indicators import Choice
from zeep.xsd.elements.indicators import Sequence
from zeep.helpers import serialize_object

import zeep     # this is for serialization and that could be made more specific jre

def element_list_to_ordered_dict(elements):
    """Converts a list of lists of zeep Element objects to a list of OrderedDicts
    Used for SQL query serialization
    """
    return [OrderedDict((element.tag, element.text) for element in row) for row in elements]


def flatten(l):
    """Flattens nested Iterable of arbitrary depth"""
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes)):
            yield from flatten(el)
        else:
            yield el


def check_valid_attribute_req_dict(iterable, d):
    """Check if iterable all of any elements in an iterable are in a dict"""
    return any((i in d if not isinstance(i, tuple) else (all(sub_i in d for sub_i in i)))
               for i in iterable)


def downcase_string(s):
    """Convert initial char to lowercase"""
    return s[:1].lower() + s[1:] if s else ''


def get_signature_kwargs_key(f):
    """Get the key name for kwargs if a method signature"""
    keys = [k for k, v in signature(f).parameters.items() if v.kind == v.VAR_KEYWORD]
    try:
        return keys.pop()
    except IndexError:  # empty list
        return None


def flatten_signature_kwargs(func, loc):
    """flatten a signature dict by one level to move kwargs keys to locals dict"""
    kwargs_name = get_signature_kwargs_key(func)
    # remove unwanted metadata for class methods
    attributes = get_signature_locals(func, loc)
    if kwargs_name:
        attributes.pop(kwargs_name)
        attributes.update(loc[kwargs_name])
    return attributes


def get_signature_locals(f, loc):
    """Filters locals to only include keys in original method signature"""
    return {k: v for k, v in loc.items() if k in signature(f).parameters}


def nullstring_dict(returnedTags):
    """Convert list to nullstring dict"""
    return {_: "" for _ in returnedTags}


# JRE was in BASE but I moved here and renamed from _get_choices to fetch_choices
# wasn't used until add_update
# is used by check_identifiers() 
# and I'm using it for add_update().
def fetch_choices(obj):
    """Create tuple of available choices as defined in xsd

    Recursively inspects a zeep object and extracts the available choices available when performing
    the specific AXL call, as defined in AXL xsd.

    :param obj: zeep Element data structure type
    :return: nested tuple of the xsd-defined choices for the AXL method
    """
    if isinstance(obj, (Choice, Sequence)):
        return tuple([fetch_choices(_) for _ in obj])
    elif isinstance(obj, Element):
        return obj.name
    else:
        raise TypeError(f"Only Choice, Sequence and Element classes inspected, Type '{obj.__class__.__name__}' found.")


# JRE was in BASE but I moved here
# wasn't used until add_update
# I'm using filter_get_choice_criteria instead for now
# this one raises an error while filter_get_choice_criteria cleans things up and proceeds
# so this is a 'check with error raised' rather than a cleaning method
def check_identifiers(wsdl_obj, **kwargs):
    """Check identifiers by inspecting choices in zeep model object

    :param wsdl_obj: zeep AXL model object
    :param kwargs: supplied identifiers to test
    :return: None
    """
    identifiers = fetch_choices(wsdl_obj.elements_nested[0][1][0])
    if not check_valid_attribute_req_dict(identifiers, kwargs):
        raise TypeError(f"Supplied identifiers not supported for API call: {identifiers}")

# JRE new callable method to get the choices from a Req object
# works with fetch_choices()
# Question: should this be in helpers?
# once happy with it, upddate check_identifiers to call it so this is the only reference that has
#   elements_nested[0][1][0] logic
def fetch_req_choices(wsdl_obj):
    """Return 'choices' for a Request zeep model object

    :param wsdl_obj: zeep AXL model object (Req object)
    :return: nested tuple of chocies
    """
    return fetch_choices(wsdl_obj.elements_nested[0][1][0])

# not used yet
def fetch_list_search_criteria(wsdl_obj):
    """Return 'searchCriteria' for a List Request zeep model object
    
    :parma wsdl_obj:    zeep AXL model obejct (ListObjectReq)
    :return:            dict of searchCriteria
    """
    return [element[0] for element in wsdl_obj.elements[0][1].type.elements]

############### Helper / Utility Functions
# These functions were taken from jkrohn library
# they should be incorporated or removed
# originally they were in the class itself as @staticmethods
# my written methods may have overlap with jels items - need to clean up
#

# JRE
def filter_get_choice_criteria(choice_criteria, valid_choices=['uuid']):
    """
    Filter through an arbitrary dict and pull out the valid choices
    Then choose between uuid or all other valid options (sending both to a 
    request will return an error so this is a necessary clean up)
    Can be used for get/update/remove methods (not for list)

    :param choice_criteria:    any dict that includes the choices.
    :param valid_choices:      (list/tuple)  list of all valid choice options
                               this can be generated by fetch_choices() in which case a nested tuple is received
                               NOTE: It may need to be flattenned using flatten()
    :return:                   dict of validated choices with data
    """
    """
    ok, new info....the fetch_choices returns a NESTED TUPLE which breaks out the options
    this routine is expecting a LIST and then works it out.
    Gotta do something with this info.

    ALSO, is this preferring UUID?  I believe so.  Do we want that to be the default behavior?
    """
    # IN USE (add_update) BUT STILL BEING OPTIMIZED
    # this routine will toggle between UUID and the other choices
    #  to make sure a valid selection is being passed to soap
    # It is being customized specifically for a GET but should be usable for a REMOVE as well
    # This step is MANDATORY becuase if you send UUID and NAME at the same time SOAP will return a TypeError
    # Things to add to this filter are to ensure all necessary fields are populated if there are more than one.
    #       Although, I haven't located one that REQUIRED more than 1 at all times...most require a single field and the others are optional
    # COULD do this by looking at the lenght of supported_search_criteria and checking on those
    # NO check for valid items is happening yet....just UUID toggle
    # If a validity check is to be added, that would use the supported_search_criteria field
    # NOTE: This routine is key because it allows us to GET things by UUID and not interfere
    #   with other entries for add/update

    # NOTE: this IF assumes that UUID is ALWAYS in the valid_choices
    #       need to confirm that this is true and, if not, change the IF
    #       it also assumes that if a nested tuple is received there are only 2 options (uuid and some other tuple)
    #
    result_criteria = {}
    for t in valid_choices:
        if isinstance(t,tuple):         # if nested tuple, then break out items in tuple
            for c in t:
                result_criteria[c] = choice_criteria.get(c, None)
        else:
            result_criteria[t] = choice_criteria.get(t, None)

    if result_criteria.get('uuid', None) is not None:
        return {'uuid': result_criteria['uuid']}
    else:
        result_criteria.pop('uuid',None)

    return result_criteria

# JRE
# jels does this right in the list method and uses a logic of just accepting the searchCritiera passed
# OR create a wildcare for all supported criteria
# NOTE: jels has 3 lines of code to do this and to generate "supported_search_criteria" so it doesn't have to be passed
#  Probably want to go with jels stuff right in the LIST method OR break it out into a method
# so it's more explicit and we document it seperately...but use his logic
# question is whether we want to keep supporting "defaul_search_criteria" or a "minimum_search" string
# if not, then definately just go with jels which it is what you submit or AL
def filter_list_search_criteria(search_criteria, supported_search_criteria, default_search_criteria=None):
    # LIST method specific formatting of search criteria (jkrohn)

    search_criteria = {k: v for k, v in search_criteria.items() if k in supported_search_criteria}
    if not search_criteria:
        if default_search_criteria is None:
            return None
        search_criteria[default_search_criteria] = '%'
    return search_criteria

# JRE
def format_get_returned_tags(returned_tags, supported_tags=None, default_tags=None, minimum_tags=None):
    """Formats provided returned_tags data as a valid nullDict and returns the dictionary. 
    For a GET method the returnedTag is OPTIONAL.  So a None value will return ALL tags (and is the default behavior)
    
    This just formats, it does not filter out unsupported tags.

    :param returned_tags: a formated dict, a list, or a string of the tags to return
    :param supported_tags: list of valid tags (not used yet)
    :param default_tags: tags to use if the string of "default" is passed in returned_tags
    :param minimum_tags: tags to use if the string of "mini" is passed in returned_tags

    :returns: dict or None
    """
    # NOTE: filtering with supported_tags not implemented yet

    if isinstance(returned_tags, list):
        returned_tags = {t: '' for t in returned_tags}
    elif isinstance(returned_tags, dict):
        return returned_tags
    elif isinstance(returned_tags, str):        
        if returned_tags.lower() in ['default']:
            returned_tags = {t: '' for t in default_tags}
        else:
            returned_tags = None
    else:
        returned_tags = None

    return returned_tags

# JRE
def format_list_returned_tags(returned_tags, supported_tags=None, default_tags=None, minimum_tags=None):
    """
    Format data as a valid dictionary and returned the dictionary. 
    A LIST method MUST have a valid returnedTag element (it can NOT be None).
    However, an empty returnedTag element can be sent and this will result in just the UUID attribute being returned
    
    :param returned_tags: a formated dict, a list, or a string of the tags to return
    :param supported_tags: list of valid tags (not used yet)
    :param default_tags: tags to use if the string of "default" is passed in returned_tags
    :parm minimum_tags: tags to use if hte string of "mini" is passed in returned_tags

    :returns: dict
    """
    # jre version of routine to accept None, a LIST, a DICT, or a string of "Default" 
    # returns a valid returnedTag object
    # TODO: make sure a blank default-tags or minimimum-tags will still return a {} rathern than None
    # NOTE: since UUID is an attribute, it does not need to be listed in the returnedTags and it will always be returned
    # NOTE: Returned Tags are MANDATORY for a list item and cannot be None.  But you can enter a blank tag.
    # NOTE: filtering with supported_tags not implemented yet. Done by zeep which throws error
    # NOTE: LIST functions are not supposed to return ALL fields and so this is not included in the helper.
    #           If you want ALL fields you must list them out explicitly in your program
    # TODO: this does not handle large requests yet with paging...TODO

    if isinstance(returned_tags, list):
        returned_tags = {t: '' for t in returned_tags}
    elif isinstance(returned_tags, dict):
        return returned_tags
    elif isinstance(returned_tags, str):        
        if returned_tags.lower() in ['default']:
            returned_tags = {t: '' for t in default_tags}
        elif returned_tags.lower() in ['mini','minimum']:
            returned_tags = {t: '' for t in minimum_tags}
        else:
            returned_tags = {}
    else:
        returned_tags = {}

    return returned_tags

# this was jkrohns serialization for a list response
# need to compare it with what jels returns and either
# use or remove
# it should also be checked for whether it works when
# using a wrapper
def handle_list_response(r):
    if r['return'] is None:
        return []
    r = r['return'][next((r for r in r['return']))]
    return [zeep.helpers.serialize_object(s) for s in r]

