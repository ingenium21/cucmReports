# THIS IS WORKING WITH LIMITED FUNCTIONALITY
#
# Using a GENERIC driver for linux to get things started
#
# NOTE: attempting to set prompt terminator BEFORE
import os
os.environ["NETMIKO_LINUX_PROMPT_PRI"] = ":"

from netmiko.linux.linux_ssh import LinuxSSH
from netmiko.ssh_dispatcher import CLASS_MAPPER
from netmiko import ConnectHandler
import textfsm
import time
import logging
from pprint import pprint
import click

from rep_base import ReportTemplate
from lib_excel import CellFormatFixed, CellFormatBody, CellFormatHeader, CellFormatTitle


DEFAULT_PROMPT = 'admin:'
LINUX_PROMPT_PRI = ':'
LINUX_PROMPT_ALT = '#'

"""
admin:
set cli pagination off
Press <enter> for 1 line, <space> for one page, or <q> to quit

"""


"""
These are the entries in the linux_ssh.py library.
If the ENV is updated BEFORE the linux_ssh.py library is loaded this should change the values.

LINUX_PROMPT_PRI = os.getenv("NETMIKO_LINUX_PROMPT_PRI", "$")
LINUX_PROMPT_PRI = os.getenv("NETMIKO_LINUX_PROMPT_ALT", "#")
LINUX_PROMPT_PRI = os.getenv("NETMIKO_LINUX_PROMPT_ROOT", "#")
"""


def parse_output_with_textfsm(command_output, template_path):
    """
    Parses the command output using a TextFSM template.

    Args:
        command_output (str): The command output to parse.
        template_path (str): The path to the TextFSM template.

    Returns:
        list: A list of dictionaries containing the parsed data.
    """
    with open(template_path) as template_file:
        fsm = textfsm.TextFSM(template_file)
        parsed_output = fsm.ParseText(command_output)
        
        # Create a list of dictionaries
        result = []
        for row in parsed_output:
            result.append(dict(zip(fsm.header, row)))
            
        return result

# Report Class - first test with VOS backup
class VOSBackupHistory(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None):           # TODO: do we change this to **kwargs
        pprint(vars)
        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.os_type = 'VOS'
        self.cluster_type = vars.get('type', '')
        self.command = 'utils disaster_recovery history backup'

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

        # process data and format to Excel
        status = self._format_data(self.data_collected)

        status = 'success'
        return status

    def _collect_data(self):
        """Make a VOS connection and run a single command for output
        """
        LOCAL_DEBUG = True

        c = NetmikoVOS(self.ip, self.user, self.pwd)
        c.connect()

        # testing code to determine if connection succeeded
        # this would be used by STATUS reporting 
        if LOCAL_DEBUG:
            print('Do we have a connected object?')
            print(type(c))
            print(type(c.connection))
            if type(c.connection) is None:
                click.secho(f'ERROR: No connection made by netmiko', fg='red')
                click.secho(f'ERROR: c.connection is None', fg='red')

        self.data_collected = c.connection.send_command(self.command, expect_string=DEFAULT_PROMPT)
        c.disconnect()

        if LOCAL_DEBUG:
            print(self.data_collected)

        status = 'success assumed'
        return status

    def _format_data(self, data=None):
        # TODO: this should be a textFSM output manipulation
        # NOT WORKING

        LOCAL_DEBUG = False

        if False:
            template_path = f'textFSM/vos_{self.command.replace(" ", "_")}.textfsm'
            parsed_data = parse_output_with_textfsm(output, template_path)
            if LOCAL_DEBUG:
                print(f"Parsed data for '{self.command}':\n{parsed_data}\n")
            data = parsed_data
        
        if not data:
            data = self.data_collected

        # write to instance attribute
        # NOTE: Current return format is a DICT with the output as a string
        self.data_formatted = {'data': data}

        status = 'success'
        return status

    def write_excel_tab(self, data=None, tab_name=None, title=None,
                       title_format=CellFormatTitle(),
                       header_format=CellFormatHeader(),
                       body_format=CellFormatBody()):
        """
        redirect to add_tab_with_formatted_data for now
        """
        LOCAL_DEBUG = False
        # accept overrides for data, tab_name, and title if they are passed as parameters
        # otherwise, use defaults instance variables:
        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name
        
        if not title:
            title = self.title
        
        if LOCAL_DEBUG:
            click.secho(f'data before writing', fg='red')
            click.secho('DATA_COLLECTED', fg='yellow')
            pprint(self.data_collected)
            click.secho('DATA_PARSED', fg='yellow')
            pprint(self.data_parsed)
            click.secho('DATA_FORMATTED', fg='yellow')
            pprint(self.data_formatted)
        
        # NOTE: this data has {'data', 'string'} for now.  See if this is what we do long-term

        self.excel_manager.add_tab_by_string(tab_name, data.get('data',''), title=title,
                        title_format=CellFormatTitle(),
                       body_format=CellFormatFixed())
        
        status = 'assume written'
        return status

# Report Class - first test with VOS backup
class VOSBackupStatus(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None):           # TODO: do we change this to **kwargs
        pprint(vars)
        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.os_type = 'VOS'
        self.cluster_type = vars.get('type', '')
        self.command = 'utils disaster_recovery status backup'

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

        # process data and format to Excel
        status = self._format_data(self.data_collected)

        return status

    def _collect_data(self):
        """Make a VOS connection and run a single command for output
        """
        LOCAL_DEBUG = True

        if LOCAL_DEBUG:
            print(f'ip:   {self.ip}')
            print(f'user: {self.user}')
            print(f'pwd:  {self.pwd}')

        c = NetmikoVOS(self.ip, self.user, self.pwd)
        c.connect()

        # testing code to determine if connection succeeded
        # this would be used by STATUS reporting 
        if LOCAL_DEBUG:
            print('Do we have a connected object?')
            print(type(c))
            print(type(c.connection))
            if type(c.connection) is None:
                click.secho(f'ERROR: No connection made by netmiko', fg='red')
                click.secho(f'ERROR: c.connection is None', fg='red')
                
        self.data_collected = c.connection.send_command(self.command, expect_string=DEFAULT_PROMPT)
        c.disconnect()

        if LOCAL_DEBUG:
            print(self.data_collected)

        status = 'assume success'
        return status

    def _format_data(self, data=None):
        """Returning as STRING for now but formatting as a DICT for consistentcy.
        May change that in future.
        """
        # TODO: this should be a textFSM output manipulation
        # NOT WORKING
        LOCAL_DEBUG = False

        if not data:
            data = self.data_collected

        if False:        # not using textFSM at this time
            template_path = f'textFSM/vos_{self.command.replace(" ", "_")}.textfsm'
            parsed_data = parse_output_with_textfsm(output, template_path)
            if LOCAL_DEBUG:
                print(f"Parsed data for '{self.command}':\n{parsed_data}\n")
            data = parsed_data

        self.data_formatted = {'data': data}
        # NOTE: Current return format is a DICT with the output as a string

        status = 'success assumed'
        return status

    def write_excel_tab(self, data=None, tab_name=None, title=None,
                       title_format=CellFormatTitle(),
                       header_format=CellFormatHeader(),
                       body_format=CellFormatFixed()):
        """
        redirect to add_tab_with_formatted_data for now
        """
        LOCAL_DEBUG = False

        # accept overrides for tab_name and title if they are passed as parameters
        # otherwise, use defaults from metadata:
        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name
        
        if not title:
            title = self.title

        if LOCAL_DEBUG:
            click.secho(f'data before writing', fg='red')
            click.secho('DATA_COLLECTED', fg='yellow')
            pprint(self.data_collected)
            click.secho('DATA_PARSED', fg='yellow')
            pprint(self.data_parsed)
            click.secho('DATA_FORMATTED', fg='yellow')
            pprint(self.data_formatted)
            click.secho('DATA_TO_USE', fg='yellow')
            pprint(self.data)

        self.excel_manager.add_tab_by_string(tab_name, data.get('data',''), title=title,
                        title_format=title_format,
                       body_format=body_format)

        status = 'success assumed'
        return status

# Report Class
# NOTE: This report was being made for Pre-UC14 systems.  UCC12 is all that is left
# this report is low priority becasue CCX15 is coming out this spring
class VOSCertListing(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None):           # TODO: do we change this to **kwargs
        pprint(vars)
        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.os_type = 'VOS'
        self.cluster_type = vars.get('type', '')
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
        status= self._collect_data()

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
        output = {}
        c = NetmikoVOS(self.ip, self.user, self.pwd)
        c.connect()
        # Get lists of certificates and services (show cert list own|trust)
        own_output = c.connection.send_command("show cert list own", expect_string=DEFAULT_PROMPT)
        output['own_output'] = own_output
        print(own_output)
        trust_output = c.connection.send_command("show cert list trust", expect_string=DEFAULT_PROMPT)
        print(trust_output)
        output['trust_output'] = trust_output

        # Split OWN output into a LIST and then parse them for output
        # Own_output should split first for lines (\n) and then by "/"
        # Result is a LIST of all services for which there are certificates
        own_list= []
        lines = own_output.split('\n')
        for line in lines:
            parts = line.split('/')
            if parts[0] == '':
                continue
            own_list.append(parts[0])
        output['own_list'] = own_list   # add the parsed list to output so we don't have to do it again
        pprint(own_list)

        # Split TRUST List out then parse them for output
        # trust_output should split first for lines (\n) and then by ":"
        # Result is a LIST of all services/cert_names.pem for which there are certificates
        trust_list= []
        lines = trust_output.split('\n')
        for line in lines:
            parts = line.split(':')
            if parts[0] == '':
                continue
            trust_list.append(parts[0])
        output['trust_list'] = trust_list   # add the parsed list to output so we don't have to do it again
        pprint(trust_list)

        # Collect OWN PEM files by parsing through own_list
        for cert in own_list:
            own_output = c.connection.send_command(f"show cert own {cert}", expect_string=DEFAULT_PROMPT)
            output[cert] = own_output
            pprint(own_output)
        
        # collect trust certs (decoded...no PEM) by parsing through trust_list
        for cert in trust_list:
            trust_output = c.connection.send_command(f"show cert trust {cert}", expect_string=DEFAULT_PROMPT)
            output[cert] = trust_output
            pprint(trust_output)
    
        c.disconnect()

        # Return ALL raw data
        return output

    def _parse_data(self, raw_output=None):
        """ Takes a DICTIONARY of outputs and parses through them
        
        :return:    DICT that is better formatted that can be then manipulated into a report
        """
        # TODO: this should be a textFSM output manipulation
        # NOT WORKING
        LOCAL_DEBUG = False

        if not raw_output:
            raw_output = self.data_collected

        if LOCAL_DEBUG:
            pprint(raw_output)

        # process Trust erts
        #   process thorugh textFSM to pull out data that is needed
        #   reformat into a new data structure
        # Process OWN Certs 
        #   option to treat same as TRUST certs and only grab some data
        #   OR pull out PEM file using textFSM nad then run through cryptography library
        #   NOTE: will start with what TRUST does but using PEM/cryptography should be preferred 
        #       since this is the parsing function

        # extract the list of KEYS for own/trust certs created during data collection
        own_list = raw_output['own_list']
        trust_list = raw_output['trust_list']

        # start createiong of NEW_DICT that will be returned
        # TODO/NOTE: Do we make a new structure for this data OR do we try to make
        # it look like the SNAPSHOT data structure to keep things equivalent?
        new_dict = {}
        new_dict['own_list'] = own_list
        new_dict['trust_list'] = trust_list

        if LOCAL_DEBUG:
            print(f'OWN CERTS: ')
            pprint(own_list)
            print(f'TRUST CERTS:')
            pprint(trust_list)
        
        # Process all trust certs through textFSM
        for tcert in trust_list:
            click.secho(f'Parsing certificate {tcert}...', fg='yellow')
            output = raw_output[tcert]
            command = 'vos_show_cert_trust'
            template_path = f'./textFSM/{command}.textfsm'
            parsed_data = parse_output_with_textfsm(output, template_path)
            if LOCAL_DEBUG:
                print(f"Parsed data for '{command}':\n{parsed_data}\n")
            new_dict[tcert] = parsed_data

        # Process all own certs through textFSM
        for own_cert in own_list:
            click.secho(f'Parsing certificate {tcert}...', fg='yellow')
            output = raw_output[own_cert]
            command = 'vos_show_cert_trust'       # MAY NEED TO CHANGE THIS
            template_path = f'./textFSM/{command}.textfsm'
            parsed_data = parse_output_with_textfsm(output, template_path)

            # TODO: Either add on PEM extration OR run data through twice to get PEM

            if LOCAL_DEBUG:
                print(f"Parsed data for '{command}':\n{parsed_data}\n")
            new_dict[own_cert] = parsed_data
        
        # NOTE: at this point I have data that I can work with but not all in a good foramt
        #   date stamps could be converted to UTC for easier working with them
        #   they are NOT SORTED by expired yet if we want that
        #   I'm thinking we should add on PEM cert for those that have it.

        # write back to instance variable
        self.data_parsed = new_dict

        status = 'success assumed'
        return status
    
    def _format_data(self, output=None):
        """Final report formatting.   This is broken out because we could want different
        types of reports from this data.  This last method is for formatting different
        reports.
        
        """
        if not output:
            output = self.data_parsed

        self.data_formatted = output

        return 'success'

    def write_excel_tab(self, data=None, tab_name=None,  
                       title_format=CellFormatTitle(),
                       header_format=CellFormatHeader(),
                       body_format=CellFormatBody()):
        """
        redirect to add_tab_with_formatted_data for now
        """

        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name

        self.excel_manager.add_tab_with_formatted_data(tab_name, data,
                        header_format=CellFormatHeader(),
                        body_format=CellFormatBody())
        
        return 'success assumed'


class NetmikoVOS(object):
    # this is not a NetMiko sub-class.  It is a helper class
    # for establishing a netmiko connection to VOS
    # as a generic device type
    # just helping with handling the prompts
    #
    # use .connect() to perform the connection/login/and wait for first prompt
    # then use x.connection.send_command() to send our commands
    # .disconnect() when done.

    def __init__(self, ip, username, password):
        self.connection = None
        # Define the device configuration
        self.device = {
            "device_type": "generic",  # Matches the registered custom class
            #"device_type": "cisco_vos",
            "host": ip,
            "username": username,
            "password": password,
            #"global_delay_factor": 10,
            #"timeout": 30
        }

    def connect(self):
        # Establish Connection
        try:
            self.connection = ConnectHandler(**self.device)  # This now uses CustomVOSSSH
            print("Connection Successful!")
            self.connection.base_prompt = "admin:"  # Adjust the base prompt
            print(f'entered base_prompt: {self.connection.base_prompt}')
            #connection.set_base_prompt()  # Force Netmiko to use this
            #print('set base prompt')
            #time.sleep(30)

            # what find_prompt does is send a newline and then return whatever the prompt is
            # this should work great AFTER we have a prompt working but not before.
            found_prompt = self.connection.find_prompt()
            
            wait = 0        # closer to TRIES as currently written
            timeout = 5

            # check for 'timeout' seconds to find the appropriate prompt.
            # TODO : redo this logic to something cleaner.
            while (found_prompt != self.connection.base_prompt) and (wait <= timeout):
                time.sleep(1)
                wait +=1
                print(wait)
                found_prompt = self.connection.find_prompt()     # NOTE: this takes time so this isn't just a WAIT multiplier - redo
                
            if wait >= timeout:
                print('TIMEOUT')

            print("Detected Prompt:", self.connection.find_prompt())

            # now lets try some commands that should respond fairly quickly without errors
            #
            # NOTE: I have NOT entered any conditions for other types of prompts yet so ANYTHING
            # will cause these to fail

            # immediately shut off pagination
            # removes case that we might get :: Press <enter> for 1 line, <space> for one page, or <q> to quit
            #
            output = self.connection.send_command('set cli pagination off', expect_string=DEFAULT_PROMPT)
            print(output)

        except Exception as e:
            print(f"Error during connection: {e}")
            pass

            # TODO: Needs better error handling and passing up to calling method

    def disconnect(self):
        self.connection.disconnect()
        

# Define the custom class
class CustomVOSSSH(LinuxSSH):
    #def session_preparation(self):
    #    """Override session preparation to match 'admin:' prompt."""
    #    self._test_channel_read(pattern=r"admin:")  # Match the correct prompt
    #    self.set_base_prompt()                     # Set the detected prompt as base

    def find_prompt(self):
        prompt = super().find_prompt()
        if not prompt.endswith(':'):
            raise ValueError("Unexpected prompt format")
        return prompt

    def set_base_prompt(self, pri_prompt_terminator=LINUX_PROMPT_PRI, 
                        alt_prompt_terminator=LINUX_PROMPT_ALT,
                        delay_factor=1,):
           return super().set_base_prompt(
                pri_prompt_terminator=pri_prompt_terminator,
                alt_prompt_terminator=alt_prompt_terminator,
                delay_factor=delay_factor,)

# Testing Routine
def main():
    if False:
        # Register the custom class with Netmiko's CLASS_MAPPER
        CLASS_MAPPER["cisco_vos"] = CustomVOSSSH
        # Ensure the class registration has been done
        print("Registered device types:", CLASS_MAPPER.keys())

    # Define the device configuration
    device = {
        "device_type": "generic",  # Matches the registered custom class
        #"device_type": "cisco_vos",
        "host": "10.10.42.10",
        "username": "administrator",
        "password": "Ir0nv01p",
        #"global_delay_factor": 10,
        #"timeout": 30
    }

    if False:
        # Register the custom class with Netmiko's CLASS_MAPPER
        CLASS_MAPPER["cisco_vos"] = CustomVOSSSH
        # Ensure the class registration has been done
        print("Registered device types:", CLASS_MAPPER.keys())

    # Establish Connection
    try:
        connection = ConnectHandler(**device)  # This now uses CustomVOSSSH
        print("Connection Successful!")
        connection.base_prompt = "admin:"  # Adjust the base prompt
        print(f'entered base_prompt: {connection.base_prompt}')
        #connection.set_base_prompt()  # Force Netmiko to use this
        #print('set base prompt')
        #time.sleep(30)

        # what find_prompt does is send a newline and then return whatever the prompt is
        # this should work great AFTER we have a prompt working but not before.
        found_prompt = connection.find_prompt()
        
        wait = 0        # closer to TRIES as currently written
        timeout = 5

        # check for 'timeout' seconds to find the appropriate prompt.
        # TODO : redo this logic to something cleaner.
        while (found_prompt != connection.base_prompt) and (wait <= timeout):
            time.sleep(1)
            wait +=1
            print(wait)
            found_prompt = connection.find_prompt()     # NOTE: this takes time so this isn't just a WAIT multiplier - redo
            
        if wait >= timeout:
            print('TIMEOUT')

        print("Detected Prompt:", connection.find_prompt())

        # now lets try some commands that should respond fairly quickly without errors
        #
        # NOTE: I have NOT entered any conditions for other types of prompts yet so ANYTHING
        # will cause these to fail

        # immediately shut off pagination
        # removes case that we might get :: Press <enter> for 1 line, <space> for one page, or <q> to quit
        #
        output = connection.send_command('set cli pagination off', expect_string=DEFAULT_PROMPT)
        print(output)

        output = connection.send_command('show network eth0', expect_string=DEFAULT_PROMPT)
        print(output)

        output = connection.send_command('utils disaster_recovery history backup', expect_string=DEFAULT_PROMPT)
        print(output)

        output = connection.send_command('utils disaster_recovery status backup', expect_string=DEFAULT_PROMPT)
        print(output)

        output = connection.send_command('show cert own tomcat', expect_string=DEFAULT_PROMPT)
        print(output)

        connection.disconnect()

    except Exception as e:
        print(f"Error during connection: {e}")

# Testing routine
if __name__ == "__main__":
     main()