import sys
import time


# May rename this class to something like DefaultConfig
class ClickConfig(object):
    """
    Default Config holding all defaults for program.

    Variables that need to be initialized once are done so in __init__ but stored as
    class variables so they are common.  This config can be called my multiple modules
    and it will not re-initialize those variables.
    """

    # Variables used by calling click module
    CLICK_ENV_PREFIX = 'UCREP'      # prefix for auto environment variables
    CLICK_PROGRAM_NAME = 'UC Report Generator'
    CLICK_PROGRAM_HEADER = ' - UC Report Generator'
    CLICK_PROGRAM_VERSION = '0.1.0'
    CLICK_PROGRAM_HELP_LINE = '''UC Report Generator utility

        '''
    CLICK_HELP_EPILOG = '''Help Page additional information:

        Here is where we can put in additional information on the help page for what needs to
        be done for this application.  This text appears at the end of the help page and will
        be printed across the terminal.

        To enter in a <return> for a new paragrph use two newlines to delimit the ending. Simply
        hitting return and continuing the text will not generate a paragraph and will be treated
        as a single run-on sentence.

        *** Using the CONFIG file option (-c, --config) ***

        The --c, --config option lets you enter the name of an environment configuration file to
        populate the required
        options for this script in a single command.  To create a config file, make an envionrment
        file with a meaninful suffix such as ".env.mycluster" and place in the "input" directory.
        When you call the config option enter "-c mycluster". The script
        will load up any environemnt variables found in the file .env.mycluster and override the existing
        environment as well as the default .env file.  You will NOT be prompted to fill in any required
        options that are in your config file.

        However, you can still override your config file by explicitly adding an option on the command-line.


        '''

    # variables for supporting Click command line options
    DEFAULT_IN_FILE = 'seed.yaml'
    DEFAULT_ENV_FILE = '.env'
    DEFAULT_LOG_DIR = 'logs'
    DEFAULT_IN_DIR = 'input'
    DEFAULT_OUT_DIR = 'output'
    DEFAULT_DEBUG = True
    DEFAULT_LOG = True
    DEFAULT_TEST_AUTH = True
    DEFAULT_CONFIRM_TO_START = True
    DEFAULT_CONFIRM_EACH_ROW = False

    DEFAULT_VALIDATE_ONLY = False
    DEFAULT_IGNORE_VALUE = '#'
    DEFAULT_DELIMITER = '/'
    DEFAULT_AXL_VERSION = "14.0"
    DEFAULT_AXL_SCHEMA_DIR = "ciscocucmapi/schema"

    DEFAULT_USE_TEST_DATA = False       # can this be removed

    # variables for supporting active script
    TIME_UID = 'UNINITIALIZED'
    CSV_OUT_FILENAME = 'UNINITIALIZED'

    # AXL_WSDL_URL = f"ciscocucmapi/schema/{DEFAULT_AXL_VERSION}/AXLAPI.wsdl"
    USE_TEST_DATA = False     # may want to make this a click parameter
    DEBUG = False            # if keeping - make a CLICK parameter - does this become VERBOSE

    def __init__(self):

        # variables that need to be initialized once

        if ClickConfig.TIME_UID == 'UNINITIALIZED':
            ClickConfig.TIME_UID = str(time.strftime("%Y%m%d-%H%M%S"))
        #    print('initializing self.TIME_UID')
        # else:
        #    print(f'{ClickConfig.TIME_UID} already exists')

        ClickConfig.CSV_OUT_FILENAME = sys.argv[0].split('.')[0] + '_CSVLOG_' + ClickConfig.TIME_UID + '.csv'

    # This data structure was started because it was thought it might be useful
    # At this point, it has not yet been used
    # if it turns out it isn't needed then remove

    SUPPORTED_REPORTS = [
        {'name': 'VOS_BACKUP_HISTORY',
         'os': 'VOS',
         'cluster_types': ['UCM', 'IMPS', 'CUC', 'CER', 'CCX'],
         'method': ['VOS_NETMIKO'],
         'status': 'WORKING',
        },
        {'name': 'VOS_BACKUP_STATUS',
         'os': 'VOS',
         'cluster_types': ['UCM', 'IMPS', 'CUC', 'CER', 'CCX'],
         'method': ['VOS_NETMIKO'],
         'status': 'WORKING',
        },
        {'name': 'UCM_LICENSE_SUMMARY',
         'os': 'VOS',
         'cluster_types': ['UCM'],
         'method': ['UCM_AXL'],
         'status': 'NOT STARTED',
        },
        {'name': 'UCM_LICENSE_USAGE',
         'os': 'VOS',
         'cluster_types': ['UCM'],
         'method': ['UCM_AXL'],
         'status': 'NOT STARTED',
        },
        {'name': 'UCM_TRUNK_LISTING',
         'os': 'VOS',
         'cluster_types': ['UCM'],
         'method': ['UCM_AXL', 'UCM_RIS'],  # either AXL/RIS or SELENIUM
         'status': 'NOT STARTED',
         # mimics output from CCMAdmin but does not have date of last state change
        },
        {'name': 'UC_CERT_SNAPSHOT',
         'os': 'VOS',
         'cluster_types': ['UCM', 'IMPS', 'CUC', 'CER'],    # only v14+ code, no CCX yet
         'method': ['UC_CERTAPI'],
         'status': 'NOT STARTED',
        },
        {'name': 'VOS_CERT_LISTING',
         'os': 'VOS',
         'cluster_types': ['CCX', 'UCM', 'IMPS', 'CUC', 'CER'],
         'method': ['VOS_NETMIKO'],
         'status': 'NOT STARTED',
         # PEM for own certs, decode-only for trusted certs
         # Required for CCX only
        },
        {'name': 'EWY_CERT_LISTING',
         'os': 'TANDBERG',
         'cluster_types': ['EWY-C', 'EWY-E', 'EWY'],
         'method': ['SELENIUM'],
         'status': 'NOT STARTED',
        },
        {'name': 'CDR_MONTHLY_SUMMARY',
         'os': 'VOS',
         'cluster_types': ['UCM'],
         'method': ['UNKNOWN'],
         'status': 'NOT STARTED',
        },
    ]
