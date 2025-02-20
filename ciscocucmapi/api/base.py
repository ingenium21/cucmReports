"""Base AXL APIs"""

import functools
from operator import methodcaller

from zeep.exceptions import Fault
from zeep.helpers import serialize_object
from zeep.xsd.elements.element import Element           # jre might only be in internal_utils now
from zeep.xsd.elements.indicators import Choice         # jre might only be in internal_utils now
from zeep.xsd.elements.indicators import Sequence       # jre might only be in intenral_utils now

from .._internal_utils import check_valid_attribute_req_dict  # jre might only be in intenral_utils now
from .._internal_utils import downcase_string
from .._internal_utils import element_list_to_ordered_dict
from .._internal_utils import flatten_signature_kwargs
from .._internal_utils import nullstring_dict
from .._internal_utils import fetch_choices               # JRE add_udpate
from .._internal_utils import filter_get_choice_criteria # JRE add_udpate
from .._internal_utils import format_get_returned_tags   # JRE add_udpate
   
from ..exceptions import IllegalSQLStatement
from ..helpers import get_model_dict
from ..helpers import sanitize_model_dict
from ..helpers import filter_attributes_depth_one       # JRE add_update

from copy import deepcopy   # using for add_udpate (may remove)  [jre]
from pprint import pprint
import logging

def classproperty(func):
    """Decorator function to denote class properties"""
    if not isinstance(func, (classmethod, staticmethod)):
        func = classmethod(func)
    return ClassPropertyDescriptor(func)


class ClassPropertyDescriptor(object):
    """Decorator class for class properties"""
    # setter wont work, but we don't want it at the class level in any case
    def __init__(self, fget):
        self.fget = fget

    def __get__(self, obj, obj_class=None):
        if obj_class is None:
            obj_class = type(obj)
        return self.fget.__get__(obj, obj_class)()


class BaseAXLAPI(object):
    """Base API Class for AXL objects"""
    _factory_descriptor = ValueError

    _add_defaults = {}              # JRE testing
    USE_OBJECT_FACTORY = False      # JRE testing flag to enable or disable use of axl_data object factory 

    def __init__(self, connector, object_factory):
        self.connector = connector
        self.object_factory = object_factory
        self._return_name = downcase_string(self.__class__.__name__)

    @classproperty
    def factory_descriptor(cls):  # noqa
        return cls._factory_descriptor

    @classproperty
    def add_defaults(cls):  # JRE testing add_update (don't think this is required)
        return cls._add_defaults

    @classmethod
    def assert_supported(cls, func):
        """Decorator looks up func's name in self.supported_methods."""

        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if func.__name__ not in self.supported_methods:
                raise AttributeError(
                    f"{self.__class__.__name__} API does not support '{func.__name__}' method.")
            return func(self, *args, **kwargs)

        return wrapper


class SimpleAXLAPI(BaseAXLAPI):
    """Simple AXL API with common method support"""
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "add_update"]  # doesn't include 'options'
 
    def __init__(self, connector, object_factory):  # original
        super().__init__(connector, object_factory)
        if "add" in self.supported_methods:
            self._add_model_name = "".join(["X", self.__class__.__name__])
        if "update" in self.supported_methods:
            self._update_method_name = "".join(["Update", self.__class__.__name__, "Req"])
        if "get" in self.supported_methods:
            self._get_model_name = "".join(["R", self.__class__.__name__])
            self._get_method_name = "".join(["Get", self.__class__.__name__, "Req"])
        if "list" in self.supported_methods:
            self._list_model_name = "".join(["L", self.__class__.__name__])
            self._list_method_name = "".join(["List", self.__class__.__name__, "Req"])

    def _fetch_add_model(self):
        return self._get_wsdl_obj(self._add_model_name)

    def _fetch_update_method(self):
        return self._get_wsdl_obj(self._update_method_name)

    def _fetch_get_model(self):
        return self._get_wsdl_obj(self._get_model_name)

    def _fetch_get_method(self):
        return self._get_wsdl_obj(self._get_method_name)

    def _fetch_list_model(self):
        return self._get_wsdl_obj(self._list_model_name)

    def _fetch_list_method(self):
        return self._get_wsdl_obj(self._list_method_name)

    def _get_wsdl_obj(self, obj_name):
        """Get empty python-zeep complex type

        :param obj_name: name of AXL type
        :return: empty zeep complex type obj
        """
        return self.connector.client.get_type(f'ns0:{obj_name}')

    def _axl_methodcaller(self, action, **kwargs):
        """Map calling method to a concat of the action verb and the API class name

        :param action: (str) API verb - 'add', 'get', 'list', etc.
        :param kwargs: input kwargs for called method
        :return: axl response zeep object
        """
        axl_method = methodcaller("".join([action, self.__class__.__name__]), **kwargs)
        return axl_method(self.connector.service)

    def _serialize_axl_object(self, action, **kwargs):
        """Builds and AXL methodcaller using given action verb and the object type.

        Serializes the response and uses the resultant dict to instantiate a data model object

        :param action: AXL action verb - 'add', 'get', 'update', 'remove', etc.
        :param kwargs: AXL method attribute kwargs dictionary
        :return: Data Model object containing the serialized response data dict
        """
        axl_resp = self._axl_methodcaller(action, **kwargs)

        # Disabled object factory due to issues with mutable mapping
        if self.USE_OBJECT_FACTORY:
            return self.object_factory(
            self.__class__.__name__,
            serialize_object(axl_resp)["return"][self._return_name])
        else:
            return serialize_object(axl_resp)["return"][self._return_name]

    def _serialize_uuid_resp(self, action, **kwargs):
        """Serialize commons responses that return a uuid string only

        :param action: axl method verb
        :param kwargs: dict of method attributes
        :return: (str) uuid
        """
        axl_resp = self._axl_methodcaller(action, **kwargs)
        return serialize_object(axl_resp)["return"]

    @BaseAXLAPI.assert_supported
    def model(self, target_model="add", serialize=True, include_types=False, sanitized=True):
        """Return a target model in either Python dict or as Zeep object.
        
        Useful for inspecting the endpoint's schema and future template generation.

        Also used by axlmethodcaller when analyzing choice elements

        :param target_model:    target model for api - 'add', 'get', 'update' etc.
        :param serialize:       defaults to True to return a Python dict/ODict.  If False, returns
                                a Zeep complex type object
        :param sanitized:       collapse zeep's interpretation of the xsd nested dicts
                                with '_value_1' and 'uuid' keys into a simple k,v pair with v as a (str)
                                ignored if "serialize" is false
        :param include_types: (bool) include zeep model type inspection

        :return: empty data model dictionary

            add
                Request         XObject
                Response        UUID
            Update
                Request         UpdateObjectReq
                Response        UUID
            Get (2 needed)
                Request         GetObjectReq
                Response        RObject (standard get)
            remove
                Request         (use GetObjectReq)
                Response        UUID
            List
                Request
                Response

        ENHANCE: how to hanlde methods that are ADDED and NOT in WSDL?
            And for methods that are not in object?
            What if, on failure, it calls a dict that is stored in the child object?
            so..on error...see if an object_of_last_resort is created
                if so, return the object...otherwise, raise error
                this object would alwasy need to be serialized

            Examples to try with:
                All     userRank, userRole
                GET     routepartitionsforils
                ADD     ldapSystem,ldapAuthentication
        """

        if target_model == "add": 
            raw_model = self._fetch_add_model()         # model only - XObject
        elif target_model == "update":                  
            raw_model = self._fetch_update_method()     # method only - RObject
        elif target_model in ["get", "get_response"]:   
            raw_model = self._fetch_get_model()         # response model - RObject
        elif target_model in ["get_method", "get_request"]:            
            raw_model = self._fetch_get_method()        # request method 
        elif target_model in ["list", "list_response"]:
            raw_model = self._fetch_list_model()        # response model
        elif target_model in ["list_method", "list_request"]:
            raw_model = self._fetch_list_method()        # request method (searchCriteria and returnedTags)
        else:
            raise NotImplementedError       # this else may need to move due to catch
        
        if serialize:    
            model_dict = get_model_dict(raw_model, include_types=include_types)
            return sanitize_model_dict(model_dict) if sanitized else model_dict
        else:
            return raw_model     # requested raw Zeep object

    @BaseAXLAPI.assert_supported
    def create(self, **kwargs):
        """Create AXL object locally for pre-processing"""
        axl_add_method = methodcaller(self._fetch_add_model().__class__.__name__, **kwargs)
        axl_add_obj = axl_add_method(self.connector.model_factory)

        # Disabled object factory due to issues with mutable mapping
        if self.USE_OBJECT_FACTORY:
            return self.object_factory(self.__class__.__name__, serialize_object(axl_add_obj))
        else:
            return serialize_object(axl_add_obj)

    @BaseAXLAPI.assert_supported
    def add(self, **kwargs):
        """Add method for API endpoint"""
        wrapped_kwargs = {
            self._return_name: kwargs
        }
        return self._serialize_uuid_resp("add", **wrapped_kwargs)

    @BaseAXLAPI.assert_supported
    def get(self, returnedTags=None, **kwargs):
        """Get method for API endpoint"""
        if isinstance(returnedTags, list):
            returnedTags = nullstring_dict(returnedTags)
        # define zeep objects for method generically
        #get_method = self._get_wsdl_obj(self._get_method_name)
        get_kwargs = flatten_signature_kwargs(self.get, locals())
        return self._serialize_axl_object("get", **get_kwargs)

    @BaseAXLAPI.assert_supported
    def update(self, **kwargs):
        """Update method for API endpoint"""
        return self._serialize_uuid_resp("update", **kwargs)

    @BaseAXLAPI.assert_supported
    def list(self, searchCriteria=None, returnedTags=None, skip=None, first=None):
        """Fetch a list of API endpoint objects.

        Note:
        'searchCriteria=None' or 'returnedTags=None' may have VERY verbose output
        and create large responses over 8MB, potentially resulting in AXL errors for large data sets.

        :param searchCriteria: (dict) search criteria for "list' method.  Wraps a 'fetch-all' if unspecified.
        :param returnedTags: (dict) returned attributes.  If none, wrapper
        :param skip: (int) skip number of results
        :param first: (int) return first number of results
        :return: list of Data Models for API Endpoint
        """
        if not searchCriteria:
            # this is presumptive and may not work in all cases.
            list_method = self._get_wsdl_obj(self._list_method_name)
            supported_criteria = [element[0] for element in list_method.elements[0][1].type.elements]
            searchCriteria = {supported_criteria[0]: "%"}
        if not returnedTags:
            list_model = self._get_wsdl_obj(self._list_model_name)
            returnedTags = get_model_dict(list_model)
        elif isinstance(returnedTags, list):
            returnedTags = nullstring_dict(returnedTags)
        axl_resp = self._axl_methodcaller("list", searchCriteria=searchCriteria, returnedTags=returnedTags,
                                          skip=skip, first=first)
        try:
            axl_list = serialize_object(axl_resp)["return"][self._return_name]

            # Disabled object factory due to issues with mutable mapping
            if self.USE_OBJECT_FACTORY:
                return [self.object_factory(self.__class__.__name__, item) for item in axl_list]
            else:
                return axl_list

        except TypeError:
            return []

    @BaseAXLAPI.assert_supported
    def remove(self, **kwargs):
        """Remove method for API endpoint"""
        return self._serialize_uuid_resp("remove", **kwargs)

    @BaseAXLAPI.assert_supported
    def options(self, uuid, returnedChoices=None):
        """Return options for selected API endpoints"""
        kwargs = {
            "uuid": uuid,
            "returnedChoices": returnedChoices
        }
        options_method = methodcaller("".join(["get", self.__class__.__name__, "Options"]), **kwargs)
        axl_resp = options_method(self.connector.service)

        # Disabled object factory due to issues with mutable mapping
        if self.USE_OBJECT_FACTORY:
            return self.object_factory(
                "".join([self.__class__.__name__, "Options"]),
                serialize_object(axl_resp)["return"][self._return_name]
            )
        else:
            return serialize_object(axl_resp)["return"][self._return_name] 

    @BaseAXLAPI.assert_supported
    def add_update(self, obj_data):
        """add_update routine
        
        EXPERIMENTAL (but working - remove LOCAL_DEBUG once finished)
        takes a single "obj_data" element which is a dict holding all add/update items
        Goal is to have a method that is somewhat idempotent for add/update.
        This method does not break out the "required" fields for an add.  If they are
        missing, an error will be thrown.   But it will attempt to fill in the 'defaults'
        that are seen in the GUI as an assist.  Defaults are applied only on an add but
        not on an update
        Method will:
            -extract GET choices to form a GET requrest (priority to UUID if it exists)
            -If found, perform an UPDATE after POPping off any items unique to an ADD
            -If not found, perform an ADD
                -begins from class "defaults" and updates it with passed data
                -then POPs off any items unique to an UPDATE
                -then perform add
        WHEN NOT TO USE update() INSTEAD:
            -if identifying by UUID, then use update instead (doesn't work on ADD)
            -if using "newName" fields or "remove/addLines" style itesm use update instead
        """
        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            logging.info('ADD_UPDATE being performed with the following data:')
            logging.info(pprint(obj_data))

        try:
            # Perform GET request
            #valid_choices = fetch_req_choices(self._fetch_get_method())
            valid_choices = fetch_choices(self._fetch_get_method().elements_nested[0][1][0])    # pull choices from WSDL object (this appears to be working)
            choice_criteria = filter_get_choice_criteria(choice_criteria=obj_data, valid_choices=valid_choices)   # pull out choice_criteria from obj_data
            returned_tags = nullstring_dict(choice_criteria)                            # use choice criteria for return tags
            
            if LOCAL_DEBUG:
                print(f'choice_criteria (valid): {valid_choices}')
                print(type(valid_choices))
                print(f'choice_criteria (active): {choice_criteria}')
                print(type(choice_criteria))
                print(f'returnedTags: {returned_tags}')
                print(type(returned_tags))
                print('ABOUT TO GET object')

            g = self._serialize_axl_object("get", returnedTags=returned_tags, **choice_criteria)         # this could be simplified

            if LOCAL_DEBUG:
                print('SUCCESSFUL GET RESPONSE:')
                pprint(g)

        except Fault as e:                                              # match of zeep.exception.Fault
            # ADD routine if not found
            if LOCAL_DEBUG:
                print('ADD_UPDATE: GET did NOT return a value: Proceeding with ADD')
            
            # NOTE: Jels would probably use a create() here.
            # need to consider if we want to use that or populate new _add_defaults item
            # within each class.  Either way, a copy of data is needed due to filtering
            # step coming up
            add_data = deepcopy(self._add_defaults)       # make a copy of the defaults for an add
            add_data.update(obj_data)                     # update it with the passed obj_data


            # pop items not used for ADD
            add_model=self.model()
            add_data = filter_attributes_depth_one(add_model, add_data)

            if LOCAL_DEBUG:
                print('ADD OBJ just befor ADD: ')
                pprint(add_data)
            return self.add(**add_data)          # run add and serialize to a UUID
        else:
            # UPDATE routine
            if LOCAL_DEBUG:
                print('ADD_UPDATE: GET RETURNED VALUE: Proceeding with UPDATE')
                
            update_model=self.model(target_model='update')

            if LOCAL_DEBUG:
                # BUG/ISSUE: for LRG, has an additional depth of struture
                # THEORY: it looks like hte update_model coming back for LRG is not formed like the others
                print('Found update_model of:')
                print(update_model)

            # copy needed so original config is not affected
            update_data = deepcopy(obj_data)
            update_data = filter_attributes_depth_one(update_model, update_data)

            if LOCAL_DEBUG:
                print('UPDATE OBJ just before UPDATE: ')
                pprint(update_data)
            return self.update(**update_data)       # run UPDATE and seriliaze to a UUID


class DeviceAXLAPI(SimpleAXLAPI):
    """AXL API support additional device-related methods"""
    supported_methods = [
        "model", "create", "add", "get", "list", "update", "remove",
        "apply", "restart", "reset",
        "add_update"
    ]

    @BaseAXLAPI.assert_supported
    def apply(self, **kwargs):
        """Apply config to API endpoint

        :param kwargs: uuid or name
        :return: (str) uuid
        """
        return self._serialize_uuid_resp("apply", **kwargs)

    @BaseAXLAPI.assert_supported
    def restart(self, **kwargs):
        """Restart API endpoint

        :param kwargs: uuid or name
        :return: (str) uuid
        """
        return self._serialize_uuid_resp("restart", **kwargs)

    @BaseAXLAPI.assert_supported
    def reset(self, **kwargs):
        """Reset API endpoint

        :param kwargs: uuid or name
        :return: (str) uuid
        """
        return self._serialize_uuid_resp("reset", **kwargs)


class ThinAXLAPI(BaseAXLAPI):
    """API extension for Thin AXL"""
    _factory_descriptor = "sql"
    supported_methods = ["query", "update"]

    @BaseAXLAPI.assert_supported
    def query(self, sql_statement):
        """Execute SQL query via Thin AXL

        :param sql_statement: Informix-compliant SQL statement
        :return: SQL Thin AXL data model object
        """
        try:
            axl_resp = self.connector.service.executeSQLQuery(sql=sql_statement)
            try:
                serialized_resp = element_list_to_ordered_dict(
                    serialize_object(axl_resp)["return"]["rows"])
            except KeyError:
                # single tuple response
                serialized_resp = element_list_to_ordered_dict(
                    serialize_object(axl_resp)["return"]["row"])
            except TypeError:
                # no SQL tuples
                #
                # JRE Edit - original routine would return "None" if no rows found
                # Instead, returning an empty list for 0 entries of the query was
                # executed without errors
                serialized_resp = []
                #serialized_resp = serialize_object(axl_resp)["return"] 

            # Disabled object factory due to issues with mutable mapping
            if self.USE_OBJECT_FACTORY:
                return self.object_factory(self.__class__.__name__, serialized_resp)
            else:
                return serialized_resp

        except Fault as fault:
            raise IllegalSQLStatement(message=fault.message)

    @BaseAXLAPI.assert_supported
    def update(self, sql_statement):
        """Execute SQL update via Thin AXL

        :param sql_statement: Informix-compliant SQL statement
        :return: (int) number of rows updated
        """
        try:
            axl_resp = self.connector.service.executeSQLUpdate(sql=sql_statement)
            return serialize_object(axl_resp)["return"]["rowsUpdated"]
        except Fault as fault:
            raise IllegalSQLStatement(message=fault.message)


class Device(BaseAXLAPI):
    """API Extension for restartable CUCM Devices"""
    _factory_descriptor = "device"
    supported_methods = ["login", "logout", "reset"]

    @BaseAXLAPI.assert_supported
    def login(self, deviceName, profileName, userId,
              loginDuration=0):
        axl_resp = self.connector.service.doDeviceLogin(deviceName, profileName, userId, loginDuration)
        return serialize_object(axl_resp)["return"]

    @BaseAXLAPI.assert_supported
    def logout(self, deviceName):
        axl_resp = self.connector.service.doDeviceLogout(deviceName)
        return serialize_object(axl_resp)["return"]

    @BaseAXLAPI.assert_supported
    def reset(self, deviceName, **kwargs):
        reset_kwargs = flatten_signature_kwargs(self.reset, locals())
        axl_resp = self.connector.service.doDeviceLogin(**reset_kwargs)
        return serialize_object(axl_resp)["return"]
