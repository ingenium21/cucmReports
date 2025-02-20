"""CUCM AXL Device APIs."""

from .._internal_utils import flatten_signature_kwargs
from .base import DeviceAXLAPI
from .base import SimpleAXLAPI
from .vendorconfig import VendorConfig

class CommonDeviceConfig(DeviceAXLAPI):
    _factory_descriptor = "common_device_config"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "reset", "add_update"]

    def add(self, name, softkeyTemplateName=None, userLocale=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# JRE adding vendorConfig processing
class CommonPhoneConfig(DeviceAXLAPI):
    _factory_descriptor = "common_phone_profile"
    supported_methods = ["model", "create", "add", "get", "list", "update", "remove", "apply", "reset", "add_update"]

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)
        self.vendor_config = VendorConfig(connector,self._factory_descriptor)

    # added vendorConfig pre-procssing (needs optimizing)
    def add(self, name, unlockPwd=None, featureControlPolicy=None, **kwargs):

        LOCAL_DEBUG = False

        # pop vendorConfig if it exists for later processing
        vc_data = kwargs.pop('vendorConfig', None)
        if LOCAL_DEBUG:
            print('PRE FOUND DATA FOR vc_data')
            print(vc_data)
        
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        a = super().add(**add_kwargs)

        # then post-process by updating the vendorConfig using SQL
        if vc_data is not None:
            if LOCAL_DEBUG:
                print(a)


            # get pkid from a sql query - this will NOT be the pkid of the CPC but the XML entry
            sql_get = self.vendor_config.get_sql(name=name)
            if LOCAL_DEBUG:
                print('OUTPUT FROM GET_SQL IN UPDATE METHOD ')
                print(sql_get)
                print(vc_data)
            xml_pkid = sql_get.get('pkid','')
            if xml_pkid != '':
                vc_u = self.vendor_config.update_sql(vc_data, pkid=xml_pkid) 
                if vc_u == 1:
                    if LOCAL_DEBUG:
                        print('VC UPDATE SUCCESSFUL IN CPC_UPDATE')
                else:
                    print('ERROR: ADD SUCCEEDS BUT VC_UPDATE FAILED')

        return a
    
    # added vendor_config processing (needs optimizing)
    def get(self, **kwargs):
        g = super().get(**kwargs)

        # confirm a good name came back from get, then replace vendorConfig with SQL response
        name = g.get('name', None)
        if name is not None:
            vc = self.vendor_config.get_sql(name=name)
            g['vendorConfig'] = vc['vendorConfig']

        return g
    
    # added vendor_config processing (needs optimizing)
    # TODO: enhance this to handle if the CHOICE was a UUID rather than the name
    #   this means the get_sql command would need to be updated to handle either.
    def update(self, **kwargs):
        
        LOCAL_DEBUG = False

        # pop vendorConfig if it exists for later processing
        vc_data = kwargs.pop('vendorConfig', None)
        if LOCAL_DEBUG:
            print('PRE FOUND DATA FOR vc_data')
            print(vc_data)

        u = super().update(**kwargs)


        # then post-process by updating the vendorConfig using SQL
        if vc_data is not None:
            if LOCAL_DEBUG:
                print(u)

            # get pkid from a sql query - this will NOT be the pkid of the CPC but the XML entry
            sql_get = self.vendor_config.get_sql(name=kwargs.get('name','__BAD_ENTRY__'))
            if LOCAL_DEBUG:
                print('OUTPUT FROM GET_SQL IN UPDATE METHOD ')
                print(sql_get)
                print(vc_data)
            xml_pkid = sql_get.get('pkid','')
            if xml_pkid != '':
                vc_u = self.vendor_config.update_sql(vc_data, pkid=xml_pkid) 
                if vc_u == 1:
                    if LOCAL_DEBUG:
                        print('VC UPDATE SUCCESSFUL IN CPC_UPDATE')
                else:
                    print('ERROR: UPDATE SUCCEEDS BUT VC_UPDATE FAILED')
        return u
    
    # not in API, added utility function
    def patch(self, name, param, value):
        """Utility method using Thin AXL to update a single entry in vendorConfig
        
        :param param:   parameter to update in XML string
        :param value:   value to insert
        :param name:    name of profile to edit
        :return:        0 or 1 from sql update.  All errors return 0
        """
        g = self.vendor_config.get_sql(name=name)

        pkid = g.get('pkid','')
        if pkid != '':
            return self.vendor_config.patch(param=param, value=value, name=name)
        else:
            print('ERROR: Name of CPC not found')
            return 0
        

# JRE is protocolSide="User" required for add?
class CtiRoutePoint(DeviceAXLAPI):
    _factory_descriptor = "cti_route_point"

    def add(self, name, devicePoolName, product="CTI Route Point", protocol="SCCP", **kwargs):
        if "class" not in kwargs:  # workaround for restricted 'class' attribute
            kwargs["class"] = "CTI Route Point"
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DefaultDeviceProfile(SimpleAXLAPI):
    _factory_descriptor = "default_device_profile"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "options", "add_update"]

    def add(self, name, product, phoneButtonTemplate="Universal Device Template Button Layout", softkeyTemplate=None,
            protocol="SIP", protocolSide="User", **kwargs):
        # the name is not obvious in the UI.  It appears to default to a concat of product and protocol.
        # it may be useful to log a warning for this...
        if "class" not in kwargs:  # workaround for restricted 'class' attribute
            kwargs["class"] = "Device Profile"
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class DeviceProfile(SimpleAXLAPI):
    _factory_descriptor = "udp"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "options", "add_update"]

    def add(self, name, product, phoneTemplateName,
            protocol="SIP",
            **kwargs):
        if "class" not in kwargs:  # workaround for restricted 'class' attribute
            kwargs["class"] = "Device Profile"
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class FeatureControlPolicy(SimpleAXLAPI):
    _factory_descriptor = "feature_control_policy"

    def add(self, name,
            features=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class IpPhoneServices(SimpleAXLAPI):
    _factory_descriptor = "ip_phone_service"

    def add(self, serviceName, asciiServiceName, serviceUrl, secureServiceUrl=None, serviceCategory="XML Service",
            serviceType="Standard IP Phone Service", enabled=True, enterpriseSubscription=False, parameters=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Line(DeviceAXLAPI):
    _factory_descriptor = "line"
    supported_methods = [
        "model", "create", "add", "get", "update", "list", "remove", 
        "options", "apply", "restart", "reset", "add_update"
    ]

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)

    def add(self, pattern, routePartitionName,
            usage="Device",
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class NetworkAccessProfile(SimpleAXLAPI):
    _factory_descriptor = "network_access_profile"

    def add(self, name, vpnRequired="Default", proxySettings="None", proxyHostname="", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class Phone(DeviceAXLAPI):
    _factory_descriptor = "phone"
    supported_methods = [
        "model", "create", "add", "get", "list", "update", "remove",
        "options", "wipe", "lock",
        "apply", "restart", "reset",
        "add_update"
    ]

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)
        self.vendor_config = VendorConfig(connector,self._factory_descriptor)

    @staticmethod
    def _check_confidential_access(confidentialAccess):
        """Workaround for AXL defect not accepting None for 'confidentialAccessMode'"""
        if not confidentialAccess['confidentialAccessMode']:
            confidentialAccess['confidentialAccessMode'] = ''
        return confidentialAccess

    def add(self, name, product, devicePoolName, locationName="Hub_None", protocol="SIP",
            commonPhoneConfigName="Standard Common Phone Profile", **kwargs):
        
        LOCAL_DEBUG = True

        if "class" not in kwargs:  # workaround for restricted 'class' attribute
            kwargs["class"] = "Phone"

        # POP vendorConfig for later processing
        vc_data = kwargs.pop('vendorConfig', None)

        add_kwargs = flatten_signature_kwargs(self.add, locals())
        try:
            add_kwargs['confidentialAccess'] = self._check_confidential_access(add_kwargs['confidentialAccess'])
        except KeyError:
            pass
        a = super().add(**add_kwargs)

        # then post-process by updating the vendorConfig using SQL
        if vc_data is not None:
            if LOCAL_DEBUG:
                print(a)
            
            # convert vendorConfig dict to an xml string 
            vc_xml = self.vendor_config._dict_to_xml_str(vc_data)

            # run update - will return 'u' from original update regardless of outcome if VC update
            r = self.vendor_config._update_phone_vendor_config(kwargs.get['name'], vc_xml)

            if LOCAL_DEBUG:
                print(r)

        return a


    # adding vendor_config processing (needs optimizing)
    def get(self, **kwargs):

        LOCAL_DEBUG = False

        g = super().get(**kwargs)


        name = g.get('name', None)
        vendor_config = g.get('vendorConfig', None)

        # confirm a good name came back from get, then replace vendorConfig with SQL response
        # TO ENHANCE: This vendor_config operation is expensive and should only be done if vendorConfig
        # is in the returned Tags.  Make this conditional on it's existence
        # Need to handle:
        #       not in returnedTags so comes back as ('vendorConfig', OrderedDict([('_value_1', None)]))
        #       in returnedTags but has no value
        #       has a value
        #
        # TODO: this mess is still being tested for all cases.  Once tested, clean it up
        #
        vc = g.get('vendorConfig','MISSING')
        if LOCAL_DEBUG:
            print(vc)
        vc = vc.get('_value_1','MISSING')
        if vc is None:
            if LOCAL_DEBUG:
                print('VC is none')
            vc_exists = False
        else:
            vc_exists = True

        if LOCAL_DEBUG:
            print('GET testing vendorConfig limitations')
            rt = kwargs.get('returnedTags','MISSING')
            print('KWARGS ReturnedTags:')
            print(rt)
            rt2 = g.get('vendorConfig','MISSING')
            print('vendorConfig from get:')
            print(rt2)
            print(g)

    
        # only perform SQL query if response worked and it has a vendorConfig populated
        if name is not None and vc_exists:      
            vc = self.vendor_config.get_sql(name=name)
            g['vendorConfig'] = vc['vendorConfig']

            if LOCAL_DEBUG:
                print(f'PHONE-GET-returned a vc of: {vc}')

        return g

    def update(self, **kwargs):

        LOCAL_DEBUG = True

        try:
            kwargs['confidentialAccess'] = self._check_confidential_access(kwargs['confidentialAccess'])
        except KeyError:
            pass

        # POP vendorConfig if it exists
        vc_data = kwargs.pop('vendorConfig', None)

        u = super().update(**kwargs)

        # then post-process by updating the vendorConfig using SQL
        if vc_data is not None:
            if LOCAL_DEBUG:
                print(u)
            
            # convert vendorConfig dict to an xml string 
            vc_xml = self.vendor_config._dict_to_xml_str(vc_data)

            # run update - will return 'u' from original update regardless of outcome if VC update
            r = self.vendor_config._update_phone_vendor_config(kwargs.get['name'], vc_xml)

            if LOCAL_DEBUG:
                print(r)

        return u

    def wipe(self, **kwargs):
        """Allows Cisco's newer Android-based devices, like the Cisco DX650,
        to be remotely reset to factory defaults, removing user specific settings and data.

        :param kwargs: phone name or uuid
        :return: None
        """
        # check_identifiers(self._wsdl_objects["name_and_guid_model"], **kwargs)
        return self._serialize_axl_object("wipe", **kwargs)

    def lock(self, **kwargs):
        return self._serialize_axl_object("lock", **kwargs)


class PhoneLine(DeviceAXLAPI):
    """ JRE Added
    EXPERIMENTAL
    # this class will exist only so that you can get models for PhoneLines using
    # the existing libraries. I've add add/update/get just so that the model functions will work.
    # basically, it's here to support utility functions for manipulating phone lines.
    """
    _factory_descriptor = "phone_line"
    supported_methods = ["model", "create", "add", "update", "get", "add_update"]

    def add(self, **kwargs):
        raise NotImplementedError

    def update(self, **kwargs):
        raise NotImplementedError

    def get(self, **kwargs):
        raise NotImplementedError


class PhoneButtonTemplate(DeviceAXLAPI):
    _factory_descriptor = "phone_button_template"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "restart", "add_update"]

    def add(self, name, basePhoneTemplateName, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class PhoneSecurityProfile(DeviceAXLAPI):
    _factory_descriptor = "phone_security_profile"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "restart", "add_update"]

    def add(self, name, phoneType="Universal Device Template", protocol="Protocol Not Specified",
            deviceSecurityMode=None, authenticationMode="By Null String", keySize=1024, transportType="TCP+UDP",
            sipPhonePort=5060, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RecordingProfile(SimpleAXLAPI):
    _factory_descriptor = "recording_profile"

    def add(self, name, recorderDestination, recordingCssName=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RemoteDestination(SimpleAXLAPI):
    _factory_descriptor = "remote_destination"

    def add(self, destination, ownerUserId, name=None, enableUnifiedMobility=True, enableMobileConnect=True,
            isMobilePhone=True, remoteDestinationProfileName=None, dualModeDeviceName=None, lineAssociations=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class RemoteDestinationProfile(SimpleAXLAPI):
    _factory_descriptor = "rdp"

    def add(self, name, devicePoolName, userId, rerouteCallingSearchSpaceName=None, callingSearchSpaceName=None,
            lines=None, product="Remote Destination Profile", protocol="Remote Destination", protocolSide="User",
            **kwargs):
        if "class" not in kwargs:  # workaround for restricted 'class' attribute
            kwargs["class"] = "Remote Destination Profile"
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# why does this have a class of trunk (JRE)
# commenting that out
class SdpTransparencyProfile(SimpleAXLAPI):
    _factory_descriptor = "sdp_transparency_profile"

    def add(self, name, attributeSet, **kwargs):
        #if "class" not in kwargs:
        #    kwargs["class"] = "Trunk"
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SipTrunk(DeviceAXLAPI):
    _factory_descriptor = "sip_trunk"

    def add(self, name, devicePoolName, destinations, product="SIP Trunk", locationName="Hub_None", protocol="SIP",
            securityProfileName="Non Secure SIP Trunk Profile", sipProfileName="Standard SIP Profile",
            presenceGroupName="Standard Presence Group", protocolSide="Network", **kwargs):
        if "class" not in kwargs:
            kwargs["class"] = "Trunk"
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SipProfile(DeviceAXLAPI):
    _factory_descriptor = "sip_profile"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "options", "apply", "restart", "add_update"]

    def add(self, name, sdpTransparency="Pass all unknown SDP attributes", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SipTrunkSecurityProfile(DeviceAXLAPI):
    _factory_descriptor = "sip_trunk_security_profile"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "reset", "add_update"]

    def add(self, name, acceptPresenceSubscription=False, acceptOutOfDialogRefer=False,
            acceptUnsolicitedNotification=False, allowReplaceHeader=False, transmitSecurityStatus=False, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SoftKeyTemplate(DeviceAXLAPI):
    _factory_descriptor = "softkey_template"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "apply", "restart", "add_update"]

    def add(self, name, description,
            baseSoftkeyTemplateName="Standard User",
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SoftKeySet(SimpleAXLAPI):
    _factory_descriptor = "softkey_set"
    supported_methods = ["get", "update"]   # no model


# JRE removed lineLabel=None, directoryNumber=None, displayCallerId=None, 
# need to review factory descriptor
class UniversalDeviceTemplate(SimpleAXLAPI):
    _factory_descriptor = "udt"

    def add(self, name, devicePool, callingSearchSpace=None,
            sipProfile="Standard SIP Profile", commonPhoneProfile="Standard Common Phone Profile",
            phoneButtonTemplate="Universal Device Template Button Layout",
            deviceSecurityProfile="Universal Device Template - Model-independent Security Profile",
            blfPresenceGroup="Standard Presence group", location="Hub_None", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# JRE added - experimental
# NOTE: Case of this breaks rules for camel/snake case
# not sure how it will behave yet.
# assuming default supported_methods
class SIPNormalizationScript(SimpleAXLAPI):
    _factory_descriptor = "sip_normalization_script"

    def add(self, name, content, scriptExecutionErrorRecoveryAction="Message Rollback Only",
            systemResourceErrorRecoveryAction="Disable Script", maxMemoryThreshold=50,
            maxLuaInstructionsThreshold=1000, isStandard=False, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class UniversalLineTemplate(SimpleAXLAPI):
    _factory_descriptor = "ult"

    def add(self, name, routePartition=None, lineDescription=None, callingSearchSpace=None, voiceMailProfile=None,
            alertingName=None, rejectAnonymousCall=False,  # override inconsistency between normal line add and ULT
            blfPresenceGroup="Standard Presence group", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class WifiHotspot(SimpleAXLAPI):
    _factory_descriptor = "wifi_hotspot"

    def add(self, name, ssidPrefix, frequencyBand="Auto", userModifiable="Allowed", authenticationMethod="None",
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class WLANProfile(SimpleAXLAPI):
    _factory_descriptor = "wlan_profile"

    def add(self, name, ssid, frequencyBand="Auto", userModifiable="Allowed", authMethod="EAP-FAST",
            networkAccessProfile=None, userName="", password="", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class WlanProfileGroup(SimpleAXLAPI):
    _factory_descriptor = "wlan_profile_group"

    def add(self, name,
            members=None,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)
