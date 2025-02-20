"""CUCM System Configuration APIs."""

from datetime import datetime
from datetime import timedelta

from zeep.helpers import serialize_object

from .._internal_utils import flatten_signature_kwargs
from .._internal_utils import get_signature_locals
from .._internal_utils import nullstring_dict
from ..helpers import get_model_dict
from .base import DeviceAXLAPI
from .base import SimpleAXLAPI
from .vendorconfig import VendorConfig

from copy import deepcopy
import xmltodict    # JRE utility
import re           # JRE utility
from collections import OrderedDict
import click  # delete me
from lxml import etree  # jre testing
# JRE NOTE: lxml is being used but not imported - confirm we're good on that
# need to determine final location of VendorConfig Class

class ApplicationServer(SimpleAXLAPI):
    _factory_descriptor = "application_server"

    def add(self, name, appServerType, ipAddress=None, appUsers=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class AppServerInfo(SimpleAXLAPI):
    _factory_descriptor = "application_server_info"
    supported_methods = ["model", "create", "add", "get", "update", "remove", "add_update"]

    def add(self, appServerName, appServerContent, content=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class AudioCodecPreferenceList(SimpleAXLAPI):
    _factory_descriptor = "audio_codec_preference_list"

    def add(self, name, description, codecsInList, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class CallManager(DeviceAXLAPI):
    _factory_descriptor = "callmanager"
    supported_methods = ["get", "list", "update", "apply", "restart", "reset", "model"]  # added model


class CallManagerGroup(DeviceAXLAPI):
    _factory_descriptor = "callmanager_group"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "reset", "add_update"]

    def add(self, name, members, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DateTimeGroup(DeviceAXLAPI):
    _factory_descriptor = "date_time_group"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "reset", "add_update"]

    _add_defaults = {
            #'name':'',
            'timeZone': 'Europe/London',
            'separator': '-',
            'dateformat': 'M-D-Y',
            'timeFormat': '12-hour',
            #'phoneNtpReferences': {}
            }

    def add(self, name, timeZone, separator="-", dateformat="M-D-Y", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DeviceMobilityGroup(SimpleAXLAPI):
    _factory_descriptor = "device_mobility_group"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DeviceMobility(SimpleAXLAPI):
    _factory_descriptor = "device_mobility_info"

    def add(self, name, subNet, subNetMaskSz, members, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DevicePool(DeviceAXLAPI):
    _factory_descriptor = "device_pool"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "reset", "add_update"]

    def add(self, name, callManagerGroupName='Default', dateTimeSettingName='CMLocal', regionName='Default', **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    def _minimum_add_fields(self, **kwargs):
        """Experimental method to return only the mandatory fields for an add"""
        mandatory_fields = ['name', 'callManagerGroupName', 'dateTimeSettingName', 'regionName']

        minimum_fields = {}
        for field in minimum_fields:
            minimum_fields[field] = kwargs.get(field, None)

        return minimum_fields


class DhcpServer(SimpleAXLAPI):
    _factory_descriptor = "dhcp_server"

    def add(self, processNodeName, primaryTftpServerIpAddress=None, secondaryTftpServerIpAddress=None,
            primaryDnsIpAddress=None, secondaryDnsIpAddress=None, domainName=None, arpCacheTimeout=0,
            ipAddressLeaseTime=0, renewalTime=0, rebindingTime=0, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class EnterprisePhoneConfig(SimpleAXLAPI):
    _factory_descriptor = "enterprise_phone_config"
    supported_methods = ["get", "update", "patch", "model"]  # patch not part of API.  Q: do we add model?

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)
        self._get_model_name = "XEnterprisePhoneConfig"
        self.vendor_config = VendorConfig(connector,self._factory_descriptor)

    def get(self):
        """
        SQL/Thin version of GET
        
        Returns PKID so it can be used in future queries
        """

        return self.vendor_config.get_sql()

    def update(self, **kwargs):
        """
        SQL/Thin version of update

        this routine has reponsiblity to
            1) get the pkid
            2) validate and provide a proper vendorConfig as a dict
        """
        # will recevie a single element of vendorconfig

        LOCAL_DEBUG = True

        # must GET current config to retrieve PKID
        g = self.vendor_config.get_sql()

        pkid = g.get('pkid','')
        if pkid == '':
            print('ERROR: retrieving current enterprise phone config.')
            return 0
        
        # TODO: needs errro checking for all cases and how data could come in
        vendor_config = kwargs.get('vendorConfig', None)
        
        if LOCAL_DEBUG:
            print('UPDATE_SQL-KWARGS')
            print(kwargs)
            print(type(vendor_config))

        if isinstance(vendor_config, str):
            # if string, convert to a dict as an error check procedure
            try:
                vendor_config = self.vendor_config._xml_str_to_dict(vendor_config)
            except Exception as e:
                print(e)
                print('ERROR parsing xml string.')
                return 0

        # Q: do we want one last errorcheck to make sure we don't have a nother nexted vendorconfig?
        if vendor_config is not None:
            if isinstance(vendor_config, (dict, OrderedDict)):
                if LOCAL_DEBUG:
                    click.secho('About to UPDATE using SQL with dict of:', fg='blue')
                    print(vendor_config)
                    resp_u = self.vendor_config.update_sql(vendor_config, pkid=pkid)

                if LOCAL_DEBUG:                          
                    print(resp_u)

                return resp_u
        
        return 0

    def patch(self, param, value):
        """Utility method using Thin AXL to update a single entry in vendorConfig
        
        :param param:   parameter to update in XML string
        :param value:   value to insert
        
        :return:        0 or 1 from sql update.  All errors return 0
        """

        return self.vendor_config.patch(param, value)


    # experimental
    def get_thick(self):
        """
        AXL Thick version (working) with post processor for vendorConfig.  
        See if we keep it after doing the UPDATE version.
        Thin and Thick response are slightly different
        """
        axl_resp = self.connector.service.getEnterprisePhoneConfig()

        g = serialize_object(axl_resp)["return"][self._return_name]

        # post-process vendorConfig to a dict
        vc = g.get('vendorConfig', None)
        elements = vc.get('_value_1',[])
        
        if vc is not None:        
            g['vendorConfig'] = self.vendor_config._vc_to_dict(elements)
            
        return g

    # experimental
    def update_thick(self, **kwargs):
        """
        Attempt to correct ZEEP rendering issues with vendorConfig object
        This is not functioning and can eihter be deleted or kept for future
        investigation.

        Leverages code in VendorConfig() object

        # will recevie a single element of vendorconfig
        # we will rn the optional preprocessor on it
        # then it just runs an update and REPLACES teh value
        # if for sigle element then use patch

        """

        LOCAL_DEBUG = True

        # TODO: needs errro checking for all cases and how data could come in
        vendor_config = kwargs.get('vendorConfig', None)
        
        if LOCAL_DEBUG:
            print('UPDATE2-KWARGS')
            print(kwargs)
            print(type(vendor_config))
        
        # need to isolate the variable
        # then change it to a string
        
        if vendor_config is not None:
            if isinstance(vendor_config, (dict, OrderedDict)):
                if LOCAL_DEBUG:
                    click.secho('UPDATE2-IS DICT', fg='blue')
                #if vendor_config.get('vendorConfig', None) is not None:
                #    vendor_config = self.vendor_config._dict_to_lxml_elements(vendor_config['vendorConfig'])
                #else:
                #    vendor_config = self.vendor_config._dict_to_lxml_elements(vendor_config)
                vendor_config = self.vendor_config._dict_to_lxml_elements(vendor_config)
        
        if LOCAL_DEBUG:                          
            print(vendor_config)
        
        kwargs['vendorConfig'] = {'vendorConfig': vendor_config}
        kwargs['vendorConfig'] = vendor_config
        
        update_kwargs = flatten_signature_kwargs(self.update_thick, locals())

        # this is expeting an LXML object - do I have to get this all the way back to LXML?  Can't I just give a string?

        if LOCAL_DEBUG:
            click.secho('UPDATE_KWARGS before calling SUPER', fg='magenta')
            print(update_kwargs)
        return super().update(**update_kwargs)


class DhcpSubnet(SimpleAXLAPI):
    _factory_descriptor = "dhcp_subnet"

    def add(self, dhcpServerName, primaryStartIpAddress, primaryEndIpAddress, subnetIpAddress, subnetMask,
            primaryRouterIpAddress,  # making this mandatory for sanity-sake
            primaryTftpServerIpAddress=None, secondaryTftpServerIpAddress=None, primaryDnsIpAddress=None,
            secondaryDnsIpAddress=None, domainName=None, arpCacheTimeout=0, ipAddressLeaseTime=0, renewalTime=0,
            rebindingTime=0, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class LdapAuthentication(SimpleAXLAPI):
    _factory_descriptor = "ldap_authentication"
    supported_methods = ["get", "update", "model"]

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)
        self._get_model_name = "XLdapAuthentication"

    def get(self):
        axl_resp = self.connector.service.getLdapAuthentication()
        return serialize_object(axl_resp)["return"][self._return_name]

# experimental adding userRank to add_update
class LdapDirectory(SimpleAXLAPI):
    _factory_descriptor = "ldap_directory"
    supported_methods = [
        "model", "create", "add", "get", "update", "list", "remove",
        "sync", "get_sync_status", "add_update"
    ]

    def add(self, name, ldapDn, ldapPassword, userSearchBase, servers, intervalValue=7, scheduleUnit="DAY",
            nextExecTime=None, **kwargs):
        if not nextExecTime:
            nextExecTime = (datetime.now() + timedelta(days=intervalValue + 1)).strftime("%y-%m-%d 00:00")
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    def sync(self, name=None, uuid=None, sync=True):
        kwargs = get_signature_locals(self.get_sync_status, locals())
        axl_resp = self.connector.service.doLdapSync(**kwargs)
        return serialize_object(axl_resp)["return"]

    def get_sync_status(self, name=None, uuid=None):
        kwargs = get_signature_locals(self.get_sync_status, locals())
        axl_resp = self.connector.service.getLdapSyncStatus(**kwargs)
        return serialize_object(axl_resp)["return"]

    def add_update(self, obj_data):
        #unique add_update required in order to get userRank entry past filtering

        # if user ranks exists, then perform deepcopy for changes
        user_rank = obj_data.get('userRank', None)
        if user_rank is not None:
            obj_data = deepcopy(obj_data)
            user_rank = obj_data.pop('userRank', '')

        au = super().add_update(obj_data)

        # NOTE This has to be checked for an error in name
        # it SHOULD be the case that a raised error will pass this but
        # check to confirm
        if user_rank is not None:
            name = obj_data.get('name','')
            if name != '':
                u = self._update_rank(name, user_rank)
            
        return au

    def get(self, **kwargs):
        # currently, this only returns userRank if NO returned tags are entered
        
        returned_tags = kwargs.get('returnedTags', 'NO_RETURNED_TAGS')

        g = super().get(**kwargs)

        if returned_tags == 'NO_RETURNED_TAGS':
            name = kwargs.get('name','')
            if name != '':
                user_rank = self._get_rank(name)
                g['userRank'] = user_rank

        return g

    def _update_rank(self, name, user_rank):
        """Experimental user_rank update routine"""
 
        sql = f"update directorypluginconfig set userrank = '{user_rank}' where name='{name}'"
        return self.connector.sql.update(sql)
        

    def _get_rank(self, name):
        """Experiemental user-rank get routine"""

        sql = f"select userrank from directorypluginconfig where name='{name}'"
        s = self.connector.sql.query(sql)

        try:
            user_rank = s[0].get('userrank','')
        except Exception as e:
            user_rank = ''

        return user_rank


class LdapFilter(SimpleAXLAPI):
    _factory_descriptor = "ldap_filter"

    def add(self, name, filter, **kwargs):  # shadow not used
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class LdapSearch(SimpleAXLAPI):
    _factory_descriptor = "ldap_search"
    supported_methods = ["get", "list", "update"]


# issue - not working!
class LdapSyncCustomField(SimpleAXLAPI):
    _factory_descriptor = "ldap_custom_field"

    def add(self, ldapConfigurationName, customUserField, ldapUserField, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class LdapSystem(SimpleAXLAPI):
    _factory_descriptor = "ldap_system"
    supported_methods = ["get", "update", "model"]

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)
        self._get_model_name = "XLdapSystem"

    def get(self):
        axl_resp = self.connector.service.getLdapSystem()
        return serialize_object(axl_resp)["return"][self._return_name]

    def update(self, syncEnabled=True, ldapServer="Microsoft Active Directory", userIdAttribute="sAMAccountName"):
        return super().update(syncEnabled=syncEnabled, ldapServer=ldapServer, userIdAttribute=userIdAttribute)


class LbmGroup(SimpleAXLAPI):
    _factory_descriptor = "lbm_group"

    def add(self, name, ProcessnodeActive, ProcessnodeStandby=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class LbmHubGroup(SimpleAXLAPI):
    _factory_descriptor = "lbm_hub_group"

    def add(self, name, member1,
            member2=None,
            member3=None,
            members=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Location(SimpleAXLAPI):
    _factory_descriptor = "location"

    # experimental for add_update
    add_defaults = {
            }

    def add(self, name,
            betweenLocations=None,
            **kwargs):
        # this approach is probably not compatible with pre-9's flattened locations.
        # if warranted in future, would require extension for a version check.
        if not betweenLocations:
            betweenLocations = {
                "betweenLocation": {
                    "locationName": "Hub_None",
                    "audioBandwidth": 0,  # translates to 'UNLIMITED'
                    "videoBandwidth": 384,  # investigate default?
                    "immersiveBandwidth": 384,
                    "weight": 50
                }
            }
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class PresenceRedundancyGroup(SimpleAXLAPI):
    _factory_descriptor = "presence_redundancy_group"

    def add(self, name, server1, server2=None, haEnabled=False, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class PhoneNtp(SimpleAXLAPI):
    _factory_descriptor = "phone_ntp_reference"

    def add(self, ipAddress, mode="Directed Broadcast", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class PhysicalLocation(SimpleAXLAPI):
    _factory_descriptor = "physical_location"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class PresenceGroup(SimpleAXLAPI):
    _factory_descriptor = "presence_group"

    def add(self, name, presenceGroups=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class ProcessNode(SimpleAXLAPI):
    _factory_descriptor = "process_node"

    def add(self, name,
            processNodeRole="CUCM Voice/Video"):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Region(DeviceAXLAPI):
    _factory_descriptor = "region"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "restart", "add_update"]

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class ServiceParameter(SimpleAXLAPI):
    _factory_descriptor = "service_parameter"
    supported_methods = ["get", "list", "update", "reset_all", "model"]

    def reset_all(self, processNodeName, service):
        axl_resp = self.connector.service.doServiceParametersReset(processNodeName=processNodeName, service=service)
        return serialize_object(axl_resp)["return"]


# JRE NOTE: entpepriseParameter is not a true element in the schema so it's open to interpretation
#   how this should be implmemented.  Only items that exist in schema are
#       applyConfig, reset, restart
# get/update/list are actually part of service parameters
class EnterpriseParameter(ServiceParameter):
    _factory_descriptor = "enterprise_parameter"

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)
        self._return_name = "serviceParameter"
        self._get_method_name = "GetServiceParameterReq"
        self._get_model_name = "RServiceParameter"
        self._list_method_name = "ListServiceParameterReq"
        self._list_model_name = "LServiceParameter"
        # JRE Q: Should update_method_name be here? It's technically not
        # needed because it was only used for add_update and that method is meaningless here
        # self._update_method_name = "UpdateServiceParameterReq"

    def get(self, returnedTags=None, **kwargs):
        if "uuid" not in kwargs:
            if "processNodeName" not in kwargs:
                kwargs["service"] = "Enterprise Wide"
            if "service" not in kwargs:
                kwargs["processNodeName"] = "EnterpriseWideData"
        if isinstance(returnedTags, list):
            returnedTags = nullstring_dict(returnedTags)
        get_kwargs = flatten_signature_kwargs(self.get, locals())
        axl_resp = self.connector.service.getServiceParameter(**get_kwargs)
        return serialize_object(axl_resp)["return"][self._return_name]

    def list(self, searchCriteria=None, returnedTags=None, skip=None, first=None):
        # todo - warrants rework in base class
        if not searchCriteria:
            searchCriteria = {
                "processNodeName": "EnterpriseWideData",
                "service": "Enterprise Wide"
            }
        if not returnedTags:
            list_model = self._get_wsdl_obj(self._list_model_name)
            returnedTags = get_model_dict(list_model)
        elif isinstance(returnedTags, list):
            returnedTags = nullstring_dict(returnedTags)
        axl_resp = self.connector.service.listServiceParameter(searchCriteria=searchCriteria,
                                                               returnedTags=returnedTags,
                                                               skip=skip,
                                                               first=first)
        try:
            axl_list = serialize_object(axl_resp)["return"][self._return_name]

            # Disabled object factory due to issues with mutable mapping
            if self.USE_OBJECT_FACTORY:
                return [self.object_factory(self.__class__.__name__, item) for item in axl_list]
            else:
                return axl_list

        except TypeError:
            return []

    def reset_all(self):
        # todo - this violates LSP due to invalid method signature.  a case for class re-design
        axl_resp = self.connector.service.doEnterpriseParametersReset()
        return serialize_object(axl_resp)["return"]

    # jre testing
    # jre new attempt at update...will probably abandon and keep jels
    def update2(self, process_node_name, name, service, value):
        update_kwargs = {'processNodeName': 'EnterpriseWideData',
                        'name': name,
                        'service': 'Enterprise Wide',
                        'value': value}
        update_kwargs = flatten_signature_kwargs(self.update2, locals())
        return super().update(**update_kwargs)

class Srst(DeviceAXLAPI):
    _factory_descriptor = "srst"

    # experimental for add_update
    add_defaults = {
            #'name': '',
            'port': 2000,
            'SipPort': 5060,
            'isSecure': False
            }

    def add(self, name, ipAddress, SipNetwork=None, **kwargs):
        # there are corner cases, but this is a good for optimized usability
        #if not SipNetwork:
        #    SipNetwork = ipAddress
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# Experimental
class LicensedUser(SimpleAXLAPI):
    """
    Experimental: only has a GET and LIST
    Still making this a SimpleAXLAPI even though other methods are not supported
    SOLID principles imply this should be of of BaseAXLAPI and have GET code repeated
    """
    _factory_descriptor = "licensed_user"
    supported_methods= ['get', 'list']

    
# Experimental
class SmartLicenseStatus(SimpleAXLAPI):
    """
    Experimental: SmartLicenseStatus only has a GET
    Still making this a SimpleAXLAPI even though other methods are not supported
    SOLID principles imply this should be of of BaseAXLAPI and have GET code repeated

    BUG: Is not returning <return> but is going straight to <LicenseDetails>
    BUG: Confirmed on both 12.5 and 14.0.   Need to see whether WSDL needs to be edited for this

    Implementing this manually with xmltodict rather than editing WSDL files.   If <return> had been
    there, the response would start with ['LicenseDetails'] so this is what this routine will return.
    
    """
    
    _factory_descriptor = "smart_license_status"
    supported_methods = ['get']

    def get(self, **kwargs):
        """Get method for API endpoint"""

        LOCAL_DEBUG = False

        try:
            # force XML raw response for this call to bypass ZEEP processing
            with self.connector._client.settings(raw_response=True):
                r = self.connector.service.getSmartLicenseStatus()
        except Exception as e:
            print(e)                    

        resp_dict = {}
        if r.status_code==200:
            try:
                # strip namespaces from response
                namespaces = {'http://www.w3.org/2001/XMLSchema-instance' : None}
                resp_dict = xmltodict.parse(r.content, namespaces=namespaces)  

                if LOCAL_DEBUG:
                    print('Zeep Response: ')
                    print(r.content)

                    print('DICT Result')
                    print(resp_dict)

                license_details = resp_dict['soapenv:Envelope']['soapenv:Body']['ns:getSmartLicenseStatusResponse']
                license_details.pop('@xmlns:ns', '')        # remove NS from resulting dict

                return license_details
            
            except Exception as e:
                print(e)

        # NOTE: this is NOT processing any error conditions yet
        # TODO: remove @xmlns:ns element if not desired

        return {}
    

