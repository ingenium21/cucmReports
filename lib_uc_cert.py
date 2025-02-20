# Methods for using the Cisco Certificate API for UC devices
#
#

import click
import requests
from pprint import pprint
import json

from rep_base import ReportTemplate
from lib_certs import *
from lib_excel import CellFormatTitle, CellFormatHeader, CellFormatBody, CellFormatFixed

"""
For the UC Cert Snapshot format, see the file "uc_cert_snapshot_output.yaml"
"""


def get_uc_cert_snapshot(base_url, auth, verify_ssl=True):
    """Retrieve certificates from Cisco UC Server (VOS v14 or higher - UCM/CER/CUC/IMPS).
    
    :return:    dictionary of SNAPSHOT data.  None if error
    :return:    JSON response with data OR 'None' if error
    """
    endpoint = f"{base_url}/platformcom/api/v1/certmgr/config/snapshot/server"
    try:
        response = requests.get(endpoint, auth=auth, verify=verify_ssl)
        if response.status_code == 200:
            return response.json()  # Assuming response is JSON and includes certificates
        else:
            click.secho(f"Failed to retrieve certificates: HTTP {response.status_code}")
            return None
    except Exception as e:
        click.secho(f"Error accessing Cisco UCM API: {e}")
        return None


def load_uc_cert_snapshot_from_file(file_path):
    """Test routine to load stored UC cert snapshot data as json format rather than making a live call to server

    :param filename:    filename to load.  JSON format
    :return:            JSON object of the UC snapshot 
    """

    try:
        with open(file_path, "rb") as snapshot_file:
            return json.load(snapshot_file)
    except Exception as e:
        print(f"Error loading snapshot: {e}")
        return None


def get_uc_cert_options(base_url, auth, verify_ssl=True):
    """
    Retrieve 'options' from the Cisco UCM REST server.

    Args:
        base_url (str): The base URL of the Cisco UCM server (e.g., 'https://ucm.example.com').
        auth (tuple): Authentication credentials as a tuple (username, password).
        verify_ssl (bool): Whether to verify SSL certificates.

    Returns:
        dict: The options retrieved from the server, or None if the call fails.
    """
    endpoint = f"{base_url}/platformcom/api/v1/certmgr/config/options"
    try:
        response = requests.get(endpoint, auth=auth, verify=verify_ssl)
        if response.status_code == 200:
            click.secho("Options successfully retrieved.")
            return response.json()
        else:
            click.secho(f"Failed to retrieve options: HTTP {response.status_code}")
            return None
    except Exception as e:
        click.secho(f"Error accessing Cisco UCM API: {e}")
        return None


# #############################################
# Process UC Cert Data
#
#   Methods for processing a uc_cert_snapshot dictionary
#


def print_all_uc_certs(cert_snapshot, format='long'):
    """identity / trust / csr """
    tracking_id = cert_snapshot.get('trackingId', '')
    server = cert_snapshot.get('server', '')

    id_cert_data = cert_snapshot.get('identities', {})
    trust_cert_data = cert_snapshot.get('trusts', {})
    revoked_cert_data = cert_snapshot.get('revokedCertificates', [])

    click.secho('-*' * 30, fg="red")
    click.secho(f'Printing all certificates for UC Server: {server}', fg="blue")
    click.secho('Identity Certificates:', fg="blue")

    for service_data in id_cert_data:
        service_name = service_data.get('service', "")
        pem_data = service_data.get("certificate", "")
        if not pem_data:
            click.secho(f"Certificate data missing for {service_name}.", fg="red")
            continue

        cert = load_pem_certificate_from_data(pem_data)
        if not cert:
            click.secho(f"Failed to load certificate for {service_name}.", fg="red")
            continue

        if format not in ['silent']:
            click.secho(f"\nProcessing certificate: {service_name}", fg="blue")
        print_certificate_details(cert, format=format)


# this routine is an older version and is being replaced by process_uc_cert_expiration_report
def process_uc_certificates(cert_snapshot, days_until_expiration=30, format='long'):
    """Process certificates retrieved from Cisco UCM.
    
    :param format:      silent, basic, long

    """
    if not cert_snapshot:
        click.secho("No data received from Cisco UCM.")
        return

    expired = []
    near_expiration = []
    valid = []

    """
    Cert Snapshot has:
        identities: list of certificate/service/csr
        trusts: list of service/certificte_data
            certificate_data is a list of filename/certificate (where certificate is the PEM string)
        revokedCertifictes:
    """

    # for this routine, we want 
    id_cert_data = cert_snapshot.get('identities', {})
    trust_cert_data = cert_snapshot.get('trusts', {})

    # Process IDENTITY certs (single cert per service)
    for service_data in id_cert_data:
        service_name = service_data.get('service', "")
        pem_data = service_data.get("certificate", "")
        if not pem_data:
            if format not in ['silent']:
                click.secho(f"Certificate data missing for {service_name}.")
            continue

        cert = load_pem_certificate_from_data(pem_data)
        if not cert:
            if format not in ['silent']:
                click.secho(f"Failed to load certificate for {service_name}.")
            continue

        if format not in ['silent']:
            click.secho(f"\nProcessing certificate: {service_name}")

        if format == 'long':
            print_certificate_details(cert, format='long')

        if is_certificate_expired(cert):
            expired.append(service_name)
        elif is_certificate_near_expiration(cert, days_until_expiration):
            near_expiration.append(service_name)
        else:
            valid.append(service_name)

    # Process TRUST cert stores (multiple certs per service)
    for trust_data in trust_cert_data:
        service_name = trust_data.get('service', "")
        cert_list = trust_data.get("certificate_data", "")
        for this_cert in cert_list:                # TODO: don't like this variable name
            file_name = this_cert.get('filename', "")
            pem_data = this_cert.get("certificate", "")
            if not pem_data:
                if format not in ['silent']:
                    click.secho(f"Certificate data missing for {file_name}.")
                continue

            cert = load_pem_certificate_from_data(pem_data)
            if not cert:
                if format not in ['silent']:
                    click.secho(f"Failed to load certificate for {file_name}.")
                continue

            if format not in ['silent']:
                click.secho(f"\nProcessing certificate: {file_name}")

            if format == 'long':
                print_certificate_details(cert, format='long')

            if is_certificate_expired(cert):
                expired.append(file_name)
            elif is_certificate_near_expiration(cert, days_until_expiration):
                near_expiration.append(file_name)
            else:
                valid.append(file_name)

    click.secho("\nSummary for Cisco UC Certificates:", fg="yellow")
    click.secho("Expired Certificates:", fg="yellow")
    for cert_name in expired:
        click.secho(f" - {cert_name}")

    click.secho("\nCertificates Near Expiration:", fg="yellow")
    for cert_name in near_expiration:
        click.secho(f" - {cert_name}")

    click.secho("\nValid Certificates:", fg="yellow")
    for cert_name in valid:
        click.secho(f" - {cert_name}")
    
    cert_status = {'expired': expired,
                   'near_expiration': near_expiration,
                   'valid': valid}
    
    excel_headers = ['server', 'type', 'service', 'name', 'serialnumber', 'expiration_date']
    return cert_status


def process_uc_cert_expiration_report(cert_snapshot, days_until_expiration=30, format='long'):
    """Process certificates retrieved from Cisco UCM. 
     
    This report is processing a "single" UC snapshot.  So each server gets run seperately.  Not setup
    yet to do an entire cluster or multiple clusters into a single set of data.
    But that could be done by making a "merge" function to pull the data structures together.
    
    The report prints things out in order that they were received in the snapshot.  No sorting yet.

    Be aware, multiple formats were tried on this and remnants exist from both tries.

    :param format:      silent, basic, long

    IDEA: Should this routine ACTUALLY just process the data and return as many fields as possible in a table foramt?
        Consider if this routine used the "format" parameter to determine which fields (or groups of fields) to return
        THEN, the next 'formatting' routine had the job of pulling out what fields it wanted to make individual reports
        That would probably be more flexible for different reports: 1 data extractions routine and then multiple report formatting routines
        With that, we probalby wouldn't use the current data format.  It would probably just be a LIST of DICTS with the dict be k/v pairs for the data pulled out.
    """

    """
    Current Formatting for loading this report to Excel: 
    
    Data structure is a dictionary of lists and it calls the "add_tab_with_formatted_data()" routine for now.

        Data format example:
            sample_data = {
                "Name": ["Alice", "Bob", "Charlie"],
                "Age": [25, 30, 35],
                "City": ["New York", "Los Angeles", "Chicago"]
            }
        Keys are Column Headers
        List attached is row data
        NOTE: this format was used becasue we had an excel method that used it...not because we particularly like the structure

    """

    LOCAL_DEBUG = False

    if not cert_snapshot:
        click.secho("No data received from Cisco UCM.")
        return None

    # what is the output of the report
    excel_formatted_data = {
        'server': [],
        'type': [],
        'service': [],
        'name': [],
        'serial_number': [],
        'expiration_data': [],
        'exp_status': [],
    }

    # format 1 for output (probably going away OR we keep this because it's simpler and have a later method that merges and formats)
    excel_headers = ['server', 'type', 'service', 'name', 'serial_number', 'expiration_date', 'exp_status']
    excel_data = []     # initialize CSV data for report

    # this classification is being used for screen output and not for report output
    expired = []
    near_expiration = []
    valid = []

    """
    Cert Snapshot has:
        identities: list of certificate/service/csr
        trusts: list of service/certificte_data
            certificate_data is a list of filename/certificate (where certificate is the PEM string)
        revokedCertifictes:
    """

    # For this report, pull the server name and the "identity" and "trust certs"
    server_name = cert_snapshot.get('server', 'NAME_NOT_FOUND')
    id_cert_data = cert_snapshot.get('identities', {})
    trust_cert_data = cert_snapshot.get('trusts', {})

    # Process IDENTITY certs (single cert per service)
    for service_data in id_cert_data:
        service_name = service_data.get('service', "")
        pem_data = service_data.get("certificate", "")

        # if ther eare no certs then ignore and do not print out
        if not pem_data:
            if format not in ['silent']:
                click.secho(f"Certificate data missing for {service_name}.")
            continue

        cert = load_pem_certificate_from_data(pem_data)

        if not cert:
            # TODO: This is an error condition that we are ignoring.  Should this be reported on?
            if format not in ['silent']:
                click.secho(f"Failed to load certificate for {service_name}.")
            continue

        # start new row of excel data (format 1)
        new_row = {'server': server_name,
                   'type': 'Own',
                   'service': service_name}
        
        # format 2 for excel data
        excel_formatted_data['server'].append(server_name)
        excel_formatted_data['type'].append('Own')
        excel_formatted_data['service'].append(service_name)
        

        # excel data (format 1)
        new_row['serial_number'] = get_serial_number(cert)
        new_row['expiration_data'] = get_certificate_expiration(cert)
        new_row['name'] = 'LEAVE BLANK'         # TODO: Or do we put the CN in here?  Trust certs have a filename.

        # excel data (format 2)
        excel_formatted_data['serial_number'].append(str(get_serial_number(cert)))
        excel_formatted_data['expiration_data'].append(get_certificate_expiration(cert))
        excel_formatted_data['name'].append('LEAVE BLANK')         # TODO: Or do we put the CN in here?  Trust certs have a filename.

        if format not in ['silent']:
            click.secho(f"\nProcessing certificate: {service_name}")

        if format == 'long':
            print_certificate_details(cert, format='long')

        if is_certificate_expired(cert):
            expired.append(service_name)
            excel_formatted_data['exp_status'].append('EXPIRED')
        elif is_certificate_near_expiration(cert, days_until_expiration):
            near_expiration.append(service_name)
            excel_formatted_data['exp_status'].append('Near Expiration')
        else:
            valid.append(service_name)
            excel_formatted_data['exp_status'].append('')

        # add to excel data output (format 1 only)
        excel_data.append(new_row)

    # Process TRUST cert stores (multiple certs per service)
    for trust_data in trust_cert_data:
        service_name = trust_data.get('service', "")
        cert_list = trust_data.get("certificate_data", "")

        for this_cert in cert_list:                # TODO: don't like this variable name

            file_name = this_cert.get('filename', "")
            pem_data = this_cert.get("certificate", "")

            if not pem_data:
                # TODO: This is an error condition that we are ignoring.  Should this be reported on?
                if format not in ['silent']:
                    click.secho(f"Certificate data missing for {file_name}.")
                continue

            cert = load_pem_certificate_from_data(pem_data)
            if not cert:
                # TODO: This is an error condition that we are ignoring.  Should this be reported on?
                if format not in ['silent']:
                    click.secho(f"Failed to load certificate for {file_name}.")
                continue

            # start new row of excel data (format 1)
            new_row = {'server': server_name,
                    'type': 'Trust',
                    'service': service_name}

            # udpate excel data (format 1)
            new_row['serial_number'] = get_serial_number(cert)
            new_row['expiration_data'] = get_certificate_expiration(cert)
            new_row['name'] = file_name

            # format 2 for excel data
            excel_formatted_data['server'].append(server_name)
            excel_formatted_data['type'].append('Trust')
            excel_formatted_data['service'].append(service_name)

            # update excel data (format 2)
            excel_formatted_data['serial_number'].append(str(get_serial_number(cert)))
            excel_formatted_data['expiration_data'].append(get_certificate_expiration(cert))
            excel_formatted_data['name'].append(file_name)
            
            if format not in ['silent']:
                click.secho(f"\nProcessing certificate: {file_name}")

            if format == 'long':
                print_certificate_details(cert, format='long')

            if is_certificate_expired(cert):
                expired.append(file_name)
                excel_formatted_data['exp_status'].append('EXPIRED')
            elif is_certificate_near_expiration(cert, days_until_expiration):
                near_expiration.append(file_name)
                excel_formatted_data['exp_status'].append('Near Expiration')
            else:
                valid.append(file_name)
                excel_formatted_data['exp_status'].append('')

            # add to excel data output (format 1 only)
            excel_data.append(new_row)

    # print out result if not 'silent'
    if format.lower() != 'silent':
        click.secho("\nSummary for Cisco UC Certificates:", fg="yellow")
        click.secho("Expired Certificates:", fg="yellow")
        for cert_name in expired:
            click.secho(f" - {cert_name}")

        click.secho("\nCertificates Near Expiration:", fg="yellow")
        for cert_name in near_expiration:
            click.secho(f" - {cert_name}")

        click.secho("\nValid Certificates:", fg="yellow")
        for cert_name in valid:
            click.secho(f" - {cert_name}")

    # this may no longer be used - remove if not needed
    cert_status = {'expired': expired,
                   'near_expiration': near_expiration,
                   'valid': valid}

    if LOCAL_DEBUG:
        click.secho("\nExcel Data to print (format 1):", fg="yellow")
        for row in excel_data:
            pprint(row)

        click.secho("\nExcel Data to print (format 2):", fg="yellow")
        pprint(excel_formatted_data)

    # 3 different formats for output have been tried
    # returning the current working one (format 2)
    return excel_formatted_data
    # return excel_data
    # return cert_status


def merge_snapshot_output(new_data, existing_data={}):
    """UC Snapshot Expiration Report
    Data merger to extract data and merge multiple snapshots together

    :param snapshots:   list of snapshots to merge
    :return:            JSON formatted data to be sent to Excel for printing
    """

    """
        Data format example:
            sample_data = {
                "Name": ["Alice", "Bob", "Charlie"],
                "Age": [25, 30, 35],
                "City": ["New York", "Los Angeles", "Chicago"]
            }
        Keys are Column Headers
        List attached is row data
    """

    LOCAL_DEBUG = False

    if LOCAL_DEBUG:
        click.secho('Existing data:', fg='yellow')
        pprint(existing_data)
        click.secho('New data:', fg='yellow')
        pprint(new_data)
        click.pause()

    # Merge data structures:
    # NOTE that this is tightly coupled right now with the data structure format.  Editing one means editing the other
    for k, v in new_data.items():
        if existing_data.get(k, None):
            # if key found, append all entries from new _data
            for entry in v:
                existing_data[k].append(entry)
        else:
            # if key not found, then initialize
            existing_data[k] = new_data[k]

    excel_data = existing_data

    return excel_data

# ####################################################################################

# individual report job class is responsible to just return formatted data
# it does not write to the excel spreadsheet at this time

# This is repeated and needs to placed in it's own modeule


# Report Class - first test with VOS backup
class ReportUCCertSnapshot(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None):           # TODO: do we change this to **kwargs
        pprint(vars)
        self.os_type = 'UC_CERT_API'

        self.excel_manager = excel
        self.metadata = metadata
        self.vars = vars
        self.tab_name = metadata.get('tab_name', 'MISSING_TAB')
        self.title = metadata.get('title', 'MISSING_TITLE')

        # running data objects
        self.data_collected = None
        self.data_parsed = None
        self.data_formatted = None
        self.status = {}

        # self.ip = vars.get('ip', '')
        # self.host = vars.get('host', '')
        # self.user = vars.get('user', '')
        # self.pwd = vars.get('pwd', '')
        self.cluster_type = vars.get('type', '')

        self.servers = vars.get('servers', {})
        # if self.servers == {}:
        #    self.servers = {'ip': self.ip,
        #                    'host': self.host,
        #                    'user': self.user,
        #                    'pwd': self.pwd,
        #                    'type': self.cluster_type
        #                   }
        self.verify_ssl = False

        # AXL_WSDL_URL=os.environ.get('AXL_WSDL_URL',f'ciscocucmapi/schema/{DEFAULT_AXL_VERSION}/AXLAPI.wsdl')
        # self.axl_wsdl_url = f'{AXL_SCHEMA_DIR}/{self.axl_version}/AXLAPI.wsdl'
        # self.commands = []

    def run(self):
        # TODO: This format may need to change.  This was the first attempt at a multi-server run
        #   The logic was do a server at a time (collect/parse/format)
        #   I believe this should change to collect all servers, then parse all servers, then format all servers
        #   Switching this, I think, will fit better with having those methods work as a strategy design in the future
        #   as well as make updating the data_xxxx attributes simpler

        LOCAL_DEBUG = False

        data = {}      # initialize final output
        report_status = {'success': True,
                         'message': ''
                         }

        # parse through the "servers" object to run on all devices
        click.secho('-' * 40, fg="blue")
        click.secho('Begin RUN for UC CERT REPORT:', fg="blue")
        click.secho(f'Servers in report: {len(self.servers)}', fg="blue")
        for server in self.servers:
            # connect and collect data
            click.secho('.' * 30, fg="blue")
            click.secho(f'Collecting data for server {server["ip"]}...', fg="blue")
            collected_data = self._collect_data(server)

            # ERROR Check to confirm we got data back for each server
            if collected_data is None or collected_data == {}:
                click.secho(f'ISSUE: Server {server["ip"]} did not return a snapshot.', fg="red")
                report_status['message'] += f"ISSUE retrieving snapshot from server {self.server['ip']}\n"
                report_status['success'] = False
            else:
                click.secho('Data retrieved but not validated yet.', fg="blue")

            # process raw output before formatting
            click.secho(f'PARSING data for server {server["ip"]}...', fg="blue")
            parsed_data = self._parse_data(collected_data)

            # ERROR Check to confirm we got data back for each server
            if parsed_data is None or parsed_data == {}:
                click.secho(f'ISSUE: Server {server["ip"]} data empty.', fg="red")
                report_status['message'] += f"ISSUE parsing snapshot from server {self.server['ip']}\n"
                report_status['success'] = False
            else:
                click.secho('Data parsed.', fg="blue")

            if LOCAL_DEBUG:
                pprint(parsed_data)
                click.pause()

            # Question: do we merge the parsed_data and then do one formatting
            #   OR do we perform multiple formats?

            # merge this into the existing final output
            # process structured data and format to Excel
            click.secho(f'Formating data for server {server["ip"]} and appending to return data....', fg="blue")
            data = self._format_data(parsed_data, data)

        click.secho('Returning data...', fg="blue")
        click.secho('End RUN for UC CERT REPORT:', fg="blue")
        click.secho('-' * 40, fg="blue")

        # this output is hte FORMATTED DATA without in between stages
        # TODO: Determine if this is how we want the running data to be done
        # TODO: we DO want to get the intermediate stages of this some how but we're not setup for it
        #       on this refactoring piece - needs more thought
        #   this report (where it has a server loop) may imply a change to the root strategy
        #   explore this....but for now, it's acceptable to skip data_collected and data_parse
        #   and just output the final self.data_formatted with all of the data merged.
        self.data_formatted = data

        status = 'success assumed'
        return status

    def _collect_data(self, server):
        """Make a VOS connection and run commands to retrieve all certificate information

        Purpose of this method is to "collect" but do minimal processing.

        :param server:  dictionary of server data from seed file

        :return:        DICT of all output.  KEYS are typically the cert/service name and VALUES are the raw
                            output received from commands.
        """

        LOCAL_DEBUG = False

        output = {}
        # for server in self.servers:
        uc_base_url = f"https://{server['ip']}"
        uc_auth = (server['user'], server['pwd'])  # Basic authentication credentials

        # Do we use test data or pull data fresh?
        if server.get('test', False):
            uc_cert_snapshot = load_uc_cert_snapshot_from_file(server['test_file'])
        else:
            # load
            uc_cert_snapshot = get_uc_cert_snapshot(uc_base_url, uc_auth, self.verify_ssl)

        if LOCAL_DEBUG:
            print(f'{server["host"]} RETURNED CERT_SNAPSHOT')
            pprint(uc_cert_snapshot)

        output[server['host']] = uc_cert_snapshot

        # Return ALL raw data
        return output

    def _parse_data(self, snapshots):

        LOCAL_DEBUG = False

        if LOCAL_DEBUG:
            pprint(snapshots)

        days_to_check = 30  # Days to consider as "near expiration"
        for server, uc_cert_snapshot in snapshots.items():

            # previous report
            # cert_status = process_uc_certificates(uc_cert_snapshot, days_to_check, format='silent')

            # new style report
            cert_status = process_uc_cert_expiration_report(uc_cert_snapshot, days_to_check, format='silent')

            if LOCAL_DEBUG:
                print(f'{server} snapshot:')
                pprint(cert_status)

            # TODO: This currently does a SINGLE snapshot.  It does NOT MERGE them so it is only returning
            # the last status returned.
        return cert_status

    def _format_data(self, new_data, existing_data=None):
        """Final report formatting.   This is broken out because we could want different
        types of reports from this data.  This last method is for formatting different
        reports.,
        """

        output = merge_snapshot_output(new_data, existing_data)

        return output

    def write_excel_tab(self, data=None, tab_name=None,
                        title_format=CellFormatTitle(),
                        header_format=CellFormatHeader(),
                        body_format=CellFormatFixed()):
        """first try of putting this inside the report job objct

        :param manager:  Excel manager object to write to
        :param tab_name:    this assumes 1 tab is being written

        :return status:     probably just a status response since the actions will happen in manager
        """

        status = None   # initialize local status
        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name

        if not self.excel_manager.workbook:
            status = 'ERROR: No active workbook'
            raise Exception("No active workbook. Create or open a spreadsheet first.")
        sheet = self.excel_manager.workbook.create_sheet(title=tab_name)

        headers = list(data.keys())
        for col_num, header in enumerate(headers, start=1):
            cell = sheet.cell(row=1, column=col_num, value=header)
            cell.font = header_format.font
            cell.fill = header_format.fill
            cell.alignment = header_format.alignment
            cell.border = header_format.border

        # Write data with formatting
        rows = zip(*data.values())
        for row_idx, row in enumerate(rows, start=2):  # Start from second row
            for col_idx, value in enumerate(row, start=1):
                cell = sheet.cell(row=row_idx, column=col_idx, value=value)
                cell.font = body_format.font
                cell.fill = body_format.fill
                cell.alignment = body_format.alignment
                cell.border = body_format.border

        # Auto-adjust column widths
        for col_num, col_cells in enumerate(sheet.columns, start=1):
            max_length = max(len(str(cell.value or "")) for cell in col_cells)
            sheet.column_dimensions[sheet.cell(row=1, column=col_num).column_letter].width = max_length + 2

        print(f"Added a new tab [{tab_name}] with formatted data to the workbook.")

        if not status:
            status = 'success assumed'
        return status
