# UCM Field Updater
#
# To be used with CLICK CSV reader
#
#
"""
This Class is written for BATCH PROCESSING for a CSV file.

Basic logic is:
    evaluate_csv_row() is called to determine what actions to take on the row
    Calling loop then performs those actions
    This could replace the single_csv_row() process since that is a subset of what it does
        but need to determine if this is too much overhead for that.

To make a new updater class
    CSV LOOP HAS EDITS
        -setup before loop needs to instantiate the UpdateClass instance
        -replace all references to this instance throughout the CSV LOOP
    The CLASS itself must publicly support
        expected_csv_headers()
        get_id()
        evaluate_csv_row()
        process_batch_of_csv_rows()
    Meat of work is in evaluate_csv_row() and process_batch_of_csv_rows()

"""
from pprint import pprint
import click
import logging
import time
# import csv
import os
import sys
# import yaml

from .report_config import ClickConfig
from .report_lib import ReportEngine


USE_TEST_DATA = False   # incorporate this or remove it


# ########################################
# Script supporting methods
# Not CLICK related
#


def get_current_time():
    """Utility function to return current time"""
    return time.time()


def initialize_logging(log_directory='logs', time_uid=ClickConfig.TIME_UID):
    # log_directory is subdirectory to place log files in (relative to working directory or full path)
    # calls global TIME_UID variable to add to log file names

    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_filename = sys.argv[0].split('.')[0] + '_LOGFILE_' + time_uid + '.txt'  # set LOGGING filename
    log_full_path = os.path.join(log_directory, log_filename)

    # define logging format
    # add "[%(threadName)-10s]" if program contains threads
    log_file_format = '[%(asctime)-15s][%(levelname)s][%(filename)s][%(funcName)s][%(lineno)s] %(message)s'
    log_console_format = '[%(asctime)-15s][%(levelname)-8s][%(funcName)s] %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=log_file_format, filename=log_full_path)  # global logging settings
    console_log = logging.StreamHandler()  # create logging handler for console
    console_log.setFormatter(logging.Formatter(log_console_format))  # set format for console logging
    console_log.setLevel(logging.INFO)  # set level of logging to console to INFO
    logging.getLogger('').addHandler(console_log)  # add the handler to the root logger

    return log_filename


class ClickMain(object):

    def __init__(self, ctx):
        # initialize ClickConfig object/class if it hasn't been done already
        default_config = ClickConfig()
        self.TIME_UID = default_config.TIME_UID
        self.DEFAULT_DELIMITER = default_config.DEFAULT_DELIMITER
        self.ctx = ctx      # Click context

        self.in_file = self.ctx.params.get('in_file', '')
        self.log_dir = self.ctx.params.get('log_dir', '')
        self.input_dir = self.ctx.params.get('input_dir', '')
        self.output_dir = self.ctx.params.get('output_dir', '')
        self.include = self.ctx.params.get('include', None)
        self.exclude = self.ctx.params.get('exclude', None)
        self.validate_only = self.ctx.params.get('validate_only', False)
        self.parse_seed = self.ctx.params.get('parse_seed', None)
        self.testing = self.ctx.params.get('testing', False)

        self.confirm_each_row = self.ctx.params.get('confirm_each_row', False)
        self.ignore = self.ctx.params.get('ignore', '#')

        # self.axl_version = self.ctx.params.get ('axl_version', default_config.DEFAULT_AXL_VERSION)
        # self.axl_wsdl_url = f"{default_config.DEFAULT_AXL_SCHEMA_DIR}/{self.axl_version}/AXLAPI.wsdl"       # directory hardwired here

    def run(self):
        """
        CLICK App to run.  CSV Processor with specific edits to all SpeedDials library
        """

        LOCAL_DEBUG = False

        # click.secho('* * * MASTER cli() method', fg='red')

        log_filename = initialize_logging(log_directory=self.log_dir, time_uid=self.TIME_UID)

        # ###############################################################
        #
        # Load seed/config file and parse.  Then report on next steps.
        #
        # ###############################################################

        # initialize report engine with SEED file
        report = ReportEngine(self.in_file)

        click.pause()
        if LOCAL_DEBUG:
            pprint(report.data)

        # parse_seed_file(config_data)
        self.outfile = report.data["customer"]["spreadsheet_name"]
        self.pwdfile = report.data["customer"]["password_file"]

        # TODO: update this method a bit
        # since the routine updates the source parameter it seems silly
        # to return it as well - make this cleaner so it's easier to understand
        resolved_data = report.resolve_env_vars(report.data)
        pprint(resolved_data)

        # TODO: Testing Report runner
        # initialization must be done AFTER env variables are resolved.
        # QUESTION: Should report_runner be stored as an instance attribute?
        #       in the report so it can be called by the object easier?
        runner = report._init_runner()
        click.secho('RUNNER: ', fg='red')
        pprint(runner)

        click.secho('\n* Current Option Settings:', fg='red')
        click.echo('\n')
        click.echo(f'log_dir:        {self.log_dir}')
        click.echo(f'input_dir:      {self.input_dir}')
        click.echo(f'output_dir:     {self.output_dir}')
        click.echo(f'File UID:       {self.TIME_UID}')
        click.echo('\n')
        click.echo(f'in_file:     {self.in_file}')
        click.echo(f'Customer:    {report.data["customer"]["customer_name"]}  ')
        click.echo(f'PWD File:    {self.pwdfile}  ')
        click.echo(f'Spreadsheet name: {self.outfile}')
        # click.echo(f'AXL Ver:     {self.axl_version}')
        # click.echo(f'user:        {self.user}')
        # click.echo(f'ip:          {self.ip}')
        click.echo('\n')
        click.pause('Press any key to continue...')
        click.echo()

        # If doing a validate/test connectivity then it should be announced up here
        # I'm thinking CLI() processes the data and gets thing ready to run
        # then we call another method which actually does the work
        # that chould keep it modular so we can reuse the code

        # ###############################################################
        #
        # Program Begins Below Here
        #
        # ###############################################################

        logging.debug("Beginning run of script")

        """
        This level selects the seed file for passing to the engine
        This script will initialize the reporting engine and control what options will run
            -reporting engine is initialized with a seed file
        From here we pick whether we want to
            -to test connectivity and report status
            -to just run the report and get the output
            -run against test data

        The report engine has the job of:
            -managing the seed file data
            -creating the spreadsheet manager
            -parsing through the seed data to figure out what to do
            -launching each individual report as needed
            -managing the final output and putting it in the report
            -save/close the excel spreadsheet
            -report back on status to the master script

        Each report will be its own object that have common calling methods
        Interface for common methods still being worked out
            -test connectivity
            -connect
            -collect data (could be multiple methods required)
            -process data
            -generate output data
            -generate formatting for Excel (but wil draw from standard config libraries)
            -generate excel ready data to write (this should be the output of the reporting object)
            -return data and status

        We will have a few 'reporting engines' which are shared code
            -each 'type' of access will probably have common code
            -Selenium, VOS CLI, standard APIs, SQL, netmiko, etc

        All reports will update a "status" object which reports back on succes of
            each stage in the report to allow the user to know if it was successful.

        """
        # TODO: Load password file data
        # Optional: Test connectivity

        # create Spreadsheet Manager
        # create standard TITLE page
        # TODO: move to self.output_dir/self.outfile for report

        # Report engine already instantiated with seed file
        # Now initialize the excel manager IF there is something to output
        full_out_file = os.path.join(self.output_dir, self.outfile)
        report.initialize_report(full_out_file)
        report.create_title_page(report.data)
        report.save_report()        # save but don't close

        # click.confirm('\nReady to proceed.  Perform updates', default=False, abort=True, prompt_suffix=' ? ', show_default=True, err=False)
        click.secho('*' * 80, fg='bright_yellow')

        total_start_time = get_current_time()

        # ###############################
        # Master FOR Loop
        #

        # This is the main RUN Loop
        # Need to put in a conditional for when this runs
        if True:
            for rep_job in runner:
                click.secho('*' * 80, fg='blue')
                start_time = get_current_time()

                click.secho('Starting next report...', fg='yellow')
                click.secho(f'Report tab: {rep_job.tab_name}', fg='yellow')

                # OPTIONAL confirm_each_row functionality to skip reports
                if self.confirm_each_row:
                    if click.confirm('Skip this report?'):
                        continue

                status = report._process_report(rep_job)

                click.secho(f'Report returned: {status}', fg='yellow')

                # TODO: Add a full STATUS output for the job here
                click.secho('Job status: ', fg='yellow')
                pprint(rep_job.status)

                report.save_report()        # save but don't close

                end_time = get_current_time()
                elapsed_time = end_time - start_time

                click.secho("\n\n")
                click.secho('Individual report completed.', fg='yellow')
                click.secho(f"Elapsed Time:   {elapsed_time} seconds", fg='yellow')

        #
        # End FOR loop
        # ###############################

        # Final Steps
        click.secho('*' * 80, fg='bright_yellow')
        # close report
        report.save_report()        # save but don't close
        report.close_report()

        # csv_out_file.close()  # close CSV writer file
        total_end_time = get_current_time()
        elapsed_time = total_end_time - total_start_time

        # TO ADD: count of lines, posibly a status count
        click.secho("\n\n")
        logging.info('Script completed.')
        logging.info(f"Elapsed Time:   {elapsed_time} seconds")
        logging.info(f'File UID:       {self.TIME_UID}')
        # logging.info('LOG file at:    ' + log_filename)
        logging.info(f'LOG file at:    {os.path.join(self.log_dir, log_filename)}')
        logging.info('Report File at: ' + full_out_file)

        # TODO: Do we print out status object here or earlier.
