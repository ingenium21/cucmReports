"""Support Classes, may put this in _internal_utils

VendorClass is used by:
    enterprisePhoneConfig
    phone
    commonPhoneConfig

    
EnterprisePhoneConfig Defaults
    <webProtocol>0</webProtocol>
    <ice></ice>
    <instantMessaging></instantMessaging>
    <desktopClient></desktopClient>

STATUS:
    base is working but this has not gone through PYTEST testing yet.
    EnterprisePHoneConfig
        -GET
        -UPDATE
    CPP
        ADD
        -GET
        -UPDATE
    PHONE
        ADD
        -GET
        -UDPATE

    TODO: ALSO, determined that the DEPTH of the vendorConfig is not 1 ...it is multiple depths
    Need to update PATCH and parsing methods to ensure they can handle this.
    UPDATE/GET should be fine as is
    Then LOCAL_DEBUG lines should be removed and clean up       1/2024

"""

#from .base import SimpleAXLAPI
from ..sql_utils import get_device_pkid

from lxml import etree
import xmltodict 
import re
from collections import OrderedDict
import click  # delete me after initial testin gis done


# Experimental
class VendorConfig(object):
    """
    Utility class to handle vendorConfig element which is 
    formatted as an XML string without a root element.
    
    Zeep does not handle this object well when parsing and could hand back LXML elements.
    
    NOTE: Have attempted to correct the SOAP call by pre/post processing the LXML objects.
        This worked for the GET but not for the UPDATE on EnterprisePhoneConfig.
        So will be using sql/thin version and will revisit thick again in the future.
        Other code is still here because it is not yet abandonned.
        
        Use of sql/thin means some additional default entries will show in response.

    Public Methods:
        get_sql
        update_sql
        patch_sql   

    Phone:
        could have it's XML data held in one of 3 tables.  So access is controleld by stored
        proceddures of dbreaddevicexml and dbwritedevicexml. [See AXL FAQ on developer.cisco.com]
        Strangely, the dbwritedevicexml alwasy return 0 evn if it updates a line.
        
    Utilities for processing vendor_config
        _xml_string_to_dict
        _dict_to_xml_str

    TODO: Determined that the vendor config DOES have depth greater than 1 and the routines
        where written assuming a flat list of XML tags.  Need to update the PATCH items
        to support additional depth

    """
            
    def __init__(self, connector, factory_descriptor):
        #super().__init__(connector, object_factory)
        #self._get_model_name = "XEnterprisePhoneConfig"
        self.type = factory_descriptor       #enterprisephoen config, phone, commonphoneprofile
        self.connector = connector

    # UTILITY FUNCTIONS

    def _patch_dict(self, input_dict, key_name, value, delimiter='/'):
        """Utility function used by PATCH methods to add/update a variable into the vendorConfig.
        key_name could have delimiter in it to show path to place in dictionary to add/update
        
        :param input_dict:      starting dictionary
        :param key_name:        key to add/update
        :param value:           new value
        :param delimiter:       split for depth of dictionary path
        
        :return:                resulting dictionary
        """
        keys = key_name.split(delimiter)  # Splitting the key_name based on the delimiter
        
        current_dict = input_dict
        for key in keys[:-1]:
            if key not in current_dict:
                current_dict[key] = {}  # Creating a nested dictionary if the key doesn't exist
            current_dict = current_dict[key]  # Traversing the dictionary based on the path
        
        current_dict[keys[-1]] = value  # Adding/updating the value at the specified path
        
        return input_dict  # Returning the updated dictionary

    def _xml_str_to_dict(self, xml_string):
        # Parse the XML string using etree.XMLParser to handle XML with multiple levels of depth

        def _process_element(element):
            result = {}
            if element.text and element.text.strip():
                return element.text.strip()

            for child in element:
                result[child.tag] = _process_element(child)

            return result

        if xml_string is None:
            xml_string = ''
            
        root = etree.fromstring('<root>' + xml_string + '</root>')

        result_dict = {}
        for element in root:
            result_dict[element.tag] = _process_element(element)

        return result_dict

    def _dict_to_xml_str(self, vc):
        """ Utility to pre-process vendorConfig.

        If a dict/OrderedDict then format to an xml string

        :param vc:   string or dict of vendorConfig object (just the value without 'vendorConfig' as a key)        
        :return:     string formatted for xml
        """

        LOCAL_DEBUG = False

        if isinstance(vc, (dict, OrderedDict)):
            if LOCAL_DEBUG:
                print(f'TYPE OF VENDORCONFIG: {type(vc)}')

            # convert dict to XML string using xmltodict.  First add a root node (which we will later remove)
            #data = {'_temp_tag_' : vc['vendorConfig']}
            data = {'_temp_tag_' : vc}
            vc_xml = xmltodict.unparse(data, encoding='unicode')
            vc_xml = re.sub('<\?xml.*\?>', '', str(vc_xml))  # strip initial XML declaration
            vc_xml = re.sub('<_temp_tag_>', '', str(vc_xml))
            vc_xml = re.sub('</_temp_tag_>', '', str(vc_xml))
            vc_xml = re.sub('\n', '', str(vc_xml))
            #vc['vendorConfig'] = vc_xml
            vc = vc_xml
        else:
            # if already a string then don't process it
            pass
            if LOCAL_DEBUG:
                print('Already found a STRING - SKIP Processing')

        return vc

    # experimental for getting update to work without sql
    def _dict_to_lxml_elements(self, input_dict):
        elements_list = []  # List to store individual LXML elements
        
        for key, value in input_dict.items():
            # Creating an element with the key as the tag name and value as text
            element = etree.Element(key)
            element.text = str(value)
            elements_list.append(element)  # Appending the element to the list
    
        return elements_list  # Returning the list of independent LXML elements

    # experimental
    def _vc_to_dict(self, vc_data):
        """ Experimental Utility to post-process vendorConfig.  For THICK calls.
        Zeep fails to process the xml formated string within vendorConfig properly 
        becasue it is not in the wSDL.
        
        Zeep returns these elements still as LXML etree elements.  
        This routine continues to process the vendorConfig elements to a dict.
        If a LIST is not found, then it just passes teh dat athrough.

        :param vc_data:   recevies the value of vendorConfig
        :returns:   dict processed version of vendor Config 

        FUTURE: Should this also process a string of xml data to dict?
        """

        try:
            vc_dict = {}

            if isinstance(vc_data, list):   # process if list of elements
                for el in vc_data:
                    vc_dict[el.tag] = el.text

            return vc_dict

        except Exception as e:
        
            return vc_data

    # Public calls
        
    def get_sql(self, *args, **kwargs):
        """
        Utility method to get vendorConfig but using SQL
        This also returns the pkid so it can be used in a future sql query

        :param:     CHANGING - none needed for enterprisePhoneConfig
        :return:    dict with vendorConfig and pkid fields
        """

        LOCAL_DEBUG = False

        # still need some error chekcign on this.  Only used for CPC/Phone
        name = kwargs.get('name','')

        # TODO: possibly move these into init to keep code cleaner (except we don't have name yet.)
        if self.type == 'enterprise_phone_config':
            sql = 'select * from enterprisephoneconfigxml'

        elif self.type in ['common_phone_config','common_phone_profile']:
            sql = f'select x.pkid, x.xml from commonphoneconfigxml as x left outer join commonphoneconfig as c on x.fkcommonphoneconfig=c.pkid where c.name = "{name}" '
            #sql = f"select x.pkid from commonphoneconfigxml as x, commonphoneconfig as c where x.fkcommonphoneconfig=c.pkid and c.name='{name}'  "
        
        elif self.type in ['phone']:
            return self._get_phone_vendor_config(name)
            
        if LOCAL_DEBUG:
            print(f'SQL: {sql}')
        try:
            # force XML raw response for this call to bypass ZEEP processing
            with self.connector._client.settings(raw_response=True):
                r = self.connector.service.executeSQLQuery(sql=sql)
        except Exception as e:
            print(e)
            # Q: should we just let this get raised?
            # if error how do we want to respond?

        # TODO: still need a check to make sure only 1 entry was returned as an error check
            
        # strip namespaces from response
        namespaces = {'http://www.w3.org/2001/XMLSchema-instance' : None}
        
        if LOCAL_DEBUG:
            print('response')
            print(r.content)

        resp_dict = xmltodict.parse(r.content, namespaces=namespaces)  

        if LOCAL_DEBUG:
            print(f'get_{self.type}: RESP_DICT')
            print(resp_dict)

        vc = {}
        pkid = ''
        if r.status_code==200:
            try:
                if LOCAL_DEBUG:
                    print('SQL RESPONSE: ')
                    print(r.content)
                pkid = resp_dict['soapenv:Envelope']['soapenv:Body']['ns:executeSQLQueryResponse']['return']['row']['pkid']

                # changed 1/9 by jre - need to regression test this on other objects
                # TODO:TOFIX - the following line caused an exception when it was None rather than going to the next line.
                # I think the "dict()" is what caused the issue.  So we may have to GET it 
                vc = resp_dict['soapenv:Envelope']['soapenv:Body']['ns:executeSQLQueryResponse']['return']['row']['vendorConfig']
                if vc is None:
                    vc = {}
                else:
                    vc = dict(vc)
            except Exception:
                # TODO: Change this to an error which is raised
                print('ERROR: vendor_config line not found in SQL response.')
                return {'pkid': pkid,
                        'vendorConfig': vc}

        if LOCAL_DEBUG:
            print('get_enterprise_phone_configuration: vendorConfig')
            print(vc)
        
        # TODO: should this be standardized to an OrderedDict so it's a common type of response?
        return {'pkid' : pkid, 'vendorConfig': vc}

    def _get_phone_vendor_config(self, name):
        """Return a phone's vendor_config by using procedure  call to dbreaddevicexml
        
        :parm name:     name of phone to query
        :return:        wrapper dictionary with pkid of phone and vendorConfig as a dict
        """

        LOCAL_DEBUG = False

        # get pkid of device
        g = get_device_pkid(self.connector, name)
        pkid = g[0].get('pkid','')

        if LOCAL_DEBUG:
            print(g)
            print(pkid)
        
        # default return dictionary - assumed vendorConfig does not exist
        ret = {'pkid': pkid, 'vendorConfig': {}}

        # run stored procedure on pkid
        sql = f"execute procedure dbreaddevicexml('{pkid}')"
        u = self.connector.sql.query(sql)

        if LOCAL_DEBUG:
            print('RESPONSES FROM DB READ')
            print(u)
            print('LAST SENT XML')
            print(self.connector.history.last_sent_xml)
            print('LAST RECEIVED XML')
            print(self.connector.history.last_received_xml)


        # get xml string and return it as a dict
        vc_str = u[0].get('expression','')
        vc_dict = self._xml_str_to_dict(vc_str)

        if LOCAL_DEBUG:
            click.secho('READ XML STRING', fg='blue')
            print(vc_str)
            click.secho('READ vc DICT', fg='blue')
            print(vc_dict)
        
        ret['vendorConfig'] = vc_dict

        return ret

    def _update_phone_vendor_config(self, name, vc_xml):

        g = get_device_pkid(self.connector, name)
        pkid = g[0].get('pkid','')

        sql = f"execute procedure dbwritedevicexml('{pkid}','{vc_xml}'"

        r = self.connector.sql.update(sql)

        # TODO:  This is alwasy returning 0 so do we want to do a GET a gain to check it?
        # or just assume it always works and return 1

        return 1        # always returns 1 (not the best)


    # TODO: NEW PATCH REQUIREMENT
    #   turns out the XML string can be of multiple depths.  So the PATCH routine needs to handle
    #   parsing down in depth and has to allow a param to have a delimiter for depth (like /)
    # ALL patch mechanisms need this updated.

    def patch_phone_vendor_config(self, name, param, value):
        """
        You can NOT do this by updating the tables directly.  you MUST use dbreaddevicexml and dbwritedevicexml
        because the database does not allow anyone to write to these tables.

        The DBREAD works simply, but the DBWRITE appears to always show "0 rows updated" whether it works
        or not.  So you have to run another DBREAD if you want to confirm that the write worked.

        LOGs are at - file tail activelog /tomcat/logs/axl/log4j/axl######.log

        FINDINGS: The dbwrite method is always returning 0 even if it succeeds.  This code is working
        but you can't confirm it works unless you run another dbread to check it.   UGH!!
        """
        LOCAL_DEBUG = False

        g = self._get_phone_vendor_config(name)

        if LOCAL_DEBUG:
            print('UPDATE_PHONE_VENDOR_CONFIG: Just called Get_phone_vendor_config and returned')
            print(g)

        if g['vendorConfig'] is None:           #confirm we have a dictionary
            g['vendorConfig'] = {}
        
        # add/udpate parameter  in 
        updated_vc = self._patch_dict(g['vendorConfig'], param, value)
        #g['vendorConfig'][param] = value        # add or update the item passed (syntax is NOT checked)

        if LOCAL_DEBUG:
            print(f'New Settings:')
            print(updated_vc)
        
        # convert dict to XML string using xmltodict.  First add a root node (which we will later remove)
        data = {'data' : updated_vc}
        v_xml = xmltodict.unparse(data, encoding='unicode')
        v_xml = re.sub('<\?xml.*\?>\n', '', str(v_xml))  # strip initial XML declaration
        v_xml = re.sub('<data>', '', str(v_xml))
        v_xml = re.sub('</data>', '', str(v_xml))
        
        if LOCAL_DEBUG:
            print('\n\nTRYING DB WRITE')

        sql = "execute procedure dbwritedevicexml('" + g['pkid'] + "','"  + str(v_xml) + "')"

        if LOCAL_DEBUG: 
            print ('\n\n')
            print('v_xml')
            print(v_xml)
            print(f'Sql update: {sql}')
            print ('\n\n')
        
        u = self.connector.sql.update(sql)

        if LOCAL_DEBUG:
            print(u)
            print('LAST SENT')
            print(self.connector.history.last_sent_xml)
            print('LAST RECEIVED')
            print(self.connector.history.last_received_xml)

        return u

    def update_sql(self, vc_data, pkid=''): 
        """ 
        Utility function to update vendor config entirely.  Previous method has performed a GET to 
        pass the pkid of the object in question.
        
        # KEY: doing things by SQL show additional optonis that you don't see using get/update
        # Not sure if that is a good reason to NOT do SQL and try to get this working on GET/UDPATE instead.
        # table to update will be determined by self.type

        :param vc_data: STRING or DICT for XML
        :parma pkid:    pkid of line to be updated 
        :return:        returns 1 for proper update (since this is a sql update)
        """

        # get existing vendor_config parameters as a parsed dict
        # for update this just needs PKID
        #r = self.get_sql()

        if pkid == '':
            print('ERROR: no pkid passed to update_sql')
            return 0
    
        if isinstance(vc_data, str):
            # is a string
            # perform check for open tag, if found then proceed
            vc_xml = vc_data
        
        if isinstance(vc_data, (dict,OrderedDict)):
            # convert dict to XML string using xmltodict.  First add a root node (which we will later remove)
            data = {'_temp_tag_' : vc_data}
            vc_xml = xmltodict.unparse(data, encoding='unicode')
            vc_xml = re.sub('<\?xml.*\?>', '', str(vc_xml))  # strip initial XML declaration
            vc_xml = re.sub('<_temp_tag_>', '', str(vc_xml))
            vc_xml = re.sub('</_temp_tag_>', '', str(vc_xml))
            vc_xml = re.sub('\n', '', str(vc_xml))

        # Q: do we need any other checks for characters like ' " to prevent sql injection issues?

        # pkid passed in is already specific to the table
        if self.type == 'enterprise_phone_config':
            sql = "update enterprisephoneconfigxml set xml='" + str(vc_xml) + "' where pkid='" + str(pkid) + "' "
        elif self.type in ['common_phone_config', 'common_phone_profile']:
            sql = "update commonphoneconfigxml set xml='" + str(vc_xml) + "' where pkid='" + str(pkid) + "' "
        elif self.type in ['phone']:
            return self._update_phone_vendor_config()

        # Q: Do we need a check to confirm that vc_xml is populated?
        # update by SQL query
        r = self.connector.sql.update(sql)

        return r

    # JRE Added utlity
    # Still experimental - working but needs testing
    def patch(self, param, value, name=''):     
        """ 
        Utility function to update a "single parameter" within the vendorConfig rather than 
        replacing the entire value.

        NOTE: There is no error checking to validate that "param" is a valid entry
        TODO: Need to handle a parameter that is multiple depth by using a delimiter (/)

        :param: parameter string within vendorConfig to be edited (case sensitive)
        :value: value to apply to the single parameter
        :parm name: ignored for EnterprisePhoneConfig. Used by CPC and Phone to locate item

        :return: 0 on failure, 1 if successful from the sql update method
        """

        # get existing vendor_config parameters as a parsed dict
        # type is controlled during __init__.  'name' is ignored for enterprisephoneconfig;
        r = self.get_sql(name=name)

        pkid = r.get('pkid', None)
        if pkid is None:
            # item not found - return an error
            return 0

        vc = r.get('vendorConfig', None)
        if vc is None:           #confirm we have a dictionary
            vc = {}

        # TODO: this add needs to parse for the delimiter and add the element at whatever
        # depth is required.  Parent dicts should be created alone the way
        vc[param] = value        # add or update the item passed (syntax is NOT checked)

        u = self.update_sql(vc, pkid)

        return u


