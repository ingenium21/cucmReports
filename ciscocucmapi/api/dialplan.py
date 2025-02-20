"""CUCM Dial Plan Configuration APIs."""

from zeep.helpers import serialize_object

from .._internal_utils import flatten_signature_kwargs
from .base import DeviceAXLAPI
from .base import SimpleAXLAPI

from pprint import pprint   # for debugging

def _check_route_group_port_assignment(members):
    """Assign all ports for route groups members when not specified."""
    if isinstance(members["member"], list):
        for member in members["member"]:
            if "port" not in member:
                member["port"] = 0
    elif isinstance(members["member"], dict):
        if "port" not in members:
            members["port"] = 0
    return members


class AarGroup(SimpleAXLAPI):
    _factory_descriptor = "aar_group"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "update_matrix", "add_update"]

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    def update_matrix(self, **kwargs):
        axl_resp = self.connector.service.updateAarGroupMatrix(**kwargs)
        return serialize_object(axl_resp)["return"]


class AdvertisedPatterns(SimpleAXLAPI):
    _factory_descriptor = "advertised_patterns"

    def add(self, pattern, patternType="Enterprise Number", hostedRoutePSTNRule="No PSTN", pstnFailStrip=0, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class ApplicationDialRules(SimpleAXLAPI):
    _factory_descriptor = "application_dial_rules"

    def add(self, name, numberBeginWith=None, prefixPattern=None, numberOfDigits=0, digitsToBeRemoved=0, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class BlockedLearnedPatterns(SimpleAXLAPI):
    _factory_descriptor = "blocked_learned_patterns"

    def add(self, pattern=None, prefix=None, clusterId=None, patternType=None, **kwargs):
        if not (pattern or prefix or clusterId):
            criteria = ("pattern", "prefix", "clusterId")
            raise ValueError(f"At least one of the following criteria must be specified: {criteria}")
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CallerFilterList(SimpleAXLAPI):
    _factory_descriptor = "caller_filter_list"

    def add(self, name, isAllowedType=False, endUse=None, members=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CallPickupGroup(SimpleAXLAPI):
    _factory_descriptor = "call_pickup_group"

    def add(self, name, pattern, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CallPark(SimpleAXLAPI):
    _factory_descriptor = "call_park"

    def add(self, pattern, callManagerName, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CalledPartyTransformationPattern(SimpleAXLAPI):
    _factory_descriptor = "called_party_xform_pattern"

    def add(self, pattern, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CallingPartyTransformationPattern(SimpleAXLAPI):
    _factory_descriptor = "calling_party_xform_pattern"

    def add(self, pattern, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CmcInfo(SimpleAXLAPI):
    _factory_descriptor = "cmc"

    def add(self, code, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class ConferenceNow(SimpleAXLAPI):
    _factory_descriptor = "conference_now"

    def add(self, conferenceNowNumber, routePartitionName=None, maxWaitTimeForHost=15, MohAudioSourceId=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Css(SimpleAXLAPI):
    _factory_descriptor = "css"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DirectedCallPark(DeviceAXLAPI):
    _factory_descriptor = "directed_call_park"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "reset", "add_update"]

    def add(self, pattern, retrievalPrefix, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DirectoryLookupDialRules(SimpleAXLAPI):
    _factory_descriptor = "directory_lookup_rules"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "add_update"]

    def add(self, name, priority=0, numberBeginWith=None, numberOfDigits=0, digitsToBeRemoved=0, prefixPattern=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class ElinGroup(SimpleAXLAPI):
    _factory_descriptor = "elin_group"

    def add(self, name, elinNumbers, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class EnterpriseFeatureAccessConfiguration(SimpleAXLAPI):
    _factory_descriptor = "mobility_enterprise_feature_access_number"

    def add(self, pattern, routePartitionName=None, isDefaultEafNumber=False, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class FacInfo(SimpleAXLAPI):
    _factory_descriptor = "fac"

    def add(self, name, code, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class HandoffConfiguration(SimpleAXLAPI):
    _factory_descriptor = "handoff_configuration"
    supported_methods = ["add", "get", "remove", "update", "add_update", "model"]

    def add(self, pattern, routePartitionName=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class HttpProfile(SimpleAXLAPI):
    _factory_descriptor = "http_profile"
    supported_methods = ["add", "get", "remove", "update", "add_update", "model"]

    def add(self, name, userName, password, webServiceRootUri, requestTimeout=60000, retryCount=4, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class HuntList(DeviceAXLAPI):
    _factory_descriptor = "hunt_list"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "reset", "add_update"]

    def add(self, name, callManagerGroupName, routeListEnabled=True, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class HuntPilot(SimpleAXLAPI):
    _factory_descriptor = "hunt_pilot"

    def add(self, pattern, huntListName, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class LineGroup(SimpleAXLAPI):
    _factory_descriptor = "line_group"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class LocalRouteGroup(SimpleAXLAPI):
    _factory_descriptor = "local_route_group"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    """
    LRG uses a different WSDL format than other objects (for no particular reason).
    The updateLocalRouteGroup element has another layer in which a 'locatRouteGroup' 
    object exists (rather than imediately accepting choice options).

    It also uses a newDescription tag for description (even though description is not a 'choice' option).
    And it apperas to require a UUID in order to perform an update.

    Consequently, some methods will require customization includeing:
        add_update (done)
        update (possibly-just to wrap data into a localRouteGroup object)
        model (possibly)
        fetch_choices (not using)
    """
    
    # NEW - not tested yet and not standardized
    # this is the first ADDUPDATE that is being done manually
    # TODO: Grab the best one from the legacy library as the template
    # WORKING but needs cleanup after full testing
    def add_update(self, obj_data):
        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print('LRG CUSTOM ADD_UPDATE')
            print(obj_data)

        name = obj_data.get('name','')
        description = obj_data.get('description','')
                               
        try:
            if LOCAL_DEBUG:
                print('LRG ADD_UPDATE performing GET')
            #r = self.connector.service.getLocalRouteGroup(name=name)
            r = self.get(name=name)
        except Exception as e:
            # perform add
            if LOCAL_DEBUG:
                print(e)
                print('LRG not found - performing add')
                
            add_data = {'name': name, 'description': description}
            #return self.connector.service.addLocalRouteGroup(localRouteGroup=add_data)
            return self.add(**add_data)
        
        else:
            # perform update
            if LOCAL_DEBUG:
                print('LRG found - performing update')
                print('get returned')
                print(r)

            newName = obj_data.get('newName', None)
            newDescription = obj_data.get('newDescription', None)
            if newName is None:
                newName = name
            if newDescription is None:
                newDescription = description

            update_data = {'uuid': r.get('uuid',''), 'name': name,
                   'description': description, 'newName': name, 'newDescription': description}

            if LOCAL_DEBUG:
                print('data before update')
                print(update_data)
            #r = self.connector.service.updateLocalRouteGroup(localRouteGroup=update_data)
            # needs update_data wrapped in localRouteGroup due to WSDL differences
            return self.update(localRouteGroup=update_data)


class MeetMe(SimpleAXLAPI):
    _factory_descriptor = "meetme"

    def add(self, pattern, routePartitionName=None, minimumSecurityLevel="Non Secure", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Mobility(SimpleAXLAPI):
    _factory_descriptor = "handoff_mobility"
    supported_methods = ["model", "create", "add", "get", "update", "add_update"]

    def add(self, handoffNumber, handoffPartitionName=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class MobilityProfile(SimpleAXLAPI):
    _factory_descriptor = "mobility_profile"

    def add(self, name, mobileClientCallingOption="Dial via Office Reverse", dvofServiceAccessNumber=None, dirn=None,
            dvorCallerId=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

# JRE added - still experimental
class RouteFilter(SimpleAXLAPI):
    _factory_descriptor = "route_filter"

    def add(self, name, members, dialPlanName, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RouteGroup(SimpleAXLAPI):
    _factory_descriptor = "route_group"

    def add(self, name, members, distributionAlgorithm="Circular", **kwargs):
        _check_route_group_port_assignment(members)
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RouteList(DeviceAXLAPI):
    _factory_descriptor = "route_list"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "reset", "add_update"]

    def add(self, name, callManagerGroupName, runOnEveryNode=True, routeListEnabled=True,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RoutePartition(DeviceAXLAPI):
    _factory_descriptor = "route_partition"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "restart", "add_update"]

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# JRE need to make a GET using SQL and add to library
class RoutePartitionsForLearnedPatterns(SimpleAXLAPI):
    _factory_descriptor = "route_partitions_for_learned_patterns"
    supported_methods = ["model", "update", 'get']  # get not in wsdl - testing this
    helper_methods = ['get']           # NEW IDEA - if a method is not in WSDL put it here

    def update(self, partitionForEnterpriseANo="Global Learned Enterprise Numbers",
               partitionForE164ANo="Global Learned E164 Numbers",
               partitionForEnterprisePatterns="Global Learned E164 Patterns",
               partitionForE164Pattern="Global Learned Enterprise Patterns",
               markLearnedEntAltNumbers=False,
               markLearnedE164AltNumbers=False,
               markFixedLengthEntPatterns=False,
               markVariableLengthEntPatterns=False,
               markFixedLengthE164Patterns=False,
               markVariableLengthE164Patterns=False,
               **kwargs):
        update_kwargs = flatten_signature_kwargs(self.update, locals())
        return super().update(**update_kwargs)

    # Experimental - should this just be made as a sql query utility and not a GET?
    def get(self):
        """Utility functions to provide a GET method.  This is not part of the 
        SOAP API
        
        NOTE: this is not yet working right for method caller functions that try to probe the WSDL for this item
        May need to put an errorcheck in those calls to allow it to pass through.  A direct call will work.  But many of the
        axlmethod class items willfail because the GET call is preceeded by a _get_method call that would fail.

        :return:    dict with same fields used for an Update
        """

        LOCAL_DEBUG = False

        sql = 'SELECT typepatternusage.name as usage, rp.name as routepartition, ropr.isurgentfixedlen, ropr.isurgentvariablelen '
        sql = sql + 'FROM remoteobjectpartitionrule as ropr left outer join routepartition as rp on ropr.fkroutepartition=rp.pkid, '
        sql = sql + 'typeremoteobject, typeglobalnumber, typepatternusage WHERE typeremoteobject.enum=ropr.tkremoteobject '
        sql = sql + 'and typeglobalnumber.enum=ropr.tkglobalnumber  and ropr.tkpatternusage=typepatternusage.enum'
    
        resp = self.connector.sql.query(sql)
        
        if LOCAL_DEBUG:
            print (f'SQL Response for {self.factory_descriptor}')
            pprint(resp)

        out_dict = {}
        # TODO: stadnardize True False values
        for row in resp:
            if row.get('usage','') == 'ILS Learned Enterprise Number':
                out_dict['partitionForEnterpriseANo'] = row.get('routepartition','')
                out_dict['markLearnedEntAltNumbers'] = row.get('isurgentfixedlen','')

            elif row.get('usage','') == 'ILS Learned E164 Number':
                out_dict['partitionForE164ANo'] = row.get('routepartition','')
                out_dict['markLearnedE164AltNumbers'] = row.get('isurgentfixedlen','')
            
            elif row.get('usage','') == 'ILS Learned Enterprise Numeric Pattern':
                out_dict['partitionForEnterprisePatterns'] = row.get('routepartition','')
                out_dict['markFixedLengthEntPatterns'] = row.get('isurgentfixedlen','')
                out_dict['markVaraibleLengthEntPatterns'] = row.get('isurgentvariablelen','')
            
            elif row.get('usage','') == 'ILS Learned E164 Numeric Pattern':
                out_dict['partitionForE164Pattern'] = row.get('routepartition','')
                out_dict['markFixedLengthE164Patterns'] = row.get('isurgentfixedlen','')
                out_dict['markVariableLengthE164Patterns'] = row.get('isurgentvariablelen','')

        if LOCAL_DEBUG:
            print(f'REPONSE DICT for GET for {self.factory_descriptor}:')
            print(out_dict)

        return out_dict

class RoutePattern(SimpleAXLAPI):
    _factory_descriptor = "route_pattern"

    add_update_base_defaults = {
            #'pattern': '',                              # add required        choice criteria
            #'routePartitionName': '',                   # add required        choice criteria
            #'destination': {},                          # add required and can not be prepopulated
            #         gatewayName or routeListName required

            'routeFilterName': '',                      # add required         choice criteria
            'dialPlanName': '',                         # add required         choice criteria

            'blockEnable': False,                       # add required
            'useCallingPartyPhoneMask': 'Off',          # add required
            'digitDiscardInstructionName': '',          # add required
            'prefixDigitsOut': '',                      # add required
            #'networkLocation':''                       # add required BUG on this one (document this)
            'calledPartyTransformationMask': '',
            'callingPartyTransformationMask': '',
            'callingPartyPrefixDigits': '',
            'patternUrgency': False,
            'supportOverlapSending': False,
            'patternPrecedence': 'Default',
            'provideOutsideDialtone': True,
            'authorizationCodeRequired': False,
            'authorizationLevelRequired': '0',
            'externalCallControl': '',
        }


    # JRE NOTE: routeFilterName and dialPlanName are not in jels defaults
    def add(self, pattern, routePartitionName, destination, blockEnable=False, provideOutsideDialtone=True,
            networkLocation="OffNet", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RoutePlan(SimpleAXLAPI):
    _factory_descriptor = "route_plan_report"
    supported_methods = ["list"]


class SipDialRules(SimpleAXLAPI):
    _factory_descriptor = "sip_dial_rules"

    def add(self, name, patterns=None, plars=None, dialPattern="7940_7960_OTHER", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SipRoutePattern(SimpleAXLAPI):
    _factory_descriptor = "sip_route_pattern"

    def add(self, pattern, routePartitionName, sipTrunkName, usage="Domain Routing", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class TimePeriod(SimpleAXLAPI):
    _factory_descriptor = "time_period"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class TimeSchedule(SimpleAXLAPI):
    _factory_descriptor = "time_schedule"

    def add(self, name, members, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class TransformationProfile(SimpleAXLAPI):
    _factory_descriptor = "transformation_profile"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class TransPattern(SimpleAXLAPI):
    _factory_descriptor = "trans_pattern"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "options", "add_update"]

    add_update_base_defaults = {
                        #'pattern': '',
                        #'routePartitionName': '',
                        'usage': 'Translation',
                        'provideOutsideDialtone': True,
                        'patternUrgency': True,
                    }

    pop_from_update = ['usage']

    def add(self, pattern, routePartitionName, usage="Translation", provideOutsideDialtone=True, patternUrgency=True,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    def get(self, dialPlanName=None, routeFilterName=None, returnedTags=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().get(**add_kwargs)
