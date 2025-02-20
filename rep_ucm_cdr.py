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
import json
from ciscocucmapi import UCMAXLConnector
import re
import csv
from rep_base import ReportTemplate
from lib_excel import CellFormatFixed, CellFormatBody, CellFormatHeader, CellFormatTitle
from openpyxl.chart import LineChart, AreaChart, Reference

from dotenv import load_dotenv
# individual report job class is responsible to just return formatted data
# it does not write to the excel spreadsheet at this time

# TODO: this should go in ClickConfig and holds the location of the AXL schema files
AXL_SCHEMA_DIR = 'ciscocucmapi/schema'

def load_cdr_data_from_file(file_path):
    """Test routine to load stored CDR data as text format rather than making a live call to server

    :param filename:    filename to load.  JSON format
    :return:            JSON object of the UC snapshot 
    """

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            data = [row for row in reader]  # Store all rows including headers
        return data
    except Exception as e:
        print(f"Error loading snapshot: {e}")
        return None

class ReportUcmCdrMonthly(ReportTemplate):
    def __init__(self, vars, metadata={}, excel=None, **kwargs):           # TODO: do we change this to **kwargs
        self.os_type = 'SELENIUM'

        #AXL_WSDL_URL=os.environ.get('AXL_WSDL_URL',f'ciscocucmapi/schema/{DEFAULT_AXL_VERSION}/AXLAPI.wsdl')
        #self.axl_wsdl_url = f'{AXL_SCHEMA_DIR}/{self.axl_version}/AXLAPI.wsdl'
        #self.axl_version = vars.get('axl_version', '12.5')
        self.commands = []

        self.excel_manager = excel
        self.metadata = metadata
        self.vars = vars
        self.tab_name = metadata.get('tab_name', 'MISSING_TAB')
        self.title = metadata.get('title', 'MISSING_TITLE')

        self.ip = vars.get('ip', '')
        self.host = vars.get('host', '')
        self.user = vars.get('user', '')
        self.pwd = vars.get('pwd', '')
        self.cluster_type = vars.get('type', '')
        pprint(vars)

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
        LOCAL_DEBUG = False
        output = ""
        status = None
        # TODO: load from file for now
        # will call selenium engine when in production
        if self.vars.get('test', False):
            # use test data
            # NOTE: this is loading right into CSV which we may not want
            # if selenium data comes in as TEXT STRING then this should too.
            # update as needed.  Then have _parse or _format manipulate the data in a common way
            data = load_cdr_data_from_file(self.vars.get('test_file', ''))
            status = 'SUCCESS - Using Test data from file.'
        else:
            # TODO: This is where the call to selenium will go when it is working
            # 
            data = {}
            status = 'SELENIUM DATA COLLECTION NOT BUILT YET'

        if LOCAL_DEBUG:
            pprint(data)

        self.data_collected = data

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

        self.data_formatted = output 

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


        # TITLE LINE: License Management 
        value = 'CDR Monthly Report'
        row = 1
        column = 1
        cell = sheet.cell(row=row, column=column, value=value)
        cell.font = title_format.font
        cell.fill = title_format.fill
        cell.alignment = title_format.alignment
        cell.border = title_format.border
        
        # this is just a starter
        for row in data:
            sheet.append(row)  # Write each row
        print(f"Added a new tab [{tab_name}] with formatted data to the workbook.")


        # NOW Add a chart - this is NOT working yet

        # Determine location of data to use
        # We will hardwire the data location for now.
        # A10 to J10, down to A41-J41 (assuming 31 days and a header row

        chart = LineChart()
        chart = AreaChart()
        chart.title = "Daily Metrics Over a Month"
        chart.x_axis.title = "Day"
        chart.y_axis.title = "Values"

        # Define data range (excluding headers)
        data_range = Reference(sheet, min_col=2, min_row=11, max_col=11, max_row=42)
        category_range = Reference(sheet, min_col=1, min_row=10, max_row=32)

        # Add data to chart (titles from headers)
        chart.add_data(data_range, titles_from_data=True)
        chart.set_categories(category_range)

        # Position the chart in the next available column (L1)
        sheet.add_chart(chart, "Q4")

        return 'success assumed'


def main():

    # test example to lab 12 server
    vars = {'ip': '10.10.42.10',
            'host': '10.10.42.10',
            'user': 'administrator',
            'pwd': '',
            'axl_version': '12.5',
            }
    
    report = ReportUcmCdrMonthly(vars)
    r = report.run()
    pprint(r)

# Testing routine
if __name__ == "__main__":
     main()