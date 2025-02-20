"""CUCM AXL User APIs."""

from collections import defaultdict

from zeep.helpers import serialize_object

from .._internal_utils import flatten_signature_kwargs
from .base import SimpleAXLAPI
from copy import deepcopy

import logging

# TODO: UserRank settings not fully deployed

# Experiementally adding user_role
# IN PROCESS NOW
class AppUser(SimpleAXLAPI):
    _factory_descriptor = "application_user"

    def add(self, userid, associatedDevices=None, associatedGroups=None, ctiControlledDeviceProfiles=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    def _minimum_add_fields(self, **kwargs):
        """Experimental method to return only the mandatory fields for an add"""
        mandatory_fields = ['name']

        minimum_fields = {}
        for field in minimum_fields:
            minimum_fields[field] = kwargs.get(field, None)

        return minimum_fields

    def _update_rank(self, name, user_rank):
        """Experimental user_rank update routine"""
 
        sql = f"update applicationuser set userrank = '{user_rank}' where name='{name}'"
        return self.connector.sql.update(sql)

    def _get_rank(self, name):
        """Experiemental user-rank get routine"""

        sql = f"select userrank from applicationuser where name='{name}'"
        s = self.connector.sql.query(sql)

        try:
            user_rank = s[0].get('userrank','')
        except Exception as e:
            user_rank = ''

        return user_rank

    def add_update(self, obj_data):
        #unique add_update required in order to get userRank entry past filtering

        # if user ranks exists, then perform deepcopy for changes
        user_rank = obj_data.get('userRank', None)
        if user_rank is not None:
            obj_data = deepcopy(obj_data)
            user_rank = obj_data.pop('userRank', '')

        au = super().add_update(obj_data)

        if user_rank is not None:
            name = obj_data.get('name','')
            if name != '':
                u = self._update_rank(name, user_rank)
            
        return au


class ApplicationUserCapfProfile(SimpleAXLAPI):
    _factory_descriptor = "application_user_capf_profile"

    def add(self, applicationUser, instanceId, certificateOperation="No Pending Operation",
            authenticationMode="By Null String", keySize=2014, keyOrder="RSA Only", ecKeySize=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# JRE Added - not fully tested yet
class CredentialPolicy(SimpleAXLAPI):
    _factory_descriptor = "credential_policy"

    def add(self, name, failedLogon=3, resetFailedLogonAttempts=30, lockoutDuration=30, credChangeDuration=0,
            credExpiresAfter=180, minCredLength=8, prevCredStoredNum=12, inactiveDaysAllowed=0, 
            expiryWarningDays=0, trivialCredCheck=True, minCharsToChange=1, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


# JRE Added - experimental - initial test working but NOT fully tested yet
# updating GET/UPDATE and adding a LIST capability not in WSDL
class CredentialPolicyDefault(SimpleAXLAPI):
    _factory_descriptor = "credential_policy_default"
    supported_methods = ['get', 'update', 'list', "model"]       # added items not in API

    """
    This class was implemented by Cisco oddly (imho).  It treats the current policy name as a required field rather than
    as an optional attribute.  This is odd because type/user are what determines the 3 possible values and not the name
    that is currently applied.   So if you wanted to find out which policy is applied, you would already need to know
    this in order to GET that information
    In our opinion, all that should be required is credentialType and credentialUser.  Consequently, we have written
    a helper methods to grab the current credential policy name and insert it into each requests.  It will also assume
    that any entry in credPolicyName is intended to be in newCredPolicyName when performing an update (as long as 
    newCredPolicyName field is blank/None).

    Mandatory Choice fields become:
        credentialUser:                                 # Application User / End User
        credentialType:                                 # PIN / Password
        credPolicyName: NEEDS_TO_HAVE_CURRENT_VALUE
        newCredPolicyName: NEW_NAME                     # this can be left blank and will be populated by the update routine
    """    

    def update(self, **kwargs):

        LOCAL_DEBUG = False

        # Question: Is a deepcopy required for this step?

        # Perform lookup of current credential (regardless of what was in credPolicyName request)
        # then update it and newCredPolicyName
        credential_type = kwargs.get('credentialType','')
        credential_user = kwargs.get('credentialUser','')
        if credential_type != '' and credential_user != '':

            # if newCredPolicyName is not populated, assume it should be replaced with credPolicyName
            if (kwargs.get('newCredPolicyName', None) is None) or (kwargs.get('newCredPolicyName', None) == ''):
                kwargs['newCredPolicyName'] = kwargs.get('credPolicyName','')

            # udpate credPolicyName with current name
            found_cred_policy_name = self._get_current_policy_name(credential_type, credential_user)

            if LOCAL_DEBUG:
                print(found_cred_policy_name)

            kwargs['credPolicyName'] = found_cred_policy_name    

        update_kwargs = flatten_signature_kwargs(self.update, locals())

        if LOCAL_DEBUG:
            print('----STARTING UPDATE')
            print(update_kwargs)
            print('----Calling SUPER().UPDATE()')

        # TODO: after testing, remove try and let error be raised
        try:
            u = super().update(**update_kwargs)
        except Exception as e:
            print(e)
            print('error')

        if LOCAL_DEBUG:
            print(('----update returned'))
            print(u)
            print(('----leaving update'))

        return u

    def _get_current_policy_name(self, credential_type, credential_user):
        """Find current policy name
        
        :param credential_type:     'PIN' 'Password'
        :param credential_user:     'Application User' / 'End User'
        :return:        name of current credential policy
        """
        LOCAL_DEBUG = False

        assert(credential_type in ['PIN', 'Password'])
        assert(credential_user in ['Application User', 'End User'])

        sql = ('SELECT cp.displayname '
               ' FROM credentialpolicydefault as cpd left outer join credentialpolicy as cp on cpd.fkcredentialpolicy=cp.pkid, '
               ' typecredential as tc, typecredentialuser as tcu '
               ' WHERE cpd.tkcredential=tc.enum and cpd.tkcredentialuser=tcu.enum '
               f' and tc.name="{credential_type}" and tcu.name="{credential_user}"')
        
        s = self.connector.sql.query(sql)      

        if LOCAL_DEBUG:
            print(s)

        try:
            cred_policy_name = s[0].get('displayname', '')
        except Exception as e:
            cred_policy_name = ''

        return cred_policy_name

    def get(self, **kwargs):

        LOCAL_DEBUG = False

        # run sql query using credentialUser (E'nd User'|'Application User') and credentialType ('Password' | 'PIN')
        # populate kwargs with value and then run get
        credential_type = kwargs.get('credentialType','')
        credential_user = kwargs.get('credentialUser','')

        if LOCAL_DEBUG:
            print(kwargs)
            print('FOUND type and user')

        if credential_type != '' and credential_user != '':
            cred_policy_name = self._get_current_policy_name(credential_type, credential_user)
            kwargs['credPolicyName'] = cred_policy_name

        if LOCAL_DEBUG:
            print(kwargs)

        return super().get(**kwargs)

    def list(self, **kwargs):
        """
        Utility method (not in typical API) to list all 3 default credential policies
        Any search criteria or returnedTags are ignored
        """

        LOCAL_DEBUG = False

        sql = ('SELECT typecredentialuser.name as credentialuser, typecredential.name as credentialtype, '
               ' cp.displayname as credpolicyname, cpd.cantchange as credusercantchange, '
               ' cpd.credmustchange credusermustchange, cpd.doesntexpire as creddoesnotexpire '
               ' FROM credentialpolicydefault as '
               ' cpd left outer join credentialpolicy as cp on cpd.fkcredentialpolicy=cp.pkid, '
               ' typecredential, typecredentialuser '
               ' WHERE cpd.tkcredential=typecredential.enum and cpd.tkcredentialuser=typecredentialuser.enum')

        s = self.connector.sql.query(sql)      

        if LOCAL_DEBUG:
            print("S BEFORE")
            print(s)

        # unfortunately, can't get SQL to return camelcase so must transform
        field_name_list = ['credentialUser', 'credentialType', 'credPolicyName', 'credUserCantChange', 'credUserMustChange', 'credDoesNotExpire']
        for row in s:
            for field in field_name_list:
                v = row.pop(field.lower(), None)
                if v is not None:
                    row[field] = v

        if LOCAL_DEBUG:
            print("S AFTER")
            print(s)
        
        # now format S and return it as a dict.
        return s


class EndUserCapfProfile(SimpleAXLAPI):
    _factory_descriptor = "end_user_capf_profile"

    def add(self, endUserId, instanceId, certificateOperation="No Pending Operation",
            authenticationMode="By Null String", keySize=2014, keyOrder="RSA Only", ecKeySize=None, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class FeatureGroupTemplate(SimpleAXLAPI):
    _factory_descriptor = "feature_group_template"

    def add(self, name, serviceProfile=None, userProfile=None, homeCluster=True, imAndUcPresenceEnable=True,
            meetingInformation=True, allowCTIControl=True, BLFPresenceGp="Standard Presence group", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

# JRE TODO: Add a get utility
class SelfProvisioning(SimpleAXLAPI):
    _factory_descriptor = "self_provisioning"
    supported_methods = ["update", "model"]

    def update(self, requireAuthentication=False, allowAuthentication=False, authenticationCode=None,
               ctiRoutePoint=None, applicationUser=None, **kwargs):
        update_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().update(**update_kwargs)


class ServiceProfile(SimpleAXLAPI):
    _factory_descriptor = "service_profile"

    def add(self, name, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class SipRealm(SimpleAXLAPI):
    _factory_descriptor = "sip_realm"

    def add(self, realm, userid, digestCredentials,
            **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class UcService(SimpleAXLAPI):
    _factory_descriptor = "uc_service"

    def add(self, name, serviceType, hostnameorip, productType=None, **kwargs):
        product_types = defaultdict(
            lambda: None,
            Voicemail="Unity Connection",
            CTI="CTI",
            MailStore="Exchange",
            Conferencing="WebEx (Conferencing)",
            Directory="Directory"
        )
        # whitespace won't work with defaultdict, so if statements for the rest
        if not productType:
            if serviceType == "IM and Presence":
                productType = "Unified CM (IM and Presence)"
            elif serviceType == "Video Conference Scheduling Portal":
                productType = "	Telepresence Management System"
            else:
                productType = product_types[serviceType]
        protocols = defaultdict(
            lambda: None,
            CTI="TCP",
            Voicemail="HTTPS"
        )
        if "protocol" not in kwargs:
            kwargs["protocol"] = protocols[serviceType]
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


class User(SimpleAXLAPI):
    _factory_descriptor = "user"
    supported_methods = ["model", "create", "add", "get", "update", "list", "remove", "add_update", "change_dnd_status"]

    # NOTE: User rank implemented for addUpdate only.  Not implemented for other operations yet to keep them standard
    
    add_update_base_defaults = {
                     #'userid':'',
                     #'lastName': '',
                     'presenceGroupName':'Standard Presence Group'}

    def add(self, userid, lastName='', presenceGroupName="Standard Presence group", **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)

    def change_dnd_status(self, userID=None, uuid=None, dndStatus=False):
        """Change Do Not Disturb status for user

        :param userID: (str) userid
        :param uuid: user uuid
        :param dndStatus: (bool) user's do not disturb status
        :return: (str) user pkid
        """
        if uuid:
            axl_resp = self.connector.service.doChangeDNDStatus(uuid=uuid, dndStatus=dndStatus)
        else:
            axl_resp = self.connector.service.doChangeDNDStatus(userID=userID, dndStatus=dndStatus)
        return serialize_object(axl_resp)["return"]

    def _minimum_add_fields(self, **kwargs):
        """Experimental method to return only the mandatory fields for an add"""
        mandatory_fields = ['userid', 'lastName', 'presenceGroupName']

        minimum_fields = {}
        for field in minimum_fields:
            minimum_fields[field] = kwargs.get(field, None)

        return minimum_fields

    def _update_rank(self, userid, user_rank):
        """Experimental user_rank update routine"""

        sql = f"update enduser set userrank = '{user_rank}' where userid='{userid}'"
            
        return self.connector.sql.update(sql)
    
    def _get_rank(self, userid):
        """Experiemental user-rank get routine"""

        sql = f"select userrank from enduser where userid='{userid}'"
        s = self.connector.sql.query(sql)

        try:
            user_rank = s[0].get('userrank','')
        except Exception as e:
            user_rank = ''

        return user_rank

    def add_update(self, obj_data):
        #unique add_update required in order to get userRank entry past filtering

        # if user ranks exists, then perform deepcopy for changes
        user_rank = obj_data.get('userRank', None)
        if user_rank is not None:
            obj_data = deepcopy(obj_data)
            user_rank = obj_data.pop('userRank', '')

        au = super().add_update(obj_data)

        if user_rank is not None:
            userid = obj_data.get('userid','')
            if userid != '':
                u = self._update_rank(userid, user_rank)
            
        return au


class UserGroup(SimpleAXLAPI):
    """Access Control Groups API"""
    """Experimental: Adding userRank capabilities to this class.
    It is ONLY being added to the ADD_UDPATE and GET methods at this time. 
    The issue is the POP can often affect the calling object so a deepcopy
    is required.   I'm not certain I want to put this into the 
    standard add and update methods.
    # also testing on ldapDirectory   - once these 2 are done then update Enduser and AppUser
    Full testing still to be done for errors.  add_udpate is getting tested by
    ucmprovisioning tool but need to write pytest scripts for standalone add and update
    NOTE: This deepcopy may be an expensive operation.  
            Need to speedtest this before doing Enduser/AppUser
    """
    _factory_descriptor = "user_group"

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

    def _update_rank(self, user_group_name, minimum_user_rank):
        """Experimental user_rank update routine"""
        # failures will be raised but original operation (add /update) will have succeeded
        # TODO: add error checking to prevent against sql injection
 
        LOCAL_DEBUG = False

        sql = f"update dirgroup set minimumuserrank='{minimum_user_rank}' where name='{user_group_name}' "
        r = self.connector.sql.update(sql)

        if LOCAL_DEBUG:
            if str(r) == '1':
                print('userRank updated')
            else:
                print(f'ERROR: udating userRank for {user_group_name}')
        
        return r

    def _get_rank(self, user_group_name):
        """Experiemental user-rank get routine"""

        sql = f"select minimumuserrank from dirgroup where name='{user_group_name}'"
        s = self.connector.sql.query(sql)

        try:
            user_rank = s[0].get('minimumuserrank','')
        except Exception as e:
            user_rank = ''

        return user_rank


class UserProfileProvision(SimpleAXLAPI):
    _factory_descriptor = "user_profile"

    def add(self, name, profile=None, deskPhones=None, mobileDevices=None, defaultUserProfile=None,
            universalLineTemplate=None, allowProvision=False, **kwargs):
        add_kwargs = flatten_signature_kwargs(self.add, locals())
        return super().add(**add_kwargs)


#
# #########################################################################
# ADD On Objects Below
#
# userRole
# userRank
#
#   NOTE: UserRank attribute updates needed for objects
#       user_group (ACG - initial build completed - testing ongoing)
#       ldap_directory ()
#       user (end user)  [NOT DONE - waiting for user_group and ldap_direcotry to work]
#       app_user
#       
    
# Add-On Experimental - Not part of WSDL API
class UserRole(SimpleAXLAPI):
    _factory_descriptor = "user_role"
    supported_methods = ['list', 'get', 'add', 'update', 'remove', 'add_update']
    _utilities = ['_add_all_permissions','_delete_all_permissions', '_update_permissions']

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)

    def _fetch_add_model(self):
        return {'name', 'description', 'permissions'}

    def _fetch_update_method(self):
        return {'name', 'newName', 'description', 'permissions'}

    def _fetch_get_model(self):
        return {'name'}

    def _fetch_get_method(self):
        return {'name'}

    """
    Format for userRole object (all made up):
        userRole:  
            name: Tier3_AdminSupport
            #newName:
            description: Tier3 Help Desk Access
            permissions: {520: 2, 100: 3}               # k:v pair is tkresource: permission
            applicationName: field not used,  can fill in for reference if you want
        Future Idea for permissions:
            permissions:
                - resourceName:
                  resourceNumber:               # this is the tkresource
                  permission:                   # still 1 2 3

    Permissions use 2-bit field:
        1 = read
        2 = update
        3 = read + update
        0 = no rights (or can delete line)   TODO: find out if 0 is set will garbage collection remove it
    Resource numbers can be generated by running query:
        run sql select * from TypeResource
    Valid application names can be generated by running query:
        run sql select * from TypeApplication

    ISSUE: Informix does not support multiple rows of values for an INSERT/UPDATE - so this guy is SLOOOOOOOW for an INSERT
        Each permission takes it's own SQL query with associated IO wait time
        Will greatly benefit from ASYNC module.
        Delete can be done in single run so that's quick
        Consequently, after _update_permissions is done, should check to see which is more efficient statistically.
            The processing overhead in UPDATE may be worth it if it reduces the number of IO calls that are made.
    
    NOTE: fetch_choices and self.model() will fail on this object.  have put in a temp fix in axlmethods - listget() already to
        make that work.  Need to look at a long-term solution that works across multiple custom objects taht are not in WSDL

    # NOTE: You are allowed to INSERT resources from 2 different applications it makes duplicate 
    #   entires in CCMAdmn (this is normal for AXL).  But the CCMADmin interface can't do this.
    #   Although, you will notice that Cisco HAS done this for many of their standard roles.
    #   In CCMAdmin you can only select one app.  And once "app" is associated you can't delete
    #   it from CCMAdmin...
    #   Deleting/updating a role in CCMADMIN will delete/update the "entire role" even if it is associated to
    #   multiple applications (showing that they are actualy linked in the tables)
    #   This can be shown by updating a "description" and seeing it change on multiple role items
    """

    def list(self, **kwargs):
        # initial working - needs testing
        
        sql = ("select f.pkid, f.name, f.description, f.isstandard, map.tkresource, map.permission "
               " from functionroleresourcemap as map, functionrole as f where map.fkfunctionrole=f.pkid")
        # TODO: should we add in typeresource.name in this output for completeness
        # TODO: add filters for "isstandard" in search
        try:
            r=self.connector.sql.query(sql)
        except Exception as e:
            print(e)
            r=[]        # return empty list if error

        result = []
        this_item = {}

        # now merge output together for permissions
        if r != []:
            for count, row in enumerate(r):
                if count == 0:
                    # first item - setup loop
                    current_name = row['name']
                    current_description = row['description']
                    is_standard = row['isstandard']
                    permissions = {row['tkresource']: row['permission']}
    
                elif row['name'] == current_name:
                    # same row - append permissions
                    permissions[row['tkresource']] = row['permission']
    
                else:
                    # write new role to output
                    this_item = {'name': current_name,
                                'description': current_description,
                                'isStandard': is_standard,
                                'permissions': permissions
                    }
                    result.append(this_item)
                    
                    # reset for next item
                    this_item = {}
                    current_name = row['name']
                    permissions = {row['tkresource']: row['permission']}

            # leaving loop - finalize last item
            this_item = {'name': current_name,
                        'description': current_description,
                        'isStandard': is_standard,
                        'permissions': permissions
            }
            result.append(this_item)
        
        return result
    
    def get(self, **kwargs):
        # utility function to return a dictionary of current resources (just prints now)
        # initial working - needs testing
        
        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print('user_role.get KWARGS received:')
            print(kwargs)
        name = kwargs.get('name', None)
        if name is None or name=='':
            return 'missing name'
        
        sql = ("select f.pkid, f.name, f.description, f.isstandard, map.tkresource, map.permission "
               " from functionroleresourcemap as map, functionrole as f "
               f" where map.fkfunctionrole=f.pkid and f.name='{name}'")

        try:
            r=self.connector.sql.query(sql)
        except:
            pass

        if LOCAL_DEBUG:
            print('SQL query returned:')
            print(r)

        # handle case of not found
        if len(r) == 0:
            return {}

        this_item = {}

        # TODO: need to confirm we only get 1 entry back (maybe keep the RESULT stuff and check length afterwards)
        # now merge output together for permissions
        for count, row in enumerate(r):
            if count == 0:
                # first item - setup loop
                current_name = row['name']
                current_description = row['description']
                is_standard = row['isstandard']
                permissions = {row['tkresource']: row['permission']}

            elif row['name'] == current_name:
                # same row - append permissions
                permissions[row['tkresource']] = row['permission']

            else:
                # write new role to output
                this_item = {'name': current_name,
                            'description': current_description,
                            'isStandard': is_standard,
                            'permissions': permissions
                }

                # reset for next item
                this_item = {}
                current_name = row['name']
                permissions = {row['tkresource']: row['permission']}

        # leaving loop - finalize last item
        this_item = {'name': current_name,
                    'description': current_description,
                    'isStandard': is_standard,
                    'permissions': permissions
        }
        
        return this_item

    def add(self, userRole):
        """
        query to make sure it doesn't exist already
        run an update to add name/description
        technically, gui requires a minimum of 1 application applied but doing this through SQL allows this to not happen
        there is NO place where you assign the "application type".  Instead this happens by the permission associations
        TODO: determine how fields will be passed.  Are we receiving one "userRole" object or like an update with **userrole
        """
        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print(userRole)
        
        new_pkid = ''
        # confirm it doesn't exist yet (needed in case of clutter)
        name = userRole.get('name', '')
        description = userRole.get('description', '')     # SQL INJECTION CHECK NEEDED
        permissions = userRole.get('permissions', {})

        if name is None or name == '':
            return 'ERROR: mising required field (name)'
        
        sql_select = f"select pkid from functionrole where name='{name}'"
        try:
            r = self.connector.sql.query(sql_select)
        except:
            pass

        if r != []:
            return 'ERROR: already exists (give pkid)'
        
        sql = f"insert into functionrole (name, description) values ('{name}','{description}')"

        if LOCAL_DEBUG:
            print(sql)

        try:
            r = self.connector.sql.update(sql)

            if LOCAL_DEBUG:
                print('INSERT for userRole returned')
                print(r)

            if int(r) == 1:
                add_successful = True

        except Exception as e:
            add_successful = False
            if LOCAL_DEBUG:
                print(e)
            return e        # TODO: sync up what is returned (error or blank pkid)
        
        if add_successful:
            # not update permission 
            sql_get = f'select pkid from functionrole where name="{name}"'
            r_get = self.connector.sql.query(sql_get)
            pkid = r_get[0].get('pkid','')
            if LOCAL_DEBUG:
                print(f'pkid for new role: {pkid}')
            for k, v in permissions.items():
                if LOCAL_DEBUG:
                    print(f'{k} / {v}')

            # if 1, then proceed with updating permissions by calling helper method
            # then get the pkid
            assert isinstance(permissions, dict)
            # TODO: change this to _add_all_permissions
            # u = self._update_resource_permissions(role_name=name, permissions=permissions)
            u = self._add_all_permissions(role_name=name, role_pkid=pkid, permissions=permissions)
            if LOCAL_DEBUG:
                print(f'Response from _update_resource_permissions: {u}')
            # TODO: not doing anything with u yet
            new_pkid = pkid
        else:
            new_pkid = ''   # ERROR: return pkid as blank

        return new_pkid

    # NOT FULLY TESTED YET
    def update(self, name=None, newName=None, description=None, permissions=None, **kwargs):
        """
        query to make sure it doesn't exist already
        run an update to add name/description
        technically, gui requires a minimum of 1 application applied but doing this through SQL allows this to not happen
        there is NO place where you assign the "application type".  Instead this happens by the permission associations
        TODO: determine how fields will be passed.  Are we receiving one "userRole" object or like an update with **userrole
        """

        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print('user_role.update KWARGS received')
            print(kwargs)
        
        if name is None or name == '':
            raise 'ERROR: No name provided'
        
        # TODO: change this query to have ALL mappings for the name
        # if 0 rows then it doesn't exist
        #
        sql_select = ("SELECT fr.pkid, fr.name, fr.description, frrm.pkid, frrm.tkresource, frrm.permission as permission "
                      " FROM FunctionRole as fr left outer join functionRoleResourceMap as frrm on fr.pkid=frrm.fkfunctionrole "
                      f" where fr.name='{name}' ")
        sql_select = f"select pkid, name, description from functionrole where name='{name}'"
        
        try:
            r = self.connector.sql.query(sql_select)
        except:
            pass
            # TODO: add in error checking or return error

        pkid = r[0].get('pkid','')  # get PKID of role for returning

        if LOCAL_DEBUG:
            print(r)

        if len(r) == 0:
            raise 'ERROR: single item not returned from sql query'

        # at this point, r has the current settings
        # now compare the two

        # do FunctionGroup fields need updating?
        if newName is not None or description is not None:
            if LOCAL_DEBUG:
                print('KEY: name/description MAY need updating')

            if newName is not None and newName != '':
                new_name = newName
            else:
                new_name = name

            if description is not None:
                new_description = description
            else:
                new_description = r[0].get('description','')

            sql_update = f"update functionrole set (name,description)=('{new_name}','{new_description}') where pkid='{pkid}'"
            try:
                uf = self.connector.sql.update(sql_update)
            except Exception as e:
                print(e)
            # TODO: add on any error checks

        # role updated - now update the permission mappings
        # TODO: this should call _update_permissions or some other submethod for permission mappings
        if False:
            x = self._update_resource_permissions(name, permissions)
            # need to error check x after permissions update

        if True:
            d = self._delete_all_permissions(name)
            a = self._add_all_permissions(role_name=name, role_pkid=pkid, permissions=permissions)
        return pkid

    def remove(self, name):
        # NOT WORKING YET
        """
        delete role from functionrole table
        delete all entries in functionroleresourcemap
        delete all entries in functionrolemembermap
        QUESTION: if you delete a role without deleteing it's members/resources what happens?  Do they get garbage collected?
        Q; what protects against dependency references?
        """

        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print(f'name: {name}')
        # perform a get first to confirm it exists
        sql_get = f'select pkid from functionrole as f where f.name="{name}" '

        pkid = None
        try:
            r = self.connector.sql.query(sql_get)
            pkid = r[0].get('pkid',None)
        except:
            pass
    
        if LOCAL_DEBUG:
            print('response from GET:')
            print(r)
            if pkid is None:
                print("pkid is none")
            else:
                print(f"pkid: {pkid}")
        
        # should be a list or orderedDict
        try:
            if r[0].get('pkid', None) is not None:
                if LOCAL_DEBUG:
                    print('FOUND PKID...PROCEED WITH DELETE of UserRole.')
                # confirm it comes back with a pkid
                sql_delete_all_resources = f"delete from functionroleresourcemap where fkfunctionrole=(select pkid from functionrole as f where f.name='{name}')"
                # delete all members (to write)
                sql_delete_role = f'delete from functionrole where name="{name}"'

                try:
                    if LOCAL_DEBUG:
                        print(f'sql query: {sql_delete_role}')
                    r = self.connector.sql.update(sql_delete_role)
                    if LOCAL_DEBUG:
                        print(f'Return from DELETE of role is: {r}')
                except Exception as e:
                    print(e)


        except:
            print(f'userRole with name {name} not found.')
        return      # should return pkid formatted as a uuid

    def add_update(self, userRole):
        """
        WORKING
        1) query to see if role exists in functionrole
        2) add or update accordingly
        should follow this with AT LEAST ONE PERMISSION to get the application type assigned
        not certain what the interface would do if 

        NOTE: application is NOT set here.  It is set when the first resource/permission is added to the mapping table
        NOTE: if you accidentally add resources from 2 types of apps, the system takes the first it finds and ignores the
        others.  Which means you could get weird behavior....so don't do that.
        """
        LOCAL_DEBUG = False

        name = userRole.get('name','')

        sql_select = f"select pkid from functionrole where name='{name}'"

        r = self.connector.sql.query(sql_select)

        if LOCAL_DEBUG:
            print(r)

        if len(r) == 1:
            # found so run update
            r = self.update(**userRole)
        else:
            # perform add
            r = self.add(userRole)

        if LOCAL_DEBUG:
            print(r)

        return r

    def add_update2(self, data):
        
        default_obj_data = {}
        obj_data = dict(default_obj_data)
        obj_data.update(**data)
        
        try:
            r = self.get(name=data['name'])
        #except zeep.exceptions.Fault:
        except:
            obj_data.pop('newName', None)
            r = self.add(userRole=obj_data)
        else:
            obj_data.pop('phoneType', None)
            r = self.update(**data)
        
        return r['return']

    # #####################
    # UserRole permission routines
    #
    #    delete all permissions
    #    add all permissions (assuming none exist - delete was just called or it's an add)
    #    update each permission (can update/insert/delete)   [a delete occurs if you set permissions to 0]
    #        this is a patch and doesn't touch everything
    
    def _delete_all_permissions(self, role_name, application_name=''):
        """Delete all resource/permision mappings for a role.
        
        :param role_name:   name of role
        :application_name:  name of application to remove if more than one.  If blank then all 
                            are removed.
        :return:            Count of mappings removed
        """
        # do we need to do something if role_name does not exist?  Or just stick with returning 0?

        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print('starting update resource permissions')
        # return role pkid with all mappings
        # if 0 rows, then role_name is bad.
        # if 1 row, then role_name exists
        if application_name == '':
            sql_get = ("select f.pkid as role_pkid, map.pkid, map.permission, map.tkresource "
                       " from functionrole as f left outer join functionroleresourcemap as map on f.pkid=map.fkfunctionrole "
                       f" where f.name='{role_name}'")
        else:
            sql_get = ("select f.pkid as role_pkid, map.pkid, map.permission, map.tkresource "
                       " from functionrole as f left outer join functionroleresourcemap as map on f.pkid=map.fkfunctionrole "
                       " left outer join TypeResource as tr on map.tkresource=tr.enum "
                       " left outer join TypeApplication as ta on tr.tkapplication=ta.enum "
                       f" where f.name='{role_name}' and ta.name='{application_name}'")
        try:
            r = self.connector.sql.query(sql_get)
        except Exception as e:
            print(e)

        if LOCAL_DEBUG:
            print('select query returned:')
            print(type(r))
            print(r)
        
        if application_name == '':
            sql_delete_all_resources = ("delete from functionroleresourcemap "
                                        " where fkfunctionrole=(select pkid from functionrole as f where f.name='{role_name}')")
        else:
            sql_delete_all_resources = ("delete from functionroleresourcemap "
                                        " where fkfunctionrole=(select pkid from functionrole as f where f.name='{role_name}')")
            sql_delete_all_resources = ("delete from functionroleresourcemap "
                                        f" where fkfunctionrole=(select pkid from functionrole as f where f.name='{role_name}') "
                                        " and (select ta.name from functionrole as f left outer join functionroleresourcemap as map on f.pkid=map.fkfunctionrole "
                                        " left outer join TypeResource as tr on map.tkresource=tr.enum "
                                        " left outer join TypeApplication as ta on tr.tkapplication=ta.enum "
                                        f" where f.name='{role_name}' and ta.name='{application_name}')")
                
        try:
            if LOCAL_DEBUG:
                print(f'sql query: {sql_delete_all_resources}')
            r = self.connector.sql.update(sql_delete_all_resources)
            if LOCAL_DEBUG:
                print(f'Return from DELETE of role is: {r}')
        except Exception as e:
            if LOCAL_DEBUG:
                print(e)

        return r        # count of deleted permissions

    # NOT TESTED
    def _add_all_permissions(self, role_name=None, role_pkid=None, permissions={}):
        """Add all permissions.
        Can assume that (a) role_name exists and that (b) no permissions exist yet
        If pkid for role is known it can be passed to speed up method

        :param role_name:   userRole name
        :param role_pkid:   userRole by PKID (if known will speed up method)
        :param permissions: DICT of K/V pairs which are tkresource/permission already formatted and checked
        
        :return:  tbd
        """

        LOCAL_DEBUG = False

        if role_pkid is None:
            pass
            # have to get pkid with sql query

        # check that permissions is not blank
        if permissions == {}:
            pass
        
        current_count = len(permissions.keys())

        for k, v in permissions.items():
            # TEMP item: print out where we are in writing permissions due to it taking so long...
            print(f'Role permissions to set: {current_count}')
            current_count -= 1
            # FUTURE ENHANCEMENT: This would be great as a call to a click function
            # since this is the core library, this would need to be triggered by a passed variable.
            # it doesn't belong here long-term

            values = f"('{role_pkid}','{k}','{v}')"
            sql_insert = f'INSERT INTO functionroleresourcemap (fkfunctionrole,tkresource,permission) VALUES {values};'
            
            if LOCAL_DEBUG:
                print(sql_insert)

            try:
                u = self.connector.sql.update(sql_insert)
                if LOCAL_DEBUG:
                    print('update returned:')
                    print(u)
            except Exception as e:
                if LOCAL_DEBUG:
                    print(e)

        return '_add_all_permissions returned no value'       # TODO: give a better return for this (it's internal anyways)

    def _update_resource_permissions(self, role_name, permissions={}):
        """
        this should be a PATCH and not an update.  if you want an update then we DELETE/ADD all items becuase this is too long
        TODO: use tkresource or "typeresource.name  (right now using tkresource)
        """
        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            print('starting update resource permissions')
        # return role pkid with all mappings
        # if 0 rows, then role_name is bad.
        # if 1 row, then role_name exists
        sql_get = ("select f.pkid as role_pkid, map.pkid, map.permission, map.tkresource "
                   " from functionrole as f left outer join functionroleresourcemap as map on f.pkid=map.fkfunctionrole "
                   f" where f.name='{role_name}'")
        try:
            r = self.connector.sql.query(sql_get)
        except:
            pass

        if LOCAL_DEBUG:
            print('select query returned:')
            print(type(r))
            print(r)
        
        # parse existing 
        if (len(r) == 1) and (r[0].get('pkid','') is None):
            print('FOUND NULL PKID IN FIRST ROW')
            print('continuing with empty mapping')

        if LOCAL_DEBUG:
            print('select query returned:')
            print(type(r))
            print(r)

        # iterate through permissions and update as needed
        for k, v in permissions.items():
            tkresource = k
            permission = v
            print(f'Current mapping: {tkresource} / {permission}')
            update_map = False
            skip_map = False

            if LOCAL_DEBUG:
                print(r)
                print(type(r))
            for row in r:
                if row['tkresource'] == tkresource:
                    update_map = True
                    existing_pkid = row['pkid']
                    if LOCAL_DEBUG:
                        print(f'PKID Found: {existing_pkid}')
                        print(f'tkresource found: {tkresource}')
                    if str(permission) == str(row['permission']):
                        skip_map = True
                    break

            if skip_map:
                if LOCAL_DEBUG: 
                    print('PERMISSIONS MATCH: SKIP update')
                break

            # insert or update?
            if update_map:
                sql = ("update functionroleresourcemap set permission = '{permission}' "
                       f" where fkfunctionrole=(select pkid from functionrole as f where f.name='{role_name}') and tkresource='{tkresource}'")
            else:
                sql = ("insert into functionroleresourcemap (fkfunctionrole,tkresource,permission) "
                       f" values ((select pkid from functionrole as f where f.name='{role_name}'),{tkresource},{permission})")
            # if permissions are 0 then delete
            # TODO: are these both UPDATE or is the insert a QUERY
            try:
                u = self.connector.sql.update(sql)
            except Exception as e:
                print(e)

            print('Update performed for mapping.')
            print(f'response is {str(u)}')


        # this is updating and adding....but it is not deleting
        return r[0]['role_pkid']

    def _x_add_update_user_role_permission(self, role_name, tkresource, permission, action='update'):
        """
        Phase 1 WORKING: Uses specific "tkresoure" and numeric "permission" setting
        since this is done in SQL we update a single permission at a time.  So updating some
        apps may take over 100 queries (yikes).  function only makes final edit if it finds a difference.

        Question: do we assume role exists or do we test for it first since this will be called AFTER
        add/update of the role?
        TODO: if last item deleted then proceed to remove_role (or document what might happen)
        TODO: add delete capability to this
        # delete a permission
        sql_delete = f"delete from functionroleresourcemap where fkfunctionrole=(select pkid from functionrole as f where f.name='{role_name}') and tkresource='{tkresource}'"
        """

        LOCAL_DEBUG = False

        # find if permission already exists
        sql_get = f"select map.pkid, map.permission from functionroleresourcemap as map, functionrole as f where map.fkfunctionrole=f.pkid and f.name='{role_name}' and map.tkresource='{tkresource}'"
        r = self.connector.sql.query(sql_get)
        if LOCAL_DEBUG: print(r)

        if len(r) == 1:                     # did we find permission?  If so do update
            pkid = r[0].get('pkid', '')
            current_permission = r[0].get('permission', '')
            if LOCAL_DEBUG:
                print(f'PKID Found: {pkid}')
                print(f'permision found: {current_permission}')
            if str(permission) == str(current_permission):
                if LOCAL_DEBUG: print('PERMISSIONS MATCH: SKIP update')
                return

            sql = f"update functionroleresourcemap set permission = '{permission}' where fkfunctionrole=(select pkid from functionrole as f where f.name='{role_name}') and tkresource='{tkresource}'"

            # TODO: Add delete capability
        else:
            if LOCAL_DEBUG:
                print('PKID NOT found for permision')
            sql = f"insert into functionroleresourcemap (fkfunctionrole,tkresource,permission) values ((select pkid from functionrole as f where f.name='{role_name}'),{tkresource},{permission})"

        if LOCAL_DEBUG:
            print(f"Resource: {tkresource}      Permission: {permission}")
            print(sql)

        r = self.connector.sql.update(sql)
        if LOCAL_DEBUG:
            print(r)

        return


# Add-On Experimental - Not part of WSDL API
class UserRank(SimpleAXLAPI):
    _factory_descriptor = "user_rank"
    supported_methods = ['list', 'update','add_update']

    """ User Rank does not exist in the SOAP API but is used by multiple objects.
    SQL queries are used to perform all operations.  Except some objects due to
    return the existing userRank value in a GET statement (TODO: list them)
    
    Your AXL User must have a rank equal or higher than the entries you are editing or
    the system will throw an error.

    The following objects are affected by userRank.
        userRank (new object)
        ldapDirectory
        user (enduser)
        appUser
        userGroup

    Object Constraints

    There are 10 ranks.  Only one per value.
    Rank is unique and name is unique.
    Rank (enum) is the pkid field for this table.
    Name is mandatory and unique, but does not appear to be a choice field.
    Rank can be found by number.  TODO: determine if can be found by name alone
    you can NOT change a rank...but you can change the name.

    """
    # User RANK Settings
    # NOTE: userRank/minimumuserrank does NOT exist in THICK AXL, all must be done through SQL
    #   Tables that have UserRank fields
    #       UserGroup:  Sql entry is dirgroup.minimumuserrank
    #       LdapDirectory: Sql entry is directorypluginconfig.userrank
    #       AppUser: Sql entry is applicationuser.userrank
    #       User: Sql entry is enduser.userrank
    #

    def __init__(self, connector, object_factory):
        super().__init__(connector, object_factory)

    # need to replace these methods and return static information for them.
    # this may need a WSDL object - hmmmmmm
    def _fetch_add_model(self):
        return {'rank', 'name', 'description'}

    def _fetch_update_method(self):
        return {'rank', 'name', 'description'}

    def _fetch_get_model(self):
        return {'rank'}

    def _fetch_get_method(self):
        return {'rank'}
    

    def add(self, rank=None, name=None, description=''):
        assert rank in [2,3,4,5,6,7,8,9,10,'2','3','4','5','6','7','8','9','10']

        # this wil throw errors
        if rank is None or name is None:
            print('ERROR: missing fields')
            return 0
        else:
            sql = f"insert into userrank (enum,name,description) values ('{rank}','{name}','{description}')"
            r = self.connector.sql.update(sql)


    def get(self, rank=None, name=None):
        assert rank in [1,2,3,4,5,6,7,8,9,10,'1','2','3','4','5','6','7','8','9','10']

        sql = f"select enum as rank, name, description from userrank where enum={rank}"
        r=self.connector.sql.query(sql)

        for line in r:
            if line['rank'] == str(rank):     # FOUND: Perform Update
                return line
    
        return {}


    def update(self, rank=None, name=None, description=None):
        #rank = kwargs.get('rank','')
        assert rank in [2,3,4,5,6,7,8,9,10,'2','3','4','5','6','7','8','9','10']

        # Does the line exist
        sql = "select enum as rank, name, description from userrank"          # grabbing all lines so to find 'name' as well
        r=self.connector.sql.query(sql)

        for line in r:
            if line['rank'] == str(rank):     # FOUND: Perform Update
                if name is None:
                    name = line['name']
                if description is None:
                    description = line['description']

                sql = f"update userrank set (name,description)=('{name}','{description}') where enum='{rank}' "
                r = self.connector.sql.update(sql)
                return r

        return 0
    
    def list(self, **kwargs):
    
        sql = "select enum as rank, name, description from userrank"          # grabbing all lines so to find 'name' as well
        
        return self.connector.sql.query(sql)

                   
    def remove(self, rank):
        assert rank in [2,3,4,5,6,7,8,9,10,'2','3','4','5','6','7','8','9','10']

        sql = f"delete from userrank where enum='{rank}'"
        r = self.connector.sql.update(sql)
        print (r)
        
        return r
    
    def add_update(self, obj_data):
        """Done with SQL queries
        There are actually 2 restricted fields (enum and name) but I am only working with enum
        This means if you try to "swap 2 names" you have to use a third entry.
        TODO: more graceful response to this scenario
        NOTE: The algorithm does a FOR loop to be ready to handle that case.  Otherwise, the
            SELECT query could have just looked for that single line item and bypassed the FOR loop
        """
        rank = obj_data.get('rank', None)
        name = obj_data.get('name', None)
        description = obj_data.get('description', None)

        # TODO: needs error checking
        # probably due an assert on rank to be a valid number
        if str(rank)=='1':
            # cannot edit rank 1
            return

        # Does the line exist
        # grabbing all lines so to find 'name' as well
        sql = "select enum as rank, name, description from userrank"
        r=self.connector.sql.query(sql)

        for line in r:
            if line['rank'] == str(rank):     # FOUND: Perform Update
                sql = f"update userrank set (name,description)=('{name}','{description}') where enum='{rank}' "
                r = self.connector.sql.update(sql)
                return r
            
        # NOT FOUND: Perform INSERT
        sql = f"insert into userrank (enum,name,description) values ('{rank}','{name}','{description}')"
        r = self.connector.sql.update(sql)

        return r

    def update_app_user_rank(self, name, rank):
        """ manually set UserRank on App User
        This appears to work BUT it does not clear the Access Groups when it is applied
        Not certain how this will behave down the road as cluster reboots.
        TODO: confirm that "rank" exists in userrank table
        """
        LOCAL_DEBUG = False

        sql = f"update applicationuser set userrank = '{rank}' where name='{name}'"
        r = self.connector.sql.update(sql)

        if LOCAL_DEBUG:
            print(sql)
            print(r)
        return r

    def update_end_user_rank(self, userid, rank):
        # set UserRank on End User using SQL

        LOCAL_DEBUG = False

        sql = f"update enduser set userrank = '{rank}' where userid='{userid}'"
        r = self.connector.sql.update(sql)

        if LOCAL_DEBUG:
            print(sql)
            print(r)
        return r

    def update_ldap_user_rank(self, ldap_name, rank):
        # set default UserRank for new users on LDAP Directory Sync using SQL

        LOCAL_DEBUG = False

        # get current user rank...update RANK (if different) before performing main update
        #sql = f"select userrank from directorypluginconfig where name='{ldapDirectory['name']}'"
        #u = self.connector.sql.query(sql)
        #current_user_rank=u[0].get('userrank', '')

        sql = f"update directorypluginconfig set userrank = '{rank}' where name='{ldap_name}'"
 
        r = self.connector.sql.update(sql)
 
        if LOCAL_DEBUG: 
            print(sql)
            print(r)
        return r

    def update_user_group_rank(self, user_group_name, minimum_user_rank):
        # set user rank on a access control group using SQL

        LOCAL_DEBUG = False

        sql = f"update dirgroup set minimumuserrank='{minimum_user_rank}' where name='{user_group_name}' "
        r = self.connector.sql.update(sql)

        if LOCAL_DEBUG:
            print(sql)
            print(r)
        return r


