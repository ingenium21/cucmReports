"""
Click CLI UC Reporter - Refactoring CLICK to it's own module and placing CONFIG object in library
"""

# standard imports for all click scripts
import click
import os
from dotenv import load_dotenv        # loading environment variable

# Imports for this specific script
from engine.report_config import ClickConfig
from engine.report_main import ClickMain

# Pull defaults from config object
config = ClickConfig()
CLICK_ENV_PREFIX = config.CLICK_ENV_PREFIX
CLICK_PROGRAM_NAME = config.CLICK_PROGRAM_NAME
CLICK_PROGRAM_HEADER = config.CLICK_PROGRAM_HEADER
CLICK_PROGRAM_VERSION = config.CLICK_PROGRAM_VERSION
CLICK_PROGRAM_HELP_LINE = config.CLICK_PROGRAM_HELP_LINE
CLICK_HELP_EPILOG = config.CLICK_HELP_EPILOG

DEFAULT_IN_FILE = config.DEFAULT_IN_FILE
# DEFAULT_QUERY_DIR = config.DEFAULT_QUERY_DIR
DEFAULT_ENV_FILE = config.DEFAULT_ENV_FILE
DEFAULT_LOG_DIR = config.DEFAULT_LOG_DIR
DEFAULT_IN_DIR = config.DEFAULT_IN_DIR
DEFAULT_OUT_DIR = config.DEFAULT_OUT_DIR
DEFAULT_DEBUG = config.DEFAULT_DEBUG
DEFAULT_LOG = config.DEFAULT_LOG
DEFAULT_TEST_AUTH = config.DEFAULT_TEST_AUTH
DEFAULT_CONFIRM_TO_START = config.DEFAULT_CONFIRM_TO_START
DEFAULT_CONFIRM_EACH_ROW = config.DEFAULT_CONFIRM_EACH_ROW
DEFAULT_IGNORE_VALUE = config.DEFAULT_IGNORE_VALUE
DEFAULT_VALIDATE_ONLY = config.DEFAULT_VALIDATE_ONLY
DEFAULT_AXL_VERSION = config.DEFAULT_AXL_VERSION


def load_env_file(ctx, param, filename='', input_dir=DEFAULT_IN_DIR):
    """
    Click method to load an environment file.

    For command line variables, they are in the format of PREFIX_COMMAND_VARIABLE.
    If not a command-line variables, then they do not require a prefix.

    This callback is called by the --config command-line option and is run
    as "eager" so that it occurs before other options are processed

    TODO: confirm click syntax and whether all paramters are needed or not

    :param ctx:      don't think this is needed but loading anyways
    :param param:    don't think this is needed but loading anyways
    :param filename: filename in local directory to load as an ENV file
                     If not found, program will search for ".env.FILENAME

    :return nothing

    TODO: Add on ability to also look in the IN_DIR for the ENV files
        This should do precedence of alloing the passed IN_DIR variable to override the
        default BEFORE this method is called.
        NEed to test this to allow for IN_DIR to be eager as well and to have it
        happen before config.

        If that works, then need to validate what to document if there is a looping
        of IN_DIR values.

    """

    # load default .env without override from input or local directory
    file_path_1 = os.path.join(input_dir, DEFAULT_ENV_FILE)
    file_path_2 = os.path.join(DEFAULT_ENV_FILE)
    if os.path.exists(file_path_1):
        load_dotenv(file_path_1)
    else:
        load_dotenv(file_path_2)

    # load --config file as "FILENAME" or as ".env.FILENAME"
    # Look in DEFAULT_IN_DIR first
    # override existing environment variables
    if isinstance(filename, str) and filename != '':
        file_path_1 = os.path.join(input_dir, filename)
        file_path_2 = os.path.join(input_dir, '.env.' + filename)
        file_path_3 = filename
        file_path_4 = '.env.' + filename

        if os.path.exists(file_path_1):
            load_dotenv(file_path_1, override=True)
            click.secho(f'Using configuration file "{file_path_1}" . . .', fg='red')
        elif os.path.exists(file_path_2):
            load_dotenv(file_path_2, override=True)
            click.secho(f'Using configuration file "{file_path_2}" . . .', fg='red')
        elif os.path.exists(file_path_3):
            load_dotenv(file_path_3, override=True)
            click.secho(f'Using configuration file "{file_path_3}" . . .', fg='red')
        elif os.path.exists(file_path_4):
            load_dotenv(file_path_4, override=True)
            click.secho(f'Using configuration file "{file_path_4}" . . .', fg='red')
        else:
            click.secho(f'WARNING: Environment file "{filename}" not found.  Using default values.', fg='red')


def old_load_env_file(ctx, param, filename=''):
    """
    Click method to load an environment file.

    For command line variables, they are in the format of PREFIX_COMMAND_VARIABLE.
    If not a command-line variables, then they do not require a prefix.

    This callback is called by the --config command-line option and is run
    as "eager" so that it occurs before other options are processed

    TODO: confirm click syntax and whether all paramters are needed or not

    :param ctx:      don't think this is needed but loading anyways
    :param param:    don't think this is needed but loading anyways
    :param filename: filename in local directory to load as an ENV file
                     If not found, program will search for ".env.FILENAME

    :return nothing
    """

    # load default .env without override
    load_dotenv(DEFAULT_ENV_FILE)

    # load --config file as "FILENAME" or as ".env.FILENAME"
    # override existing environment variables
    if isinstance(filename, str) and filename != '':
        if os.path.exists(filename):
            load_dotenv(filename, override=True)
            click.secho(f'Using configuration file "{filename}" . . .', fg='red')
        elif os.path.exists('.env.' + filename):
            load_dotenv('.env.' + filename, override=True)
            click.secho(f'Using configuration file ".env.{filename}" . . .', fg='red')
        else:
            click.secho(f'WARNING: Environment file "{filename}" not found.  Using default values.', fg='red')


# Single level CLI that does not have groups for SUBCOMMANDS
@click.command(help=CLICK_PROGRAM_HELP_LINE, epilog=CLICK_HELP_EPILOG)
@click.version_option(CLICK_PROGRAM_VERSION, prog_name=CLICK_PROGRAM_NAME)
@click.option('-c', '--config',
              type=click.Path(dir_okay=False),
              callback=load_env_file,
              is_eager=True,
              expose_value=False,
              help=f'env file to auto-load options, will override existing environment variables.  All variables should be prefixed with "{CLICK_ENV_PREFIX}_".',
              # default=DEFAULT_ENV_FILE,
              # show_default=True,
              )
# @click.option('--ip',
#              help="AXL IP or hostname",
#              required=False,
#              #prompt='AXL IP or Hostname',   # prompt if not populated
#              )
# @click.option('--user',
#              help="AXL Username",
#              required=False,
#              default='admin',
#              #prompt=True,                   # prompt if not populated
#              )
# @click.option('--pwd',
#              help="AXL Password",
#              required=False,
#              #prompt="AXL Password",         # prompt if not populated
#              hide_input=True,
#              )
@click.option('-i', '--in_file', "in_file",
              help="Input file",
              required=True,
              prompt=True,
              default=DEFAULT_IN_FILE,
              show_default=True,
              )
@click.option('--logdir', "log_dir",
              help='log directory',
              default=DEFAULT_LOG_DIR,
              show_default=True,
              )
@click.option('--indir', "input_dir",
              hidden=True,
              help='Input directory for .env and CSV files',
              default=DEFAULT_IN_DIR,
              show_default=True,
              )
@click.option('--outdir', "output_dir",
              help='Output directory for CSV files',
              default=DEFAULT_OUT_DIR,
              show_default=True,
              )
@click.option('--include',
              help='Only execute on these reports',
              # default=DEFAULT_INCLUDE,
              # show_default=True,
              )
@click.option('--exclude',
              help='Exclude these report from execution',
              # default=DEFAULT_EXCLUDE,
              # show_default=True,
              )
@click.option('-v', '--validate_only',
              is_flag=True,
              help='Validate connectivity',
              default=DEFAULT_VALIDATE_ONLY,
              show_default=True,
              )
@click.option('-v', '--parse_seed',
              is_flag=True,
              help='Parse and print out seed file',
              # default=DEFAULT_VALIDATE_ONLY,
              # show_default=True,
              )
@click.option('-t', '--testing',
              is_flag=True,
              help='Use test data if available',
              default=False,
              show_default=True,
              )
# TODO: remove unused items
#   possibly add flag for status
#   should confirm_each_row become something like 'ignore errors' or 'stop_on_error'
#   how do we want to do 'verbose' mode?
#
@click.option('--ignore',
              help='Ignore character',
              default=DEFAULT_IGNORE_VALUE,
              show_default=True,
              )
@click.option('-r', '--confirm_each_row',
              is_flag=True,
              help='Confirm each row',
              default=DEFAULT_CONFIRM_EACH_ROW,
              show_default=True,
              )
@click.pass_context
def cli(ctx: click.Context, in_file, log_dir, input_dir, output_dir,
        include, exclude, validate_only, parse_seed, testing,
        ignore, confirm_each_row):            # master CLICK application
    """
    Entry point for CLI script.  ENV file has already been loaded and user
    has been prompted to confirm any input.

    Pass context and control to main program imported from another module.
    Individual click variables 'could' be passed seperately.  We are passing them currently
    in the context (ctx) object and they are accessible in the ctx.params dictionary object.
    """

    click_program = ClickMain(ctx)
    click_program.run()


# ########################################################################


if __name__ == '__main__':

    # print out banners at start of script
    click.echo('\n\n')
    click.echo(click.style('*-' * 30, fg='red'))
    click.echo(click.style(CLICK_PROGRAM_NAME, fg='red'))
    click.echo(click.style(CLICK_PROGRAM_HEADER, fg='red'))
    click.echo()

    # call CLICK top-level method with auto_envvar
    cli(auto_envvar_prefix=CLICK_ENV_PREFIX)
