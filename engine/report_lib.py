#
# UCM Field Updater class
# Designed to work with Click and CSV Processor module
# AXL from ciscocucmapi Version


# add update Elapsed Time: 787.5150198936462 seconds [13m7s]
# update Elapsed Time: 644.9121677875519 seconds [10m44s] (saved 143 seconds on 2000 items)
# GET clean up of vendorConfig:  Elapsed Time: 548.6794240474701 seconds [9m8s] (save 96 seconds)
#          GET is at 218 actions a minute (average....need to see time for line vs phone_line (phone line will be more))
# 1000 items down as single was 234seconds  (4 minutes or 250 rows/minute) through VPN
# 1000 items with 2 per update was 110 seconds through VPN

"""
BATCH processing for UpdateField
Basing this on speeddials_lib

LESSONS LEARNED:
-some methods do not need to change between Classes.  could we put these
 into their own parent Class to signify they don't need editing?
-then have a child class prepopulated with common settings to make it clear
 what needs to be updated?

"""

from pprint import pprint
import click
import os
import logging
import yaml

from engine.report_config import ClickConfig
from lib_excel import ExcelManager
from lib_vos import VOSBackupHistory, VOSBackupStatus, VOSCertListing
from rep_license import ReportLicenseStatus, ReportLicenseUsage, ReportUnassignedDevices
from lib_uc_cert import ReportUCCertSnapshot
from rep_ucm_cdr import ReportUcmCdrMonthly


class ReportEngine(object):
    def __init__(self, config_file='seed.yaml'):
        """
        :param ucm:             authenticated instance of UCMAXLConnector
        :param delimiter:       delimter to use for splitting field names for nested fields
        :param validate_only:   validate IDs or actually process data
        :param backout_file:      option to right a backout YAML file of all found data
        :param ignore:          ignore character to keep field from being used in choice
        """

        # TODO: Click parameters are NOT getting into this object yet
        # Either they need to be passed in __init__ or will need to be sent on each command
        # ex: input_dir and output filename may change at command line.
        # Need to decide how we want this structured.

        self.config_file = config_file
        # self.EXPECTED_FIELDNAMES = ['status', 'type', 'name', 'pattern', 'partition', 'filter', 'fieldToChange', 'newValue']
        # need to add 'filter' this fieldnames at some point to support routePattern/transPattern/transformations

        # self.working_id = {'type': 'FIRST'}
        self.TESTING = False
        self.VERBOSE = True
        self.VALIDATE_ONLY = False

        self.full_file_path = self.find_seed_file(self.config_file)
        self.data = self.load_yaml(self.full_file_path)             # RAW Processed SEED File

        self.excel = ExcelManager()         # creates an openpyxl ExcelManager Object

    def find_seed_file(self, filename='', input_dir=ClickConfig.DEFAULT_IN_DIR, suffix='yaml'):

        # Search for and load the appropriate query template
        #   -) try "INPUT_DIR/FILENAME" (w/ w/o suffix)
        #   -) try "working_dir/FILENAME" (w/ w/o suffix)  [does not work for docker runs]
        #   -) try "QUERY_DIR/FILENAME" (w/ w/o suffix)

        LOCAL_DEBUG = False

        directory_list = [input_dir, '.']   # ordered list of places to look

        # query through directories to find the first instance of the filename
        for d in directory_list:
            if LOCAL_DEBUG:
                click.secho(f'Looking in dir: {d}', fg='red')

            # find filename exactly
            if os.path.isfile(d + '/' + filename):
                found_file = d + '/' + filename
                if LOCAL_DEBUG:
                    print(f' found in {d} without altering suffix')
                return found_file
            # find with suffix added
            elif os.path.isfile(d + '/' + filename + '.' + suffix):
                found_file = d + '/' + filename + '.' + suffix
                if LOCAL_DEBUG:
                    print(' found in {d} by adding default suffix')
                return found_file

        logging.error(f'SQL Query file "{filename}" NOT found in any location.')
        return ''

    @staticmethod
    def load_yaml(file_path):
        """
        Loads a YAML file.

        :param file_path (str): The path to the YAML file.
        """
        data = None

        try:
            with open(file_path, 'r') as yaml_file:
                data = yaml.safe_load(yaml_file)  # Use safe_load for security
        except FileNotFoundError:
            print(f"Error: The file '{file_path}' was not found.")
        except yaml.YAMLError as exc:
            print(f"Error parsing YAML file: {exc}")
        return data

    @staticmethod
    def _resolve_secured_variable(str, prompt="Enter value: "):
        """
        str:    String value for variable typically beginning with ".env." from YAML file
        return: the environemnt variable after stripping '.env.' off the start of the string
        TODO: Do we actually want to just return NONE for this if not found?

        NOTE: need to determine 'placement' for this method because it is used in other classes
        This might be best in a "helper" module
        Code is also still in ucmprov.py module
        """
        if str[:5] == ".env.":
            var_name = str[5:]
            str = os.environ.get(var_name, 'NOT_FOUND_IN_ENV')

        if str in ['NOT_FOUND_IN_ENV', 'PROMPTME', 'PROMPT_ME', 'PROMPT']:
            click.echo('-*' * 30)
            if str in ['NOT_FOUND_IN_ENV']:
                click.secho(f'-*- Did not find env variable: {var_name}', fg='bright_red')
            str = input(prompt)
            click.echo('-*' * 30)

        return str

    def resolve_env_vars(self, data, env_prefix='.env.'):
        """
        Recursively processes a nested dictionary or list to resolve environment variables references.

        Public method to resolve .env.XXXX references against current environment.  If system cannot
        resolve them then it will STOP processing and prompt the user for input.

        This does not do a deepcopy.  If a copy is needed it must be done before calling this routine.

        :param data:        dictionary object (may have nested lists) to parse
        :param env_prefix:  the prefix to search for

        :return:            original data object - this is a permanent edit.
        """

        # TODO: update this method a bit
        # since the routine updates the source parameter it seems silly
        # to return it as well - make this cleaner so it's easier to understand

        if isinstance(data, dict):
            # Process each key-value pair in the dictionary
            for key, value in data.items():
                data[key] = self.resolve_env_vars(value)
        elif isinstance(data, list):
            # Process each item in the list
            for i in range(len(data)):
                data[i] = self.resolve_env_vars(data[i])
        elif isinstance(data, str) and data.startswith(env_prefix):
            # Apply the transform function if the value is a string starting with '.env.'
            return self._resolve_secured_variable(data)

        return data  # Return the processed data

    # create initial excel report and add title page
    def initialize_report(self, out_file_path):
        self.excel.create_spreadsheet(out_file_path)

    def save_report(self):
        self.excel.save()

    # close and save
    def close_report(self):
        self.excel.close()

    def create_title_page(self, data):
        """ Standard routine to print the TITLE TAB within a spreadsheet

        Writes output to self.excel which should already be initialized.

        """
        sample_data = {
            "cust_data": data.get('customer', {}),
            "meta_data": data.get('meta', {}),
            "Name": ["Alice", "Bob", "Charlie"],
            "Age": [25, 30, 35],
            "City": ["New York", "Los Angeles", "Chicago"],
        }
        """
        Title
        Customer Name
        Date of Report
        Possible Equipment listing (what clusters do they have)
        Optional: listing of tabs created (make this dynamically)
        """
        click.secho('Creating Excel title page...', fg='yellow')
        self.excel.add_tab_with_formatted_data('TITLE', sample_data)

    def _init_runner(self):
        """Initialize report runner with command objects

        Instantiates all RerpotTempate() objects that it finds in the seed file and places them
        in a LIST that is returned. This list is the runner of all "command objects" that can be processed.

        :param:
        :return:    list of ReportTemplateCommmand objects
        """

        """
        This method will extract the IF/THEN treein process_job() down to a single method
        The IF/THEN tree will only happen at the initial stage...after that all reports will function
        using the same abstract interface.

        seed file is already loaded.
        Pull up all report_jobs from the seed file
        for each report in report_jobs:
            instantiated the appropriate report object using it's subclass
            add to the report_runner
        return the report_runner as a LIST
        """

        LOCAL_DEBUG = False
        report_runner = []

        click.secho('Initializing report runner...', fg='yellow')

        # set counter for REPORT NUMBER
        count = 0
        safe_to_add = True

        # TODO: add counter  - draw from other code for update-field
        for job in self.data.get('report_jobs', []):
            # read report data
            if LOCAL_DEBUG:
                pprint(job)

            vars = job.get('vars', {})
            metadata = job.get('metadata', {})

            report_name = job.get('name', '')                   # from root of job
            engine = metadata.get('engine', '')
            tab_name = metadata.get('tab_name', 'MISSING')
            title = metadata.get('title', 'MISSING')           # may want to add this
            version = metadata.get('version', '')
            
            click.secho(f'Initializing report: {count} - {report_name}...', fg='yellow')

            # TODO: Excel formatting needs to be initialized - probaby during this process
            #   How are we going to do that

            # INVOKE Report job by looking at request
            # Launch appropriate method to instantiate report object
            if engine in ['backup_history']:
                rep = VOSBackupHistory(vars, metadata=metadata, excel=self.excel)
                click.secho('BACKUP HISTORY using VOS CLI', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['backup_status']:
                rep = VOSBackupStatus(vars, metadata=metadata, excel=self.excel)
                click.secho('BACKUP STATUS using VOS CLI', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['VOS_CERT_LISTING']:
                rep = VOSCertListing(vars, metadata=metadata, excel=self.excel)
                click.secho('CERT LISTING using VOS CLI', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['UCM_LICENSE_STATUS']:
                rep = ReportLicenseStatus(vars, metadata=metadata, excel=self.excel)
                click.secho('UCM Smart License Status', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['UCM_LICENSE_USAGE']:
                rep = ReportLicenseUsage(vars, metadata=metadata, excel=self.excel)
                click.secho('UCM Smart License Usage', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['UCM_LICENSE_UNASSIGNED_DEVICES']:
                rep = ReportUnassignedDevices(vars, metadata=metadata, excel=self.excel)
                click.secho('UCM Licensing - Unassigned Devices', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['UC_CERT_API']:
                rep = ReportUCCertSnapshot(vars, metadata=metadata, excel=self.excel)
                click.secho('UCM CERT Snapshot', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['UCM_CDR_SELENIUM']:
                rep = ReportUcmCdrMonthly(vars, metadata=metadata, excel=self.excel)
                click.secho('UCM CDR Monthly Report (selenium)', fg='magenta')
                click.secho(f'TAB NAME: {tab_name}', fg='magenta')
                count += 1
            elif engine in ['vos']:
                pass
                # response =  vos_report(vars, metadata=metadata, excel=self.excel)
            elif engine in ['netmiko']:
                pass
                # response = netmiko(vars, metadata=metadata, excel=self.excel)
            elif engine in ['cert_api']:
                pass
                # response = cert_api(vars, metadata=metadata, excel=self.excel)
            else:
                # NOTE: For this runner the default case needs to be different
                #   determine what we want to do here.  This code is currently from old method.
                # receive data
                # determine if good data returned or error
                click.secho('REPORT NOT INITIALIZED. NO ENGINE FOUND.', fg='red')
                safe_to_add = False
            # now append it to the runner_list
            if safe_to_add:
                report_runner.append(rep)
            safe_to_add = True
        click.secho('Report runner created.', fg='magenta')
        click.secho(f'Length: {len(report_runner)}', fg='magenta')
        for r in report_runner:
            print(r.tab_name)

        # TODO: need a status that says how many items found in seed/report_jobs
        #   and how many were processed into jobs.
        #   IF they are not equal, then show an ERROR message to alert that the seed file
        #   was not fully processed into actionable objects.

        # QUESTION: Should this report_runner LIST be stored in the report instance
        #   rather than being returned?

        return report_runner

    def _process_report(self, report_command, test_only=False):
        """Process a report command object and return response

        NEW processor - in progress
        still working out how report's meta infomration is pulled for this
        at this point, when the report_command is instantiated I don't think that is being entered...only the vars data
        """

        click.secho('Processing a report and writing new tab', fg='yellow')

        tab_name = report_command.metadata.get('tab_name', 'MISSING_TAB_NAME')
        title = report_command.metadata.get('title', 'MISSING_TITLE')

        click.secho(f'TITLE: {title}', fg='magenta')
        click.secho(f'TAB NAME: {tab_name}', fg='magenta')

        # run report and format data
        status = report_command.run()
        pprint(status)

        # TODO: Make writing of report contingent on status (once status has valid data)
        # write to the excel file and return status
        status = report_command.write_excel_tab()
        pprint(status)

        return status


def main():
    file_path = "seed.yaml"
    report = ReportEngine(file_path)
    pprint(report.data)


# Example Usage
if __name__ == "__main__":
    main()
