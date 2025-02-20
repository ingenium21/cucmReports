"""Package helper functions and classes"""

import csv
import json
from collections import OrderedDict
from collections.abc import MutableMapping
from pathlib import Path

from zeep.helpers import serialize_object

from .exceptions import ParseError

"""
to_json_dict()                  not called anywhere
to_csv()                        called by axl_data model
get_model_dict()                called by base.py, system.py and advanced.py
filter_dict_to_target_model()   called by axl_data model
sanitize_model_dict()           multiple calls
extract_pkid_from_uuid()        not called anywhere
_filter_mandatory_attributes()  [experimental] - not used anywhere
filter_attributes()             not called anywhere
"""

def to_json_dict(json_data):
    """Given a dictionary or JSON string; return a dictionary.

    :param json_data: json_data(dict, str): Input JSON object.
    :return: A Python dictionary/OrderedDict with the contents of the JSON object.
    :raises TypeError: If the input object is not a dictionary or string.
    """
    if isinstance(json_data, dict):
        return json_data
    elif isinstance(json_data, str):
        return json.loads(json_data, object_hook=OrderedDict)
    else:
        raise TypeError(f"'json_data' must be a dict or valid JSON string; received: {json_data!r}")


def to_csv(data_model_list, destination_path):
    """Write list of AXL data models to disk

    :param data_model_list: list of dicts or ordered dicts of data model
    :param destination_path: (Path) file destination Path object or (str)
    :return: None.  csv file written to disk
    """
    if isinstance(destination_path, Path):
        destination_path = destination_path.resolve()
    try:
        with open(destination_path, "w", newline='') as _:
            dict_writer = csv.DictWriter(_, fieldnames=data_model_list[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(data_model_list)
    except FileNotFoundError:
        # placeholder for pre-3.6 support...
        raise FileNotFoundError


# JRE Question: why is this here when the model() method already exists?
# when would this be used rather than the model() which I think has more
# capabilties?
def get_model_dict(obj, include_types=False):
    """Get an empty model dict or OrderedDict for an api endpoint from a complex zeep type

    'include_types' is useful for quickly determining the API endpoints expected attribute type
    (e.g. "hostName": "String128") without delving into the .xsd or API documentation.

    Note:

    some output (e.g. "ldapPortNumber": "anySimpleType") may actually be of a sub-type
    (i.e. "XInteger" in the case of "ldapPortNumber"), but this util does not yet provide that level of granularity
    in its schema inspection.

    :param obj: zeep AXL data structure
    :param include_types: (bool) replace null string with string name of AXL type for each attr
    :return: (dict or OrderedDict) of soap api endpoint
    """
    model_dict = OrderedDict()
    for e in obj.elements:
        if not hasattr(e[1].type, 'elements'):
            model_dict[e[0]] = "" if not include_types else e[1].type.name
        else:
            # list of list of elements represented as list with single ordered dict
            if hasattr(e[1].type.elements[0][1].type, 'elements'):
                model_dict[e[0]] = OrderedDict([
                    (e[1].type.elements[0][0],
                     [get_model_dict(e[1].type.elements[0][1].type,
                                     include_types=include_types)])
                ])
            else:
                model_dict[e[0]] = get_model_dict(e[1].type,
                                                  include_types=include_types)
    return model_dict


# JRE NOTE:  this will need updating because of MutableMappings
#
def filter_dict_to_target_model(obj, target_model):
    """Filters a serialized response to match the structure of a target model dictionary.

    This is useful for filtering a 'get' or 'list' response to match the required schema of a 'add' request.
        e.g. filtering a serialized 'RPhone' for re-purposing in a subsequent 'XPhone' request.

    :param obj: serialized zeep response
    :param target_model: model dict for
    :return: filtered dict only containing k-v pairs matching the target model
    """

    try:
        # base case for empty model with uuid attr
        if (set(obj.keys()) == {"uuid", "_value_1"} or set(obj.keys()) == {"_value_1"}) and \
                (set(target_model.keys()) == {"uuid", "_value_1"} or set(target_model.keys()) == {"_value_1"}):
            return obj

        # if isinstance(obj, dict):
        if isinstance(obj, MutableMapping):
            filtered_obj = OrderedDict()
        else:
            raise TypeError

        for k, v in target_model.items():
            if k in obj:
                if isinstance(v, list):
                    if all([isinstance(i, dict) for i in v]) and len(v) == 1 and obj[k]:
                        filtered_obj[k] = [filter_dict_to_target_model(item, v[0]) for item in obj[k]]
                    else:
                        filtered_obj[k] = obj[k]
                elif isinstance(v, dict) and obj[k]:
                    filtered_obj[k] = filter_dict_to_target_model(obj[k], v)
                else:
                    filtered_obj[k] = obj[k]
        return filtered_obj
    except (ValueError, AttributeError, TypeError):
        raise ParseError("Unable to parse data object dictionary against target model")

# JRE NOTE: this is jels routine but it is called within the model and other places.
# However, it assumes the top level is a DICT...but it allows LISTS within it.
# Replacement method named sanitize_uuid_value_one() works on dict/list/OrderedDict at any depth.
# Evaluate whether to keep this method or rename one of them (sanitize_uuid_value_one())
# used in base.py and key to model() method also used in axl_data model
def JELS_sanitize_model_dict(obj):
    """Sanitize zeep output dict with `_value_N` references.

    This is useful for data processing where one wishes to consume the 'get' api data instead of re-purposing
    it in e.g. an 'update' api call. Achieved by flattening the nested OrderedDict by replacing
    the nested dict for AXL's 'XFkType' with the value specified in zeep's `_value_N` key.

    Note: Doing so disregards 'uuid' values.

    Example:

    sample_model_dict = {
        'name': 'SEPAAAABBBBCCCC',
        'callingSearchSpaceName': {
            '_value_1': 'US_NYC_NATIONAL_CSS',
            'uuid': '{987345984385093485gd09df8g}'
        }
    }

    is sanitized to:

    sanitized_sample_model_dict = {
        'name': 'SEPAAAABBBBCCCC',
        'callingSearchSpaceName': 'US_NYC_NATIONAL_CSS'
    }

    :param obj: (dict) AXL data model
    :return: sanitized AXL data model
    """
    if set(obj.keys()) == {"uuid", "_value_1"} or set(obj.keys()) == {"_value_1"}:
        return obj["_value_1"]
    else:
        for k, v in obj.items():
            if isinstance(v, dict):
                obj[k] = sanitize_model_dict(v)
            elif isinstance(v, list):
                obj[k] = [sanitize_model_dict(item) for item in v]
    return obj

# JRE Version that also supports lists
# update of jels sanitize_model_dict()
# TODO: Once fully tested, merge comments and remove decremented code.
def sanitize_model_dict(data):
    """Sanitize zeep output object with `_value_N` references.

    Sanitize output of {'FIELDNAME':{'uuid':'','__value_1': 'VALUE'}} to {'FIELDNAME':'VALUE'}
    Set to work with dict/OrderedDict/list
    :parm obj: (dict, OrderedDict, or list) 
    :return:    sanitized data of same type
    """
    if isinstance(data, (dict, OrderedDict)):
        for key, value in data.items():
            if isinstance(value, (dict, OrderedDict, list)):
                sanitize_model_dict(value)
                if len(value) == 2 and 'uuid' in value and '_value_1' in value:
                    new_key = key
                    new_value = value['_value_1']
                    data[new_key] = new_value
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, OrderedDict, list)):
                data[idx] = sanitize_model_dict(item)
    return data


def extract_pkid_from_uuid(pkid_or_uuid):
    """Removes all braces braces encapsulation included with AXL uuid if it exists.
    Also makes the value lowercase.

    Does not use regex matching on start/finish for speed.  No validation is provided on uuid format.
    If braces do not exist, the original string should be returned as-is.

    :param pkid_or_uuid: (str) pkid or uuid
    :return: (str) pkid with stripped encapsulation
    """
    return pkid_or_uuid.lower().replace('{', '').replace('}', '')  # double replace implemented for speed


def _filter_mandatory_attributes(zeep_axl_factory_object):
    """Inspect the AXL schema and return a generator of an API endpoint's mandatory attributes.

    Intended use is for local validation prior to submitting an 'add' AXL request to reduce the cost of
    remote error responses from the AXL server.

    Note:
    EXPERIMENTAL ONLY.
    Inconsistencies noted for determinations on 'minOccurs' and 'nillable'.  Suggested NOT to be used.

    :param zeep_axl_factory_object: zeep AXL object generated from a 'get_type' factory call
    :return: generator of mandatory axl elements
    """
    for element in serialize_object(zeep_axl_factory_object).elements:
        # filter on minimum occurrence and no default value
        if element[1].min_occurs >= 1 \
                and not element[1].is_optional \
                and not element[1].nillable \
                and not element[1].default:
            yield element[1]


# JRE Question: to what depth does this go?  Does it work on a list?
def filter_attributes(target, model):
    """Filter attributes in dict to only include those in a target model

    :param target: (dict) target model
    :param model: (dict) current model
    :return: (dict) filtered model
    """
    if isinstance(target, dict):
        return {k: target[k] if not isinstance(v, dict) else filter_attributes(target[k], model[k])
                for k, v in model.items()}
    elif isinstance(target, OrderedDict):
        return OrderedDict((k, target[k] if not isinstance(v, dict) else filter_attributes(target[k], model[k]))
                           for k, v in model.items())
    else:
        raise TypeError("Invalid target class - dict or DefaultDict supported")

# ########################################################
# JRE Add-ons
    
def filter_attributes_depth_one(target, model):
    """ Filter attributes in dict to only include those in the target model
    This method works to a depth of 1.
    
    :param target: (dict) target model
    :param model: (dict) current model to be filtered
    :return: (dict) filtered model
    """

    LOCAL_DEBUG = False

    keys_to_remove = [key for key in model if key not in target]

    if LOCAL_DEBUG:
        print(keys_to_remove)
    
    for key in keys_to_remove:
        del model[key]
        if LOCAL_DEBUG:
            print(f'{key} being removed')
    return model

def camel_to_snake(input_string):
    result = [input_string[0].lower()]
    for char in input_string[1:]:
        if char.isupper():
            result.append('_')
            result.append(char.lower())
        else:
            result.append(char)
    return ''.join(result)


def snake_to_camel(input_string):
    components = input_string.split('_')
    return components[0] + ''.join(x.capitalize() for x in components[1:])

