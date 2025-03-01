"""python-zeep client wrappers for Cisco UC SOAP APIs"""

import os

import urllib3
from lxml import etree
from requests import Session
from requests.auth import HTTPBasicAuth
from urllib3.exceptions import InsecureRequestWarning
from zeep import Client
from zeep.cache import SqliteCache
from zeep.plugins import HistoryPlugin
from zeep.transports import Transport
from zeep import Settings   # JRE attempting fix for SIP_PROFILE Bug

from .api import *
from .model import axl_factory

from pprint import pprint

def get_connection_kwargs(env_dict, kwargs):
    """Get zeep client kwargs by consolidating environment variables and statically defined attributes.

    Note:
    Static parameters take precedence over env vars, if they exist.

    :param env_dict: dict mapping connection argument names to environment variable names
    :param kwargs: __init__ input args
    :return: kwargs with updated connection parameter values
    """
    connection_kwargs = {k: os.environ.get(v) for k, v in env_dict.items()}
    connection_kwargs.update(kwargs)

    return connection_kwargs


class AXLHistoryPlugin(HistoryPlugin):
    """Simple HistoryPlugin extension for easy xml extraction"""

    @staticmethod
    def _parse_envelope(envelope):
        return etree.tostring(envelope, encoding="unicode", pretty_print=True)

    @property
    def last_received_xml(self):
        last_tx = self._buffer[-1]
        if last_tx:
            return self._parse_envelope(last_tx['received']['envelope'])

    @property
    def last_sent_xml(self):
        last_tx = self._buffer[-1]
        if last_tx:
            return self._parse_envelope(last_tx['sent']['envelope'])


class UCSOAPConnector(object):
    """Parent class for all Cisco UC SOAP Connectors"""

    def __init__(self, username=None, password=None, wsdl=None, binding_name=None, address=None, tls_verify=False,
                 timeout=10, history=True, history_maxlen=1, strict=True):
        """Instantiate UC SOAP Client Connector

        :param username: SOAP client connector username
        :param password: SOAP client connector password
        :param wsdl: SOAP WSDL location
        :param binding_name: QName of the binding
        :param address: address of the endpoint
        :param tls_verify: /path/to/certificate.pem or False.  Certificate must be a CA_BUNDLE. Supports .pem and .crt
        :param is_async: create async client
        :param strict:   Zeep uses strict interpretation of WSDL (True by default.  Experimental for testing)
        :param timeout: timeout in seconds.  Overrides zeep 300 default to timeout after 30sec
        """
        self._username = username
        self._wsdl = wsdl
        self._timeout = timeout

        self._session = Session()
        self._session.auth = HTTPBasicAuth(username, password)
        self._session.verify = tls_verify
        self._plugins = []

        self._settings = Settings(strict=strict)    

        if not self._session.verify:
            urllib3.disable_warnings(InsecureRequestWarning)

        if history:
            self._history = AXLHistoryPlugin(maxlen=history_maxlen)
            self._plugins.append(self._history)

        transport = Transport(cache=SqliteCache(),
                              session=self._session,
                              timeout=self._timeout)


        self._client = Client(wsdl=wsdl, transport=transport, plugins=self._plugins, settings=self._settings)
        if binding_name and address:
            self._service = self._client.create_service(binding_name, address)
        elif binding_name or address:
            raise ValueError("Incomplete parameters for ServiceProxy Object creation.  "
                             "Requires 'binding_name' and 'address'")
        self.model_factory = self._client.type_factory('ns0')

    @property
    def timeout(self):
        return self._timeout

    @property
    def wsdl(self):
        return self._wsdl

    @property
    def client(self):
        """Direct access to zeep client for wsdl inspection or advanced in-line client modification,
        factory building, etc."""
        return self._client

    @property
    def service(self):
        """Direct access to zeep service for method-calling of proxied services"""
        return self._service

    @property
    def history(self):
        return self._history


class UCMAXLConnector(UCSOAPConnector):
    """UCM AXL API Connector"""

    _ENV = {
        "username": "AXL_USERNAME",
        "password": "AXL_PASSWORD",
        "fqdn": "AXL_FQDN",
        "wsdl": "AXL_WSDL_URL"
    }

    def __init__(self, **kwargs):
        connection_kwargs = get_connection_kwargs(self._ENV, kwargs)
        connection_kwargs["binding_name"] = "{http://www.cisco.com/AXLAPIService/}AXLAPIBinding"
        connection_kwargs["address"] = "https://{fqdn}:8443/axl/".format(**connection_kwargs)
        del connection_kwargs["fqdn"]  # remove fqdn as not used in super() call
        super().__init__(**connection_kwargs)

        # sql API wrapper
        self.sql = ThinAXLAPI(self, axl_factory)

        # device
        self.device = Device(self, axl_factory)

        # device API wrappers
        self.common_device_config = CommonDeviceConfig(self, axl_factory)
        self.common_phone_config = CommonPhoneConfig(self, axl_factory)             # proper schema name
        self.common_phone_profile = CommonPhoneConfig(self, axl_factory)            # alias 
        self.cti_route_point = CtiRoutePoint(self, axl_factory)
        self.feature_control_policy = FeatureControlPolicy(self, axl_factory)
        self.ip_phone_services = IpPhoneServices(self, axl_factory)                 # proper schema name (note it's plural)
        self.ip_phone_service = IpPhoneServices(self, axl_factory)                  # alias
        self.line = Line(self, axl_factory)
        self.network_access_profile = NetworkAccessProfile(self, axl_factory)
        self.phone = Phone(self, axl_factory)
        self.phone_line = PhoneLine(self, axl_factory)                              # jre added, not in schema
        self.default_device_profile = DefaultDeviceProfile(self, axl_factory)
        self.device_profile = DeviceProfile(self, axl_factory)                      # proper schema name
        self.udp = DeviceProfile(self, axl_factory)                                 # alias
        self.phone_button_template = PhoneButtonTemplate(self, axl_factory)
        self.phone_security_profile = PhoneSecurityProfile(self, axl_factory)
        self.recording_profile = RecordingProfile(self, axl_factory)
        self.sdp_transparency_profile = SdpTransparencyProfile(self, axl_factory)
        self.sip_trunk = SipTrunk(self, axl_factory)
        self.sip_trunk_security_profile = SipTrunkSecurityProfile(self, axl_factory)
        self.sip_profile = SipProfile(self, axl_factory)
        self.sip_normalization_script = SIPNormalizationScript(self, axl_factory)
        self.soft_key_template = SoftKeyTemplate(self, axl_factory)                     # proper schema name
        self.softkey_template = SoftKeyTemplate(self, axl_factory)                      # alias
        self.soft_key_set = SoftKeySet(self, axl_factory)                               # proper schema name
        self.softkey_set = SoftKeySet(self, axl_factory)                                # alias
        self.universal_device_template = UniversalDeviceTemplate(self, axl_factory)     # proper schema name
        self.udt = UniversalDeviceTemplate(self, axl_factory)                           # alias
        self.universal_line_template = UniversalLineTemplate(self, axl_factory)         # proper schema name
        self.ult = UniversalLineTemplate(self, axl_factory)                             # alias
        self.remote_destination_profile = RemoteDestinationProfile(self, axl_factory)   # proper schema name
        self.rdp = RemoteDestinationProfile(self, axl_factory)                          # alias
        self.remote_destination = RemoteDestination(self, axl_factory)
        self.wifi_hotspot = WifiHotspot(self, axl_factory)
        self.wlan_profile = WLANProfile(self, axl_factory)                              # Case issue in name
        self.wlan_profile_group = WlanProfileGroup(self, axl_factory)

        # user API wrappers
        self.app_user = AppUser(self, axl_factory)                                      # proper schema name
        self.application_user = AppUser(self, axl_factory)                              # alias
        self.application_user_capf_profile = ApplicationUserCapfProfile(self, axl_factory)
        self.credential_policy = CredentialPolicy(self, axl_factory)
        self.credential_policy_default = CredentialPolicyDefault(self, axl_factory)
        self.end_user_capf_profile = EndUserCapfProfile(self, axl_factory)
        self.feature_group_template = FeatureGroupTemplate(self, axl_factory)
        self.user = User(self, axl_factory)
        self.uc_service = UcService(self, axl_factory)
        self.sip_realm = SipRealm(self, axl_factory)
        self.self_provisioning = SelfProvisioning(self, axl_factory)
        self.service_profile = ServiceProfile(self, axl_factory)
        self.user_group = UserGroup(self, axl_factory)
        self.user_profile_provision = UserProfileProvision(self, axl_factory)           # proper schema name
        self.user_profile = UserProfileProvision(self, axl_factory)                     # alias
        self.user_rank = UserRank(self, axl_factory)                                    # ADD-ON (not in Cisco spec)
        self.user_role = UserRole(self, axl_factory)                                    # ADD-ON (not in Cisco spec)
        
        # dialplan API wrappers
        self.caller_filter_list = CallerFilterList(self, axl_factory)
        self.advertised_patterns = AdvertisedPatterns(self, axl_factory)
        self.aar_group = AarGroup(self, axl_factory)
        self.application_dial_rules = ApplicationDialRules(self, axl_factory)
        self.blocked_learned_patterns = BlockedLearnedPatterns(self, axl_factory)
        self.call_pickup_group = CallPickupGroup(self, axl_factory)
        self.call_park = CallPark(self, axl_factory)
        self.called_party_transformation_pattern = CalledPartyTransformationPattern(self, axl_factory)      # proper schema name
        self.called_party_xform_pattern = CalledPartyTransformationPattern(self, axl_factory)               # alias
        self.calling_party_transformation_pattern = CallingPartyTransformationPattern(self, axl_factory)    # proper schema name
        self.calling_party_xform_pattern = CallingPartyTransformationPattern(self, axl_factory)             # alias
        self.transformation_profile = TransformationProfile(self, axl_factory)
        self.conference_now = ConferenceNow(self, axl_factory)
        self.cmc_info = CmcInfo(self, axl_factory)                                  # proper schema name
        self.cmc = CmcInfo(self, axl_factory)                                       # alias
        self.css = Css(self, axl_factory)
        self.directed_call_park = DirectedCallPark(self, axl_factory)
        self.directory_lookup_dial_rules = DirectoryLookupDialRules(self, axl_factory)          # proper schema name
        self.directory_lookup_rules = DirectoryLookupDialRules(self, axl_factory)               # alias
        self.enterprise_feature_access_configuration = EnterpriseFeatureAccessConfiguration(self, axl_factory)  # proper schema name
        self.mobility_enterprise_feature_access_number = EnterpriseFeatureAccessConfiguration(self, axl_factory)    # alias
        self.fac_info = FacInfo(self, axl_factory)                                  # proper schema name
        self.fac = FacInfo(self, axl_factory)                                       # alias
        self.handoff_mobility = Mobility(self, axl_factory)
        self.handoff_configuration = HandoffConfiguration(self, axl_factory)
        self.http_profile = HttpProfile(self, axl_factory)
        self.meet_me = MeetMe(self, axl_factory)
        self.mobility_profile = MobilityProfile(self, axl_factory)
        self.hunt_list = HuntList(self, axl_factory)
        self.hunt_pilot = HuntPilot(self, axl_factory)
        self.line_group = LineGroup(self, axl_factory)
        self.local_route_group = LocalRouteGroup(self, axl_factory)
        self.route_filter = RouteFilter(self, axl_factory)
        self.route_group = RouteGroup(self, axl_factory)
        self.route_list = RouteList(self, axl_factory)
        self.route_partition = RoutePartition(self, axl_factory)
        self.route_pattern = RoutePattern(self, axl_factory)
        self.route_plan = RoutePlan(self, axl_factory)                      # proper schema name
        self.route_plan_report = RoutePlan(self, axl_factory)               # alias
        self.sip_dial_rules = SipDialRules(self, axl_factory)
        self.sip_route_pattern = SipRoutePattern(self, axl_factory)
        self.time_period = TimePeriod(self, axl_factory)
        self.time_schedule = TimeSchedule(self, axl_factory)
        self.trans_pattern = TransPattern(self, axl_factory)                # proper schema name
        self.translation_pattern = TransPattern(self, axl_factory)          # alias
        self.route_partitions_for_learned_patterns = RoutePartitionsForLearnedPatterns(self, axl_factory)
        self.elin_group = ElinGroup(self, axl_factory)

        # system API wrappers
        self.application_server = ApplicationServer(self, axl_factory)
        self.audio_codec_preference_list = AudioCodecPreferenceList(self, axl_factory)
        self.call_manager_group = CallManagerGroup(self, axl_factory)       # proper schema name
        self.callmanager_group = CallManagerGroup(self, axl_factory)        # alias
        self.date_time_group = DateTimeGroup(self, axl_factory)
        self.device_mobility_group = DeviceMobilityGroup(self, axl_factory)
        self.device_mobility = DeviceMobility(self, axl_factory)            # proper schema name
        self.device_mobility_info = DeviceMobility(self, axl_factory)       # alias
        self.device_pool = DevicePool(self, axl_factory)
        self.ldap_directory = LdapDirectory(self, axl_factory)
        self.ldap_filter = LdapFilter(self, axl_factory)
        self.ldap_sync_custom_field = LdapSyncCustomField(self, axl_factory)
        self.lbm_group = LbmGroup(self, axl_factory)
        self.lbm_hub_group = LbmHubGroup(self, axl_factory)
        self.location = Location(self, axl_factory)
        self.presence_redundancy_group = PresenceRedundancyGroup(self, axl_factory)
        self.phone_ntp= PhoneNtp(self, axl_factory)                         # proper schema name
        self.phone_ntp_reference = PhoneNtp(self, axl_factory)              # alias
        self.physical_location = PhysicalLocation(self, axl_factory)
        self.presence_group = PresenceGroup(self, axl_factory)
        self.region = Region(self, axl_factory)
        self.srst = Srst(self, axl_factory)
        self.service_parameter = ServiceParameter(self, axl_factory)
        self.enterprise_parameter = EnterpriseParameter(self, axl_factory)
        self.ldap_system = LdapSystem(self, axl_factory)
        self.ldap_authentication = LdapAuthentication(self, axl_factory)
        self.ldap_search = LdapSearch(self, axl_factory)
        self.call_manager = CallManager(self, axl_factory)                  # proper schema name
        self.callmanager = CallManager(self, axl_factory)                   # alias
        self.process_node = ProcessNode(self, axl_factory)
        self.dhcp_server = DhcpServer(self, axl_factory)
        self.dhcp_subnet = DhcpSubnet(self, axl_factory)
        self.enterprise_phone_config = EnterprisePhoneConfig(self, axl_factory)

        self.smart_license_status = SmartLicenseStatus(self, axl_factory)   # Experimental
        self.licensed_user = LicensedUser(self, axl_factory)                # Experimental

        # media API wrappers
        self.announcement = Announcement(self, axl_factory)
        self.annunciator = Annunciator(self, axl_factory)
        self.conference_bridge = ConferenceBridge(self, axl_factory)
        self.fixed_moh_audio_source = FixedMohAudioSource(self, axl_factory)
        self.media_resource_group = MediaResourceGroup(self, axl_factory)       # proper schema name
        self.mrg = MediaResourceGroup(self, axl_factory)                        # alias
        self.media_resource_list = MediaResourceList(self, axl_factory)         # proper schema name
        self.mrgl = MediaResourceList(self, axl_factory)                        # alias
        self.mtp = Mtp(self, axl_factory)
        self.transcoder = Transcoder(self, axl_factory)
        self.mobile_voice_access = MobileVoiceAccess(self, axl_factory)
        self.moh_audio_source = MohAudioSource(self, axl_factory)
        self.moh_server = MohServer(self, axl_factory)
        self.voh_server = VohServer(self, axl_factory)

        # advanced API wrappers
        self.called_party_tracing = CalledPartyTracing(self, axl_factory)
        self.dir_number_alias_lookupand_sync = DirNumberAliasLookupandSync(self, axl_factory)   # proper schema name
        self.directory_number_alias_sync = DirNumberAliasLookupandSync(self, axl_factory)       # alias
        self.ils_config = IlsConfig(self, axl_factory)
        self.message_waiting = MessageWaiting(self, axl_factory)            # proper schema name
        self.mra_service_domain = MraServiceDomain(self, axl_factory)
        self.mwi_number = MessageWaiting(self, axl_factory)                 # alias
        self.remote_cluster = RemoteCluster(self, axl_factory)
        self.voice_mail_pilot = VoiceMailPilot(self, axl_factory)           # proper schema name
        self.voicemail_pilot = VoiceMailPilot(self, axl_factory)            # alias
        self.voice_mail_profile = VoiceMailProfile(self, axl_factory)       # proper schema name
        self.voicemail_profile = VoiceMailProfile(self, axl_factory)        # alias
        self.vpn_gateway = VpnGateway(self, axl_factory)
        self.vpn_group = VpnGroup(self, axl_factory)
        self.vpn_profile = VpnProfile(self, axl_factory)
        self.secure_config = SecureConfig(self, axl_factory)
        self.infrastructure_device = InfrastructureDevice(self, axl_factory)  

        # serviceability API wrappers
        self.billing_server = BillingServer(self, axl_factory)
        self.snmp_community_string = SNMPCommunityString(self, axl_factory)     # alias (schema name not used)
        self.snmp_user = SNMPUser(self, axl_factory)                            # alias (schema name not used)
        self.snmp_mib2_system_group = SNMPMIB2List(self, axl_factory)           # alias (schema name not used)
        self.syslog_configuration = SyslogConfiguration(self, axl_factory)
        self.process_node_service = ProcessNodeService(self, axl_factory)

    def get_ccm_version(self, processNodeName=None):
        axl_resp = self.service.getCCMVersion(processNodeName=processNodeName)
        return serialize_object(axl_resp)["return"]["componentVersion"]["version"]

    def get_os_version(self):
        axl_resp = self.service.getOSVersion()
        return serialize_object(axl_resp)["return"]["os"]