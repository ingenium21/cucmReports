# THIS IS WORKING WITH LIMITED FUNCTIONALITY
#
# Using a GENERIC driver for linux to get things started
#
# NOTE: attempting to set prompt terminator BEFORE
import os
import time
import logging
from pprint import pprint
import click
from ciscocucmapi import UCMAXLConnector
import re
from rep_base import ReportTemplate
from lib_excel import CellFormatFixed, CellFormatBody, CellFormatHeader, CellFormatTitle

from dotenv import load_dotenv
# individual report job class is responsible to just return formatted data
# it does not write to the excel spreadsheet at this time

# TODO: this should go in ClickConfig and holds the location of the AXL schema files
AXL_SCHEMA_DIR = 'ciscocucmapi/schema'


class ReportLicenseStatus(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None, **kwargs):           # TODO: do we change this to **kwargs
        self.excel_manager = excel
        self.metadata = metadata
        self.vars = vars
        self.tab_name = metadata.get('tab_name','MISSING_TAB')
        self.title = metadata.get('title','MISSING_TITLE')

        # running data objects
        self.data_collected = None
        self.data_parsed = None
        self.data_formatted = None
        self.status = {}

        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.os_type = 'VOS'
        self.cluster_type = vars.get('type', '')
        self.axl_version = vars.get('axl_version', '12.5')

        #AXL_WSDL_URL=os.environ.get('AXL_WSDL_URL',f'ciscocucmapi/schema/{DEFAULT_AXL_VERSION}/AXLAPI.wsdl')
        self.axl_wsdl_url = f'{AXL_SCHEMA_DIR}/{self.axl_version}/AXLAPI.wsdl'
        self.commands = []


    def run(self):
        # connect and collect data
        status = self._collect_data()

        # process raw output before formatting
        status = self._parse_data()

        # process structured data and format to Excel
        status = self._format_data()

        return status

    def _collect_data(self):
        """Make a VOS connection and run commands to retrieve all certificate information

        Purpose of this method is to "collect" but do minimal processing.

        :return:        DICT of all output.  KEYS are typically the cert/service name and VALUES are the raw
                            output received from commands.
        """

        LOCAL_DEBUG = False

        axl = UCMAXLConnector(username=self.user, password=self.pwd, fqdn=self.host, wsdl=self.axl_wsdl_url)
        #axlmethodcaller = UCMAXLMethodCaller(axl)

        try:
            r = axl.get_ccm_version()
            print(r)
        except Exception as e:
            print('ERROR: Authentication failure.')
            print(e)

        try:
            print('*-' * 30)
            print('TRY smart_license_status.get()')
            r = axl.smart_license_status.get()

            # TODO: Change this to determine if data was returned by checking for the expected data type
            # if an error occurs then print out all the data in e
            
            if LOCAL_DEBUG:
                print('FINAL r return')
                pprint(r)
            
            status = 'success assumed'
        except Exception as e:
            logging.error('ERROR: Exception occured during _collect_data')
            print(e)
            logging.error('Response received: ')
            pprint(r)
            status = 'error during _collect_data'

        self.data_collected = r

        return status

    def _parse_data(self, raw_output=None):
 
        if not raw_output:
            raw_output = self.data_collected 
        
        self.data_parsed = raw_output

        return 'success assumed'
    
    def _format_data(self, data=None):
        """Final report formatting.   This is broken out because we could want different
        types of reports from this data.  This last method is for formatting different
        reports.
        """

        if not data:
            data = self.data_parsed 
        
        self.data_formatted = data
        
        return 'success assumed'

    def write_excel_tab(self, data=None, tab_name=None,  
                       title_format=CellFormatTitle(),
                       header_format=CellFormatHeader(),
                       body_format=CellFormatBody()):
        """first try of putting this inside the report job objct
        
        :param manager:  Excel manager object to write to
        :param tab_name:    this assumes 1 tab is being written
        
        :return status:     probably just a status response since the actions will happen in manager
        """
        
        """
        {'LicenseDetails': {'Authorization': {'AuthorizationExpires': 'Sun Mar 02 '
                                                              '11:10:25 EST '
                                                              '2025',
                                      'AuthorizationFailedReason': 'Successful.',
                                      'EvaluationPeriodRemaining': '89',
                                      'LastCommunicationAttempt': 'Mon Dec 02 '
                                                                  '14:00:19 '
                                                                  'EST 2024',
                                      'LastCommunicationStatus': 'SUCCEEDED',
                                      'NextCommunicationAttempt': 'Wed Jan 01 '
                                                                  '14:00:19 '
                                                                  'EST 2025',
                                      'Status': 'Authorized'},
                    'LicenseStatus': {'Entitlement': [{'Count': '10',
                                                       'Status': 'InCompliance',
                                                       'Tag': 'regid.2017-02.com.cisco.UCM_CUWL,12.0_cc59375a-1cd8-4b36-8366-6f4d2abba965'},
                                                      {'Count': '3',
                                                       'Status': 'InCompliance',
                                                       'Tag': 'regid.2016-07.com.cisco.UCM_EnhancedPlus,12.0_d8372792-588c-4caa-b279-8587e5ce2f82'},
                                                      {'Count': '7',
                                                       'Status': 'InCompliance',
                                                       'Tag': 'regid.2016-07.com.cisco.UCM_Enhanced,12.0_66d0d1cf-4863-4761-91d0-d01d3eb1949a'},
                                                      {'Count': '1',
                                                       'Status': 'InCompliance',
                                                       'Tag': 'regid.2016-07.com.cisco.UCM_Basic,12.0_ef827a2f-f4ae-4ebb-887f-052737063d3a'},
                                                      {'Count': '0',
                                                       'Status': 'Init',
                                                       'Tag': 'regid.2016-07.com.cisco.UCM_Essential,12.0_25f9c396-c67c-4519-aa98-d4b3ad18f805'},
                                                      {'Count': '7',
                                                       'Status': 'InCompliance',
                                                       'Tag': 'regid.2016-07.com.cisco.UCM_TelePresenceRoom,12.0_d9a71418-29e9-4c9a-9d3a-1366ebe38e7c'}]},
                    'Registration': {'ExportControlFunctionality': 'ALLOWED',
                                     'LastRenewalAttempt': 'Wed Nov 20 '
                                                           '19:31:12 EST 2024',
                                     'LastRenewalStatus': 'SUCCEEDED',
                                     'NextRenewalAttempt': 'Mon May 19 '
                                                           '20:31:12 EDT 2025',
                                     'ProductUDI': 'UDI: '
                                                   'PID:UCM,SN:0efb8,UUID:27524c63780b4d7dafd213703a20efb8',
                                     'RegistrationExpires': 'Thu Nov 20 '
                                                            '16:44:29 EST 2025',
                                     'RegistrationFailedReason': 'Successful.',
                                     'SmartAccount': 'IRON BOW TECHNOLOGIES',
                                     'Status': 'Registered',
                                     'VirtualAccount': 'ironbowlab'},
                    'SmartLicensing': 'ENABLED'}}

        """

        """
        SQL Query that CCMAdmin uses:
        SELECT tcrs.moniker, tcas.moniker, daysleft, smartaccountname, virtualaccountname, deploymentmode, tst.name, lastrenewalattempt, nextrenewalattempt, registrationexpires, lastauthattempt, nextauthattempt, authorizationexpires, isregistrationfailed, isauthorizationfailed, registrationfailedreason, authorizationfailedreason, evaluationexpiredtime, transportgatewayurl, overagedays, overagedaysupdatedtime, isprovisionallowed, tst.enum, si.exportcontrolledallow, ss.productinstancename, reservationrequested, ss.deploymentmode FROM slminfo si, slmserver ss, typecssmregstatus tcrs, typecssmauthstatus tcas, typeslmtransport tst WHERE fkslmserver = ss.pkid and tkcssmregstatus=tcrs.enum and tkcssmauthstatus=tcas.enum and tst.enum = ss.tkslmtransport

        tables slmserver and slminfo.
        
        TODO:
            Add:
                Last Updated: DATE
                
            Headers:
                User Id, First Name, Lastname, SNR Enabled, Device count, License Type, LIcenses used
                
                Count of how many licensed users
                """
        
        LOCAL_DEBUG = False

        status = None   # initialize locally to None

        if not data:
            data = self.data_formatted
        if not tab_name:
            tab_name = self.tab_name

        if not self.excel_manager.workbook:
            raise Exception("No active workbook. Create or open a spreadsheet first.")
        sheet = self.excel_manager.workbook.create_sheet(title=tab_name)

        if LOCAL_DEBUG:
            click.secho(f'data before writing', fg='red')
            click.secho('DATA_COLLECTED', fg='yellow')
            pprint(self.data_collected)
            click.secho('DATA_PARSED', fg='yellow')
            pprint(self.data_parsed)
            click.secho('DATA_FORMATTED', fg='yellow')
            pprint(self.data_formatted)
            click.secho('DATA_TO_USE', fg='yellow')
            pprint(data)

        try:
            auth_data  = data['LicenseDetails']['Authorization']
            reg_data   = data['LicenseDetails']['Registration']
            lic_data   = data['LicenseDetails']['LicenseStatus']
            smart_data = data['LicenseDetails']['SmartLicensing']
        except Exception as e:
            click.secho(f'ERROR: Expected dictionary items not in data.', fg='red')
            status = 'ERROR during write_excel_tab'

        # CUSTOM REPORT

        # TITLE LINE: License Management 
        value = 'License Management'
        row = 1
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = title_format.font
        cell.fill = title_format.fill
        cell.alignment = title_format.alignment
        cell.border = title_format.border
        

        # HEADER: Authorization Data (Column 1)
        value = 'Smart Software Licensing'
        row += 2
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = header_format.font
        cell.fill = header_format.fill
        cell.alignment = header_format.alignment
        cell.border = header_format.border

        row += 2

        # HEADER: Authorization Data (Column 1)
        value = 'Authorization Data'
        row += 2
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = header_format.font
        cell.fill = header_format.fill
        cell.alignment = header_format.alignment
        cell.border = header_format.border

        row += 1
        # Authoriation Items
        for k, v in auth_data.items():
            cell = sheet.cell(row=row, column=2, value=k)
            cell.font = header_format.font
            cell.fill = header_format.fill
            cell.alignment = header_format.alignment
            cell.border = header_format.border

            cell = sheet.cell(row=row, column=3, value=v)
            cell.font = body_format.font
            cell.fill = body_format.fill
            cell.alignment = body_format.alignment
            cell.border = body_format.border

            row += 1

        # HEADER: Registration Data (Column 1)
        value = 'Registration Data'
        row += 2
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = header_format.font
        cell.fill = header_format.fill
        cell.alignment = header_format.alignment
        cell.border = header_format.border

        row += 1
        # Registration Items
        for k, v in reg_data.items():
            cell = sheet.cell(row=row, column=2, value=k)
            cell.font = header_format.font
            cell.fill = header_format.fill
            cell.alignment = header_format.alignment
            cell.border = header_format.border

            cell = sheet.cell(row=row, column=3, value=v)
            cell.font = body_format.font
            cell.fill = body_format.fill
            cell.alignment = body_format.alignment
            cell.border = body_format.border

            row += 1
        #
        #   SmartLicensing: Enabled ALSO Add in Smartlicensing

        # HEADER: "Registration"
        #       Body col1/col2
        #

        # HEADER: Authorization Data (Column 1)
        value = 'License Requirements by Type'
        row += 2
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = header_format.font
        cell.fill = header_format.fill
        cell.alignment = header_format.alignment
        cell.border = header_format.border

        row += 2

        # HEADER: LicenseStatus
        #   FOR LOOP BODY (3 items of count/status/tag)
        #   GUI HEADER: License Requirements by Type
        #   GUI FIELDS: License Type, Current Usage, Status, Report

        # ent_data is a LIST of DICTs
        ent_data = lic_data.get('Entitlement', [])

        # print headers by parsing through keys once
        col_start = 1   # will be added to
        col_headers = list(ent_data[0].keys())

        for col_num, header in enumerate(col_headers, start=1):
            cell = sheet.cell(row=row, column=col_num + col_start, value=header)
            cell.font = header_format.font
            cell.fill = header_format.fill
            cell.alignment = header_format.alignment
            cell.border = header_format.border

        # Write data with formatting
        row_start = row + 2
        #rows = zip(*ent_data.values())
        for row_idx, row in enumerate(ent_data, start=2):  # Start from second row
            for col_idx, col in enumerate(col_headers, start=1):
                value = row[col]
                if col == 'Tag':
                    # CUSTOM Parsing to pull out the license type from the TAG field
                    match = re.search(r'\.cisco\.([^,]*),', value)
                    if match:
                        value = match.group(1)     
                cell = sheet.cell(row=row_idx+row_start, column=col_idx+col_start, value=value)
                cell.font = body_format.font
                cell.fill = body_format.fill
                cell.alignment = body_format.alignment
                cell.border = body_format.border

        # NOTE: this was copied from another method and isn't wokring correctly here yet
        # Auto-adjust column widths
        for col_num, col_cells in enumerate(sheet.columns, start=1):
            max_length = max(len(str(cell.value or "")) for cell in col_cells)
            sheet.column_dimensions[sheet.cell(row=1, column=col_num).column_letter].width = max_length + 2

        print(f"Added a new tab [{tab_name}] with formatted data to the workbook.")

        if not status:
            status = 'success assumed'
        return status

class ReportLicenseUsage(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None, **kwargs):           # TODO: do we change this to **kwargs
        pprint(vars)
        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.os_type = 'VOS'
        self.cluster_type = vars.get('type', '')
        self.axl_version = vars.get('axl_version', '12.5')

        #AXL_WSDL_URL=os.environ.get('AXL_WSDL_URL',f'ciscocucmapi/schema/{DEFAULT_AXL_VERSION}/AXLAPI.wsdl')
        self.axl_wsdl_url = f'{AXL_SCHEMA_DIR}/{self.axl_version}/AXLAPI.wsdl'
        self.commands = []

        self.excel_manager = excel
        self.metadata = metadata
        self.vars = vars
        self.tab_name = metadata.get('tab_name','MISSING_TAB')
        self.title = metadata.get('title','MISSING_TITLE')

        # running data objects
        self.data_collected = None
        self.data_parsed = None
        self.data_formatted = None
        self.status = {}

    def run(self):
        # connect and collect data
        status = self._collect_data()

        # process raw output before formatting
        status = self._parse_data()

        # process structured data and format to Excel
        status = self._format_data()

        return status

    def _collect_data(self):
        """Make a VOS connection and run commands to retrieve all certificate information

        Purpose of this method is to "collect" but do minimal processing.

        :return:        DICT of all output.  KEYS are typically the cert/service name and VALUES are the raw
                            output received from commands.
        """

        LOCAL_DEBUG = False

        axl = UCMAXLConnector(username=self.user, password=self.pwd, fqdn=self.host, wsdl=self.axl_wsdl_url)
        #axlmethodcaller = UCMAXLMethodCaller(axl)

        try:
            r = axl.get_ccm_version()
            print(r)
        except Exception as e:
            print(e)

        try:
            print('*-' * 30)
            print('TRY smart_license_status.get()')
            r = axl.licensed_user.list()

            if LOCAL_DEBUG:
                print('FINAL r return')
                pprint(r)
        
                print(f'Length of returned list: {len(r)}')

            status = 'success assumed'        
        except Exception as e:
            logging.error('ERROR: Exception occured during _collect_data')
            print(e)
            logging.error('Response received: ')
            pprint(r)
            status = 'error during _collect_data'

        self.data_collected = r

        return status
    
    def _parse_data(self, raw_output=None):
 
        if not raw_output:
            raw_output = self.data_collected

        self.data_parsed = raw_output

        return 'success assumed'
    
    def _format_data(self, output=None):
        """Final report formatting.   This is broken out because we could want different
        types of reports from this data.  This last method is for formatting different
        reports.
        """

        if not output:
            output = self.data_parsed

        self.data_formatted = self.data_parsed

        return 'success assumed'


    def write_excel_tab(self, data=None, tab_name=None,  
                       title_format=CellFormatTitle(),
                       header_format=CellFormatHeader(),
                       body_format=CellFormatBody()):
        """first try of putting this inside the report job objct
        
        :param manager:  Excel manager object to write to
        :param tab_name:    this assumes 1 tab is being written
        
        :return status:     probably just a status response since the actions will happen in manager
        """
        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name

        if not self.excel_manager.workbook:
            raise Exception("No active workbook. Create or open a spreadsheet first.")
        sheet = self.excel_manager.workbook.create_sheet(title=self.tab_name)

        # CUSTOM REPORT

        # TITLE LINE: License Management 
        value = 'Licensed User Usage'
        row = 1
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = title_format.font
        cell.fill = title_format.fill
        cell.alignment = title_format.alignment
        cell.border = title_format.border
        
        # ent_data is a LIST of DICTs
        table_data = data
        
        # print headers by parsing through keys once

        row = 3
        col_start = 1   # will be added to
        col_headers = list(table_data[0].keys())

        for col_num, header in enumerate(col_headers, start=1):
            cell = sheet.cell(row=row, column=col_num + col_start, value=header)
            cell.font = header_format.font
            cell.fill = header_format.fill
            cell.alignment = header_format.alignment
            cell.border = header_format.border

        # Write data with formatting
        row_start = row + 1
        #rows = zip(*ent_data.values())
        for row_idx, row in enumerate(table_data, start=2):  # Start from second row
            for col_idx, col in enumerate(col_headers, start=1):
                value = row[col]
                if col == 'Tag':
                    # CUSTOM Parsing to pull out the license type from the TAG field
                    match = re.search(r'\.cisco\.([^,]*),', value)
                    if match:
                        value = match.group(1)     
                cell = sheet.cell(row=row_idx+row_start, column=col_idx+col_start, value=value)
                cell.font = body_format.font
                cell.fill = body_format.fill
                cell.alignment = body_format.alignment
                cell.border = body_format.border


        print(f"Added a new tab [{tab_name}] with formatted data to the workbook.")

        return 'success assumed'

class ReportUnassignedDevices(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None, **kwargs):           # TODO: do we change this to **kwargs
        pprint(vars)
        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.os_type = 'VOS'
        self.cluster_type = vars.get('type', '')
        self.axl_version = vars.get('axl_version', '12.5')

        #AXL_WSDL_URL=os.environ.get('AXL_WSDL_URL',f'ciscocucmapi/schema/{DEFAULT_AXL_VERSION}/AXLAPI.wsdl')
        self.axl_wsdl_url = f'{AXL_SCHEMA_DIR}/{self.axl_version}/AXLAPI.wsdl'
        self.commands = []

        # this query DOES need some work to restrict it down to ONLY phones that are licensed.
        # Need a TypeClass=Phone (1)
        # Also need to get the TypeModel listing into a list (or exclude cti)
        self.sql = ('select d.name, d.description, typemodel.name as deviceType, '
                    ' typemodel.enum '  # just for troubleshooting - remove this for production
                    ' from device as d '
                    ' left outer join enduser as eu on d.fkenduser=eu.pkid '
                    ' left outer join TypeModel on d.tkmodel=TypeModel.enum '
                    ' where eu.userid is null '
                    ' and d.tkclass = 1 '        # TypeClass = Phone
                    ' and d.tkmodel != 72'      # ignore CTI Ports
        )

        # NOTE: This query generated by reading TOMCAT logs of CCMAdmin page
        self.sql = ("SELECT D.pkid, D.name devicename, D.description description, TP.name productname,"
                    "(CASE WHEN (TLRPM.tklicensedresource = 6) THEN 'TelePresence Room' "
                    " ELSE (CASE WHEN (TLRPM.tklicensedresource = 4) THEN 'CUWL Standard' "
                    " ELSE (CASE WHEN (TLRPM.tklicensedresource = 3 OR TLRPM.tklicensedresource IS NULL) THEN 'Enhanced' "
                    " ELSE (CASE WHEN (TLRPM.tklicensedresource = 8) THEN 'Adjunct' "
                    " ELSE (CASE WHEN (TLRPM.tklicensedresource = 2) THEN 'Basic' "
                    " ELSE (CASE WHEN (TLRPM.tklicensedresource = 1) THEN 'Essential' END) END) END) END) END) END) "
                    " licensetype,NVL(NP.dnorpattern,' ') extension "
                    " FROM Device D "
                    " LEFT OUTER JOIN TypeLicensedResourceProductMap TLRPM ON (TLRPM.tkProduct = D.tkProduct) "
                    " INNER JOIN TypeProduct TP ON (D.tkProduct = TP.enum) "
                    " LEFT OUTER JOIN DeviceNumPlanMap DNPM ON (DNPM.fkdevice = D.pkid and DNPM.numplanindex=1) "
                    " LEFT OUTER JOIN NumPlan NP ON (DNPM.fknumplan=NP.pkid) "
                    " WHERE D.fkEndUser IS NULL and D.tkClass = 1 "
                    " AND (TLRPM.tklicensedresource != 7 OR TLRPM.tklicensedresource IS NULL) "
                    " AND ((my_lower(d.name::lvarchar) LIKE my_lower('%')  "
                    " OR d.name IS NULL OR my_lower(d.name::lvarchar) = ''))"
        )

        self.excel_manager = excel
        self.metadata = metadata
        self.vars = vars
        self.tab_name = metadata.get('tab_name','MISSING_TAB')
        self.title = metadata.get('title','MISSING_TITLE')

        # running data objects
        self.data_collected = None
        self.data_parsed = None
        self.data_formatted = None
        self.status = {}

    def run(self):
        # connect and collect data
        status = self._collect_data()

        # process raw output before formatting
        status = self._parse_data()

        # process structured data and format to Excel
        status = self._format_data()

        return status

    def _collect_data(self):
        """First SQL Test

        :return:        DICT of all output.  KEYS are typically the cert/service name and VALUES are the raw
                            output received from commands.

        fields in this are 
            name,
            description
            device type
            LICEnSe type (how do I get this?)
            Extension (line 1)

        Easy enough SQL query except for licnese type which may need to be a seperate lookup table.

        """
        LOCAL_DEBUG = False

        click.secho(f'{__class__} collecting data...')
        axl = UCMAXLConnector(username=self.user, password=self.pwd, fqdn=self.host, wsdl=self.axl_wsdl_url)
        #axlmethodcaller = UCMAXLMethodCaller(axl)

        try:
            r = axl.get_ccm_version()
            print(r)
        except Exception as e:
            print(e)

        try:
            print('*-' * 30)
            print('TRY SQL query)')
            r = axl.sql.query(self.sql)

            # TODO: planned success check is whether it returns a LIST or not
            if LOCAL_DEBUG:
                print('FINAL r return')
                pprint(r)
        
                print(f'Length of returned list: {len(r)}')

            status = 'success assumed'        
        except Exception as e:
            logging.error('ERROR: Exception occured during _collect_data')
            print(e)
            logging.error('Response received: ')
            pprint(r)
            status = 'error during _collect_data'

        self.data_collected = r

        return status

    def _parse_data(self, raw_output=None):
 
        if not raw_output:
            raw_output = self.data_collected

        self.data_parsed = raw_output
        
        return 'success assumed'
    
    def _format_data(self, data=None):
        """Final report formatting.   This is broken out because we could want different
        types of reports from this data.  This last method is for formatting different
        reports.
        """
        if not data:
            data = self.data_parsed

        self.data_formatted = data

        return 'success assumed'


    def write_excel_tab(self, data=None, tab_name=None,  
                       title_format=CellFormatTitle(),
                       header_format=CellFormatHeader(),
                       body_format=CellFormatBody()):
        """first try of putting this inside the report job objct
        
        :param manager:  Excel manager object to write to
        :param tab_name:    this assumes 1 tab is being written
        
        :return status:     probably just a status response since the actions will happen in manager
        """
        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name

        if not self.excel_manager.workbook:
            raise Exception("No active workbook. Create or open a spreadsheet first.")
        sheet = self.excel_manager.workbook.create_sheet(title=self.tab_name)

        # CUSTOM REPORT

        # TITLE LINE: License Management 
        value = 'Licensed Unassigned Devices'
        row = 1
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = title_format.font
        cell.fill = title_format.fill
        cell.alignment = title_format.alignment
        cell.border = title_format.border
        
        # ent_data is a LIST of DICTs
        table_data = data
        
        # print headers by parsing through keys once

        row = 3
        col_start = 1   # will be added to
        col_headers = list(table_data[0].keys())

        for col_num, header in enumerate(col_headers, start=1):
            cell = sheet.cell(row=row, column=col_num + col_start, value=header)
            cell.font = header_format.font
            cell.fill = header_format.fill
            cell.alignment = header_format.alignment
            cell.border = header_format.border

        # Write data with formatting
        row_start = row
        #rows = zip(*ent_data.values())
        for row_idx, row in enumerate(table_data, start=1):  # Start from second row
            for col_idx, col in enumerate(col_headers, start=1):
                value = row[col]
                if col == 'Tag':
                    # CUSTOM Parsing to pull out the license type from the TAG field
                    match = re.search(r'\.cisco\.([^,]*),', value)
                    if match:
                        value = match.group(1)     
                cell = sheet.cell(row=row_idx+row_start, column=col_idx+col_start, value=value)
                cell.font = body_format.font
                cell.fill = body_format.fill
                cell.alignment = body_format.alignment
                cell.border = body_format.border


        print(f"Added a new tab [{tab_name}] with formatted data to the workbook.")

        return 'success assumed'

def main():

    # test example to lab 12 server
    vars = {'ip': '10.10.42.10',
            'host': '10.10.42.10',
            'user': 'administrator',
            'pwd': 'Ir0nv01p',
            'axl_version': '12.5',
            }
    
    report = ReportLicenseStatus(vars)
    r = report.run()
    pprint(r)

# Testing routine
if __name__ == "__main__":
     main()