# base module for Report Jobs
# Template base for all report jobs with base examples
# Long-term see this as an abstract class that must be filled in
#
# For now, using this as a template with a common example of what should be there
# These methods 'may' be used if it works for the sub-class
#

from lib_excel import CellFormatFixed, CellFormatBody, CellFormatHeader, CellFormatTitle
from pprint import pprint


# NOTE: thinking or renaming this ReportTemplateCommand() or ReportCommandTemplate()
#       do denote to the programmer that this is a "command design pattern"
class ReportTemplate(object):
    # template class for reports
    # uses "Command Design Pattern"
    #
    def __init__(self, vars, metadata={}, excel=None, **kwargs):
        """Example initialization for a report.

        Expect this to be overwritten but it gives a template of the key items expected for all reports
        """

        # passed parameters
        self.vars = vars
        self.metadata = metadata
        self.excel_manager = excel

        # common meta attributes
        self.tab_name = metadata.get('tab_name', 'MISSING_TAB')
        self.title = metadata.get('title', 'MISSING_TITLE')

        # running data objects
        self.data_collected = None          # raw data as returned from data collection methods
        self.data_parsed = None             # parsed/validated data
        self.data_formatted = None          # final formatted data before writing to output

        self.status = {'init': 'success',
                       'data_collect': None,
                       'data_parse': None,
                       'data_format': None,
                       'print': None,
                       }

        # are there any other items that are common for all reports?
        self.commands = []
        self.os_type = ''

    # public methods

    def test_connection(self):
        print('NOT YET IMPLEMENTED')
        status = 'status not set'
        return status

    def run(self):
        """Generic processing of a report

        Includes collection (which updates self.data_collected attribute),
                 parsing (which updates self.data_parsed attribute),
                 and formatting (which updates self.data_formatted attribute)

        :return: string of status
        """
        # connect and collect data. Stored in self.data_collected attribute
        status = self._collect_data()

        # perform any parsing/validation on data from self.data_collected.
        # Stored in self.data_parsed attribute
        status = self._parse_data()

        # Format the parsed data from self.data_parsed and format it for writing to excel
        # Stored in self.data_formatted attribute
        status = self._format_data()

        return status

    def write_excel_tab(self, data=None, tab_name=None, title=None,
                        title_format=CellFormatTitle(),
                        header_format=CellFormatHeader(),
                        body_format=CellFormatFixed()):
        """document routine"""
        if not data:
            data = self.data_formatted

        if not tab_name:
            tab_name = self.tab_name

        if not self.excel_manager.workbook:
            raise Exception("No active workbook. Create or open a spreadsheet first.")

        sheet = self.excel_manager.workbook.create_sheet(title=self.tab_name)

        # CUSTOM REPORT FOLLOWS
        # Write to tab in memory, but do not save in this routine
        # NOTE: possibly add 'save' as an optional parameter

        status = 'status not set'
        return status

    def show_status(self):
        """Idea is a status report of the last time this report was run
        and it's status with logs.

        NOTE: 'status' is currently an ATTRIBUTE as a dictionary but may change to method later.
        Use to determine if everything ran properly.
        If it didn't, then what was wrong.
        Did we connect to all devices?
        posibly use this as part of test_connection

        status = {'result': 'FINAL STATUS',
                  'data_collect': {'result': 'FINAL VALUE OF STEP',
                                 'steps': [{server_name: 'status of collect from this server'},
                                         {server_name: 'status of collect from this server'},
                                         {server_name: 'status of collect from this server'},
                                        ]
                                },
                  'data_parse': {'result': 'FINAL VALUE OF STEP',
                                 'steps': [{server_name: 'status of parse from this server'},
                                         {server_name: 'status of parse from this server'},
                                         {server_name: 'status of parse from this server'},
                                        ]
                                },
                }
        """
        pprint(self.status)

    def meta(self):
        """
        should this be a method or just a common attribute
        Idea for passing all report meta_data to the instance and storing it here.
        This would be a tempalte method that does not get overwritten by subclasses and is shared
        it would include things like.
            -title
            -tabname
            -engine
            -version
            -clustername
            -servername (not here)
        so these could be called up at any other time

        This could be an attribute and would be passed in when instantiated.

        For this we would structure the SEED file to put all META data
        under a "meta:" dictionary and just pass it as a dictionary

        Then any setters/getters would be written as needed and would be common to all reports
        because they shoudn't be controlled by the report....the data is just being stored there.
        """
        pass

    # Private Routines

    def _collect_data(self):
        """Collection routine.  Should be overritten by sub-classes each time.

        Routine should placed collected data into self.data_collected attribute

        :return:    status as string
        """
        # self.data_collected = None
        status = 'status not set'
        self.status['data_collect'] = {'result': status}
        return status

    def _parse_data(self, data=None):
        """Data parsing routine.

        Routine parses self.data_collected attribute and then updates self.data_parsed.

        :param: data    optional override of input data.  If none, then self.data_collected is used
        :return: status     string of status
        """

        if not data:
            data = self.data_collected

        self.data_parsed = data

        status = 'status not set'
        self.status['data_parse'] = {'result': status}
        return status

    def _format_data(self, data=None):
        """Data parsing routine.

        Routine parses self.data_collected attribute and then updates self.data_parsed.

        :param: data    optional override of input data.  If none, then self.data_collected is used
        :return: status     string of status
        """

        if not data:
            data = self.data_parsed

        self.data_formatted = data

        status = 'status not set'
        self.status['data_format'] = {'result': status}
        return status
