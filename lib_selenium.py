# First attempts at a Selenium library for use by reporting engine
# SeleniumHelper class to be used for initializing a Selenium object with ChromeDriver 
#
# Expect to put in common methods and delays as seperate classes here.
# Other reports will then draw from these methods as needed.
#

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import click
from datetime import datetime, timedelta

# from webdriver_manager.chrome import ChromeDriverManager

# NOTE: selenium lends itself to being in a docker image so you have the right browser versions

# Update with the path to your ChromeDriver
# NOTE: last downloaded driver v131
# https://googlechromelabs.github.io/chrome-for-testing/
# Version 131.0.6778.86 (Official Build) (x86_64)
CHROME_DRIVER_FILENAME = 'chromedriver'
CHROME_DRIVER_SEARCH_PATH = './:/usr/bin/'
# FOR DOCKER
#   in alpine, chromedriver will be installed at: /usr/bin/chromedriver
#   So can we add ENV PATH="/usr/bin/chromedriver:${PATH}"
#   Do we need a routine to find chrome driver in the path?
#   installa with RUN apk add chromium chromium-chromedriver

class SeleniumHelper(object):
    def __init__(self, ignore_security=True, debug=True,
                 chrome_driver_search_path=CHROME_DRIVER_SEARCH_PATH,
                 chrome_driver_filename=CHROME_DRIVER_FILENAME):

        self.ignore_security = ignore_security
        self.debug = debug
        #self.chrome_driver_path = chrome_driver_path

        self.chrome_driver_path = self._find_filename(file_name=chrome_driver_filename, 
                                                      search_path=chrome_driver_search_path)
        
        # will be initialized by create_driver()
        self.chrome_options = None
        self.service = None
        self.driver = None

    @staticmethod
    def _find_filename(file_name='chromedriver', search_path='./'):
        """Locate file_name and return entire path to file
        """
        for path_dir in search_path.split(os.pathsep):
            file_path = os.path.join(path_dir, file_name)
            if os.path.isfile(file_path):
                return file_path
        
        # if not found in passed search_path then use ENV PATH
        for path_dir in os.environ.get('PATH', '').split(os.pathsep):
            file_path = os.path.join(path_dir, file_name)
            if os.path.isfile(file_path):
                return file_path
        
        return None    
        
    def create_driver(self):
        """
        Creates and returns a Selenium WebDriver instance configured to bypass SSL warnings.
        """

        LOCAL_DEBUG = True

        # Set OPTIONS
        chrome_options = Options()

        if self.ignore_security:
            chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
            chrome_options.add_argument("--ignore-ssl-errors=yes")  # Ignore SSL errors
            chrome_options.add_argument("--allow-insecure-localhost")  # Bypass localhost SSL warnings
            chrome_options.add_argument("--disable-web-security")  # Disable web security (optional)

        if not self.debug:
            chrome_options.add_argument("--headless")  # Optional: Run in headless mode

        chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")  # Prevent site isolation
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection as bot
        chrome_options.add_argument("--disable-gpu")  # Optional: Disable GPU acceleration
        chrome_options.add_argument("--no-sandbox")  # Optional: Needed in some environments
        chrome_options.add_argument("--disable-infobars")  # Prevent "Chrome is being controlled" warning
        # chrome_options.add_argument("--start-maximized")  # Start maximized for consistent viewport

        # Set SERVICE (path taken from defaults)
        service = Service(self.chrome_driver_path)

        if LOCAL_DEBUG:
            # service.command_line_args = ['--verbose']
            print('GOT SERVICE')

        # Create DRIVER
        try:
            self.driver = webdriver.Chrome(service=self.service, options=self.chrome_options)
            if LOCAL_DEBUG:
                print('GOT DRIVER')

            return self.driver
        except Exception as e:
            print('Error when creating driver')
            print(e)
            return None

    def close_driver(self):
        """
        Closes the Selenium WebDriver instance.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
        """
        self.driver.quit()

    def authenticate(self):
        pass


class SeleniumEWY(SeleniumHelper):

    def __init__(self, ip, user, pwd,
                 ignore_security=True, debug=True,
                 chrome_driver_search_path=CHROME_DRIVER_SEARCH_PATH,
                 chrome_driver_filename=CHROME_DRIVER_FILENAME):

        self.ip = ip
        self.username = user
        self.password = pwd
        self.base_url = f'https://{self.ip}'
        super.__init__(self, ignore_security=True, debug=True, 
                       chrome_driver_search_path=CHROME_DRIVER_SEARCH_PATH,
                       chrome_driver_filename=CHROME_DRIVER_FILENAME)

    def authenticate(self):
        """
        Authenticates to a website using the provided WebDriver instance.

        TODO: Need a condition for TRUE/FALSE to know if this works

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
            url (str): The URL to authenticate against.
            username (str): The username for authentication.
            password (str): The password for authentication.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """

        PAUSE = False
        # WAIT_LOAD = 2
        WAIT_PROCESS = 3

        try:
            url = f'https://{self.ip}/login'
            self.driver.get(url)
            # time.sleep(WAIT_LOAD)  # Allow time for the page to load

            # TODO: pause needed until driver is fixed due to cert windows
            if PAUSE:
                click.pause()

            # Locate elements username/password
            username_field = self.driver.find_element(By.NAME, "username")  # Adjust selector
            password_field = self.driver.find_element(By.NAME, "password")  # Adjust selector

            # explicit wait for at least username to show up
            wait = WebDriverWait(self.driver, 10)
            wait.until(lambda d: username_field.is_displayed())

            # update fields and click form to submit
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            # password_field.send_keys(Keys.RETURN)

            print(self.driver.page_source)
            print("-*" * 40)
            print("BEFORE hitting form button")
            print("-*" * 40)

            self.driver.find_element(By.NAME, "formbutton").click()

            print(self.driver.page_source)
            print("-*" * 40)
            print("AFTER hitting form button")
            print("-*" * 40)
            # now waiting to see that it authenticated and splash screen shows
            time.sleep(WAIT_PROCESS)  # Allow time for login to process

            print(self.driver.page_source)
            print("-*" * 40)
            print("AFTER waiting...")
            print("-*" * 40)

            # explicit wait for at least username to show up
            # wait = WebDriverWait(driver, 10)
            # wait.until(lambda d : "Overview" in driver.page_source)

            if "Overview" in self.driver.page_source:
                print("Login successful")
                click.pause()
                return True
            else:
                print("Login failed")
                return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
        pass

    def fetch_certs(self, cert_type='self'):
        """
        Fetches and returns the content of a certificate page.

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
            cert_url (str): The URL of the certificate page.

        Returns:
            str: The content of the certificate page.
        """
        WAIT_LOAD = 2
        if cert_type in ['self']:
            cert_url = f"https://{self.ip}/download?file=SERVER_CERTIFICATE"
        elif cert_type in ['ca', 'trust']:
            cert_url = f"https://{self.ip}/download?file=CA_CERTIFICATE"

        try:
            self.driver.get(cert_url)
            time.sleep(WAIT_LOAD)  # Allow time for the page to load
            cert_content = self.driver.page_source
            return cert_content
        except Exception as e:
            print(f"Failed to fetch certificate: {e}")
            return None


class SeleniumVOS(SeleniumHelper):

    """
    Need more for this because there are lots of pages to authenticate to with multiple accounts
    """
    def __init__(self, ip, user, pwd,
                 ignore_security=True, debug=True,
                 chrome_driver_search_path=CHROME_DRIVER_SEARCH_PATH,
                 chrome_driver_filename=CHROME_DRIVER_FILENAME):

        self.ip = ip
        # NOTE: there are multiple logins for this - need to incorporate
        self.username = user
        self.password = pwd
        self.base_url = f'https://{self.ip}'

        super.__init__(self, ignore_security=True, debug=True,
                       chrome_driver_search_path=CHROME_DRIVER_SEARCH_PATH,
                       chrome_driver_filename=CHROME_DRIVER_FILENAME)

        self.urls = {
            'base_url': f"https://{self.ip}/ccmadmin/",  # Replace with the actual login page URL
            'cert_url': f"https://{self.ip}/ccmadmin/certificateFindList.do",
            'cert_url': f"https://{self.ip}/ccmadmin/certificateFindList.do?lookup=false&multiple=true&rowsPerPage=250&pageNumber=1",
            'cert_trust_url': f"https://{self.ip}/download?file=CA_CERTIFICATE",

            # OSAdmin
            'base_url': f"https://{self.ip}/cmplatform/",  # Replace with the actual login page URL
            'cert_url': f"https://{self.ip}/cmplatform/certificateFindList.do",
        }

    def authenticate(self, service='ccmadmin'):
        """
        Authenticates to a website using the provided WebDriver instance.

        TODO: Need a condition for TRUE/FALSE to know if this works

        Args:
            driver (webdriver.Chrome): The Selenium WebDriver instance.
            url (str): The URL to authenticate against.
            username (str): The username for authentication.
            password (str): The password for authentication.

        Returns:
            bool: True if authentication is successful, False otherwise.
        """
        assert service in ['ccmadmin', 'cmplatform']

        PAUSE = False
        # WAIT_LOAD = 2
        WAIT_PROCESS = 3

        if service in ['ccmadmin']:
            url = f"https://{self.ip}/ccmadmin/"  # Replace with the actual login page URL

        try:
            self.driver.get(url)
            # time.sleep(WAIT_LOAD)  # Allow time for the page to load

            # TODO: pause needed until driver is fixed due to cert windows
            if PAUSE:
                click.pause()

            # Locate elements username/password
            username_field = self.driver.find_element(By.NAME, "j_username")  # Adjust selector
            password_field = self.driver.find_element(By.NAME, "j_password")  # Adjust selector

            # explicit wait for at least username to show up
            wait = WebDriverWait(self.driver, 10)
            wait.until(lambda d: username_field.is_displayed())

            # update fields and click form to submit
            username_field.send_keys(self.username)
            password_field.send_keys(self.password)
            # password_field.send_keys(Keys.RETURN)

            print(self.driver.page_source)
            print("-*" * 40)
            print("BEFORE hitting form button")
            print("-*" * 40)

            # Locate and click the "Login" button
            login_button = self.driver.find_element(By.CLASS_NAME, "cuesLoginButton")
            login_button.click()

            # Alternatively, submit the form if possible
            # password_field.send_keys(Keys.RETURN)

            # driver.find_element(By.NAME, "logonForm").click()  # form has name="logonForm" with a "submit" button

            print(self.driver.page_source)
            print("-*" * 40)
            print("AFTER hitting form button")
            print("-*" * 40)
            # now waiting to see that it authenticated and splash screen shows
            time.sleep(WAIT_PROCESS)  # Allow time for login to process

            print(self.driver.page_source)
            print("-*" * 40)
            print("AFTER waiting...")
            print("-*" * 40)

            # explicit wait for at least username to show up
            # wait = WebDriverWait(driver, 10)
            # wait.until(lambda d : "Overview" in driver.page_source)

            if "Logout" in self.driver.page_source:
                print("Login successful")
                click.pause()
                return True
            else:
                print("Login failed")
                return False
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False

# #########################################################
# Testing methods (no in a class)


def create_driver(ignore_security=True, debug=True,                  
                  chrome_driver_search_path=CHROME_DRIVER_SEARCH_PATH,
                  chrome_driver_filename=CHROME_DRIVER_FILENAME):

    """
    Creates and returns a Selenium WebDriver instance configured to bypass SSL warnings.
    """

    LOCAL_DEBUG = True

    # Set OPTIONS
    chrome_options = Options()

    if ignore_security:
        chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL certificate errors
        chrome_options.add_argument("--ignore-ssl-errors=yes")  # Ignore SSL errors
        chrome_options.add_argument("--allow-insecure-localhost")  # Bypass localhost SSL warnings
        chrome_options.add_argument("--disable-web-security")  # Disable web security (optional)

    if not debug:
        chrome_options.add_argument("--headless")  # Optional: Run in headless mode

    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")  # Prevent site isolation
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid detection as bot
    chrome_options.add_argument("--disable-gpu")  # Optional: Disable GPU acceleration
    chrome_options.add_argument("--no-sandbox")  # Optional: Needed in some environments
    chrome_options.add_argument("--disable-infobars")  # Prevent "Chrome is being controlled" warning
    # chrome_options.add_argument("--start-maximized")  # Start maximized for consistent viewport

    # Set SERVICE (path taken from defaults)
    chrome_driver_path = os.path.join('./', chrome_driver_filename)     # just looking locally for this
    service = Service(chrome_driver_path)

    if LOCAL_DEBUG:
        # service.command_line_args = ['--verbose']
        print('GOT SERVICE')

    # Create DRIVER
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        if LOCAL_DEBUG:
            print('GOT DRIVER')

        return driver
    except Exception as e:
        print('Error when creating driver')
        print(e)
        return None


def authenticate_ewy(driver, url, username, password):
    """
    Authenticates to a website using the provided WebDriver instance.

    TODO: Need a condition for TRUE/FALSE to know if this works

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        url (str): The URL to authenticate against.
        username (str): The username for authentication.
        password (str): The password for authentication.

    Returns:
        bool: True if authentication is successful, False otherwise.
    """

    PAUSE = False
    # WAIT_LOAD = 2
    WAIT_PROCESS = 3

    try:
        driver.get(url)
        # time.sleep(WAIT_LOAD)  # Allow time for the page to load

        # TODO: pause needed until driver is fixed due to cert windows
        if PAUSE:
            click.pause()

        # Locate elements username/password
        username_field = driver.find_element(By.NAME, "username")  # Adjust selector
        password_field = driver.find_element(By.NAME, "password")  # Adjust selector

        # explicit wait for at least username to show up
        wait = WebDriverWait(driver, 10)
        wait.until(lambda d: username_field.is_displayed())

        # update fields and click form to submit
        username_field.send_keys(username)
        password_field.send_keys(password)
        # password_field.send_keys(Keys.RETURN)

        print(driver.page_source)
        print("-*" * 40)
        print("BEFORE hitting form button")
        print("-*" * 40)

        driver.find_element(By.NAME, "formbutton").click()

        print(driver.page_source)
        print("-*" * 40)
        print("AFTER hitting form button")
        print("-*" * 40)
        # now waiting to see that it authenticated and splash screen shows
        time.sleep(WAIT_PROCESS)  # Allow time for login to process

        print(driver.page_source)
        print("-*" * 40)
        print("AFTER waiting...")
        print("-*" * 40)

        # explicit wait for at least username to show up
        # wait = WebDriverWait(driver, 10)
        # wait.until(lambda d : "Overview" in driver.page_source)

        if "Overview" in driver.page_source:
            print("Login successful")
            click.pause()
            return True
        else:
            print("Login failed")
            return False
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False


def fetch_certificate(driver, cert_url):
    """
    Fetches and returns the content of a certificate page.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        cert_url (str): The URL of the certificate page.

    Returns:
        str: The content of the certificate page.
    """
    WAIT_LOAD = 2

    try:
        driver.get(cert_url)
        time.sleep(WAIT_LOAD)  # Allow time for the page to load
        cert_content = driver.page_source
        return cert_content
    except Exception as e:
        print(f"Failed to fetch certificate: {e}")
        return None


def close_driver(driver):
    """
    Closes the Selenium WebDriver instance.

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
    """
    driver.quit()


def auth_vos(driver, url, username, password, pause=False):
    """
    Authenticates to a website using the provided WebDriver instance.

    TODO: Need a condition for TRUE/FALSE to know if this works

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        url (str): The URL to authenticate against.
        username (str): The username for authentication.
        password (str): The password for authentication.

    Returns:
        bool: True if authentication is successful, False otherwise.
    """

    PAUSE = pause
    # WAIT_LOAD = 2
    WAIT_PROCESS = 3

    try:
        driver.get(url)
        # time.sleep(WAIT_LOAD)  # Allow time for the page to load

        # TODO: pause needed until driver is fixed due to cert windows
        if PAUSE:
            click.pause()

        # Locate elements username/password
        username_field = driver.find_element(By.NAME, "j_username")  # Adjust selector
        password_field = driver.find_element(By.NAME, "j_password")  # Adjust selector

        # explicit wait for at least username to show up
        wait = WebDriverWait(driver, 10)
        wait.until(lambda d: username_field.is_displayed())

        # update fields and click form to submit
        username_field.send_keys(username)
        password_field.send_keys(password)
        # password_field.send_keys(Keys.RETURN)

        print(driver.page_source)
        print("-*" * 40)
        print("BEFORE hitting form button")
        print("-*" * 40)

        # Locate and click the "Login" button
        login_button = driver.find_element(By.CLASS_NAME, "cuesLoginButton")
        login_button.click()

        # Alternatively, submit the form if possible
        # password_field.send_keys(Keys.RETURN)

        # driver.find_element(By.NAME, "logonForm").click()  # form has name="logonForm" with a "submit" button

        print(driver.page_source)
        print("-*" * 40)
        print("AUTH: AFTER hitting form button")
        print("-*" * 40)
        # now waiting to see that it authenticated and splash screen shows
        time.sleep(WAIT_PROCESS)  # Allow time for login to process

        print(driver.page_source)
        print("-*" * 40)
        print("AUTH: AFTER waiting...")
        print("-*" * 40)

        # explicit wait for at least username to show up
        # wait = WebDriverWait(driver, 10)
        # wait.until(lambda d : "Overview" in driver.page_source)

        if "Logout" in driver.page_source:
            print("Login successful")
            if PAUSE:
                click.pause()
            return True
        else:
            print("Login failed")
            return False
    except Exception as e:
        print(f"Authentication failed: {e}")
        return False


def ucm_car_system_report(driver, ip, report_data={}, pause=False):
    """
    NOTE: Assume we ARE authenticated and have logged in.
    "driver" is authenticated by this time

    Fetches and returns the content of CAR system report

    Args:
        driver (webdriver.Chrome): The Selenium WebDriver instance.
        ip: IP of the UCM publisher being used
        report_data:  DICT of the data to fill out the report
        pause:  Boolean for troubleshooting

    Returns:
        str: Multi-line "string" which is the 'csv-version' of the car report
            same thing you would get if you ran the report form the GUI
    """

    """
    report_data structure:

    report_data = {
        'month_from': 'oct',
        'month_to':   'oct',
        'year_from':  '2024',
        'year_to':    '2024',
        'day_from':   '31',
        'day_to':     '31',
        'report_url': f'https://{ip}/car/SystemOverview.jsp'
    }


    <select id="cboMonthFrom" name="cboMonthFrom" width="55px" height="22px" style="HEIGHT: 22px; WIDTH: 55px">
                                    <option value="01">Jan
                                    </option><option value="02">Feb
                                    </option><option value="03">Mar
                                    </option><option value="04">Apr
                                    </option><option value="05">May
                                    </option><option value="06">Jun
                                    </option><option value="07">Jul
                                    </option><option value="08">Aug
                                    </option><option value="09">Sep
                                    </option><option value="10">Oct
                                    </option><option value="11">Nov
                                    </option><option value="12">Dec</option>
                        </select>
    <input id="txtDateFrom" name="txtDateFrom" size="2" height="22px" width="25px" style="HEIGHT: 22px; WIDTH: 25px" maxlength="2">
    <select id="cboYearFrom" name="cboYearFrom" height="100px" width="55px" style="HEIGHT: 22px; WIDTH: 55px">
                        <option value="2023">2023</option><option value="2024">2024</option></select>

    <select id="cboMonthTo" name="cboMonthTo" width="55px" height="22px" style="HEIGHT: 22px; WIDTH: 55px">
                    <option value="01">Jan
                    </option><option value="02">Feb
                    </option><option value="03">Mar
                    </option><option value="04">Apr
                    </option><option value="05">May
                    </option><option value="06">Jun
                    </option><option value="07">Jul
                    </option><option value="08">Aug
                    </option><option value="09">Sep
                    </option><option value="10">Oct
                    </option><option value="11">Nov
                    </option><option value="12">Dec
                    </option>
                    </select>
    <input id="txtDateTo" name="txtDateTo" size="2" height="22px" width="25px" style="HEIGHT: 22px;WIDTH:25px" maxlength="2">
    <select id="cboYearTo" name="cboYearTo" height="100px" width="55px" style="HEIGHT: 22px; WIDTH: 55px">
                        <option value="2023">2023</option><option value="2024">2024</option></select>

    <input type="radio" name="rdoReportFormat" id="rdoReportFormat" value="csv">CSV
    <input type="button" id="cmdViewReport" name="cmdViewReport" height="25px" width="190px" style="HEIGHT: 25px; WIDTH: 190px" onclick="fnSubmitForm('View Report');" value="View Report">

    """

    WAIT_LOAD = 2
    PAUSE = pause

    if False:
        try:
            driver.get(url)
            time.sleep(WAIT_LOAD)  # Allow time for the page to load
            content = driver.page_source

            print(content)

            if PAUSE:
                click.pause()
            return content
        except Exception as e:
            print(f"Failed to fetch report: {e}")
            return None

    car_system_report = report_data.get('report_url', f'https://{ip}/car/SystemOverview.jsp')
    month_from = report_data.get('month_from', '')
    month_to = report_data.get('month_to', '')
    year_from = report_data.get('year_from', '')
    year_to = report_data.get('year_to', '')
    day_from = report_data.get('day_from', '')
    day_to = report_data.get('day_to', '')

    driver.get(car_system_report)
    time.sleep(2)  # Allow time for the page to load
    driver.get(car_system_report)
    time.sleep(2)  # Allow time for the page to load
    content = driver.page_source

    # url_data = ucm_car_system_report(driver, car_system_report)
    # if url_data:
    #    print("URL Content:")
    #    print(url_data)
    # else:
    #    print("Failed to fetch URL.")

    # take 2
    # url_data = ucm_car_system_report(driver, car_system_report)
    # if url_data:
    #    print("URL Content:")
    #    print(url_data)

    # Find and fill report dates
    from_month_field = driver.find_element(By.NAME, "cboMonthFrom")  # Adjust selector
    from_day_field = driver.find_element(By.NAME, "txtDateFrom")  # Adjust selector
    from_year_field = driver.find_element(By.NAME, "cboYearFrom")
    to_month_field = driver.find_element(By.NAME, "cboMonthTo")  # Adjust selector
    to_day_field = driver.find_element(By.NAME, "txtDateTo")  # Adjust selector
    to_year_field = driver.find_element(By.NAME, "cboYearTo")
    report_format = driver.find_element(By.NAME, "rdoReportFormat")

    # explicit wait for at least one of those fields to show up
    # TODO: move this higher and make a different type of wait
    wait = WebDriverWait(driver, 10)
    wait.until(lambda d: from_month_field.is_displayed())

    # update DATE fields fields and click form to submit
    from_month_field.send_keys(month_from)
    from_day_field.clear()
    from_day_field.send_keys(day_from)
    from_year_field.send_keys(year_from)

    to_month_field.send_keys(month_to)
    to_day_field.clear()
    to_day_field.send_keys(day_to)
    to_year_field.send_keys(year_to)

    # set report type to CSV instead of PDF
    report_format.send_keys('CSV')      # selects but does not 'set' value
    report_format.click()               # click to select

    # select report to run
    # Create a Select object and select report
    # 'TSD' is the "Traffic Summary - Day of Month" report
    report_select = driver.find_element("id", "cboListOfReports")
    select = Select(report_select)
    select.select_by_value("TSD")

    # apply the selection by calling the @onclick for adding to report listing
    apply_button = driver.find_element("xpath", "//a[contains(@onclick, 'fncmdAddOnClick')]")
    apply_button.click()

    # Submit request for report to VIEW report rather than SEND
    submit_report = driver.find_element(By.NAME, "cmdViewReport")   # tentative SUBMIT button
    submit_report.click()

    # TODO: document what this part does
    original_window = driver.current_window_handle
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            break

    # Wait for the new page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "fraReport")))

    # driver.get(url)
    # time.sleep(4)  # Allow time for the page to load
    content = driver.page_source
    print(content)
    if PAUSE:
        click.pause()

    # Extract the value of the SRC attribute
    # <FRAME NAME="fraReport" SRC="/carreports/reports/ondemand/temp/11E055FD7B156125B083A0EF0D95B104202412484346280.csv">
    csv_link = driver.find_element(By.NAME, "fraReport")
    csv_value = csv_link.get_attribute("src")

    csv_url = f'https://{ip}{csv_value}'
    print(f'CSV_VALUE: {csv_value}')
    print(f'CSV_URL: {csv_url}')
    driver.get(csv_value)
    time.sleep(4)  # Allow time for the page to load
    content = driver.page_source
    print('-*' * 5)
    print(content)

    # Locate the <pre> tag which holds the CSV data
    # Extract and return this data
    pre_element = driver.find_element(By.TAG_NAME, "pre")
    pre_data = pre_element.text

    print('-*' * 30)
    print('FINAL DATA TO EXTRACT')
    print(pre_data)
    print('-*' * 30)

    return pre_data


def last_month_report_data():
    """Utility method to populate a dictionary with data to run a report on last month

    """

    # Get the current date
    current_date = datetime.now()

    # Extract the month and year
    month = current_date.month
    year = current_date.year

    print(f"Month: {month}, Year: {year}")

    # If january then reduce the year to get last Decebmer
    if month == 1:
        year -= 1

    month -= 1  # reduce month by 1 to get last month

    report_data = {}
    MONTHS = {'Jan': 31, 'Feb': 28, 'Mar': 31, 'Apr': 30,
              'May': 31, 'Jun': 30, 'Jul': 31, 'Aug': 31,
              'Sep': 30, 'Oct': 31, 'Nov': 30, 'Dec': 31}

    report_data['month_from'] = month
    report_data['month_to'] = month
    report_data['day_from'] = 1
    report_data['day_to'] = MONTHS[month]
    report_data['year_from'] = year
    report_data['year_to'] = year
    # get today's date determine month
    # then return report based on month
    # if february and year is /4 then it's 29

    return report_data


# Chatgpt code for previos month - to test out
def get_previous_month_dates():
    # Get today's date
    today = datetime.now()

    # Calculate the first day of the current month
    first_day_this_month = today.replace(day=1)

    # Calculate the last day of the previous month
    last_day_previous_month = first_day_this_month - timedelta(days=1)

    # Extract year and month for the previous month
    year_previous = last_day_previous_month.year
    month_previous = last_day_previous_month.month

    # Get the first day of the previous month
    first_day_previous_month = last_day_previous_month.replace(day=1)

    # Format the results
    return {
        'month_from': first_day_previous_month.strftime("%b"),  # Abbreviated month name
        'month_to': last_day_previous_month.strftime("%b"),
        'year_from': str(first_day_previous_month.year),
        'year_to': str(last_day_previous_month.year),
        'day_from': str(first_day_previous_month.day),
        'day_to': str(last_day_previous_month.day),
    }


# Example Usage
def main():
    # this isn't working yet because I don't know the path
    driver = create_driver()
    print('RETURNED DRIVER')
    # driver = webdriver.Chrome()

    if False:
        # ewy login
        ip = '10.10.48.180'
        username = 'admin'
        password = 'Ir0nv01p'
        try:
            base_url = f"https://{ip}/login"  # Replace with the actual login page URL
            cert_url = f"https://{ip}/download?file=SERVER_CERTIFICATE"
            cert_trust_url = f"https://{ip}/download?file=CA_CERTIFICATE"

            if authenticate_ewy(driver, base_url, username, password):
                cert_data = fetch_certificate(driver, cert_url)
                if cert_data:
                    print("Certificate Content:")
                    print(cert_data)
                else:
                    print("Failed to fetch certificate.")

                cert_data = fetch_certificate(driver, cert_trust_url)
                if cert_data:
                    print("Certificate Content:")
                    print(cert_data)
                else:
                    print("Failed to fetch certificate.")

            else:
                print("Authentication failed.")
        finally:
            close_driver(driver)

    # VOS Login
    if False:
        ip = '10.10.54.10'
        username = 'admin'
        password = 'Ir0nv01p'
        try:
            base_url = f"https://{ip}/ccmadmin/"  # Replace with the actual login page URL
            cert_url = f"https://{ip}/ccmadmin/certificateFindList.do"
            cert_url = f"https://{ip}/ccmadmin/certificateFindList.do?lookup=false&multiple=true&rowsPerPage=250&pageNumber=1"
            cert_trust_url = f"https://{ip}/download?file=CA_CERTIFICATE"

            # OSAdmin
            base_url = f"https://{ip}/cmplatform/"  # Replace with the actual login page URL
            cert_url = f"https://{ip}/cmplatform/certificateFindList.do"

            if auth_vos(driver, base_url, username, password):
                cert_data = fetch_certificate(driver, cert_url)
                if cert_data:
                    print("Certificate Content:")
                    print(cert_data)
                else:
                    print("Failed to fetch certificate.")

            else:
                print("Authentication failed.")
        finally:
            click.pause()
            close_driver(driver)

    # CAR Report
    if True:
        # login information for CCM driver
        ip = '10.10.54.10'
        username = 'admin'
        password = 'Ir0nv01p'

        ip = 'umhucmpubv.medstar.net'
        username = ''
        password = ''
        base_url = f"https://{ip}/ccmadmin/"  # Replace with the actual login page URL

        # NOTE: actual report has to have a means of populating this report
        # thinking of using a method that looks at the current date and grabs 'last month'

        # data for report
        report_data = {
            'month_from': 'Oct',
            'month_to':   'Oct',
            'year_from':  '2024',
            'year_to':    '2024',
            'day_from':   '31',
            'day_to':     '31',
            'report_url': f'https://{ip}/car/SystemOverview.jsp'
        }

        # car_system_report = f"https://{ip}/car/SystemOverview.jsp"

        PAUSE = True
        try:
            if auth_vos(driver, base_url, username, password):
                url_data = ucm_car_system_report(driver, ip, report_data=report_data, pause=PAUSE)

            print('RETURNED CAR REPORT')
            print(url_data)
        except Exception as e:
            print(e)

    if False:
        ip = '10.10.54.10'
        username = 'admin'
        password = 'Ir0nv01p'

        PAUSE = False
        try:
            base_url = f"https://{ip}/ccmadmin/"  # Replace with the actual login page URL
            car_system_report = f"https://{ip}/car/SystemOverview.jsp"
            month_from = 'oct'
            month_to = 'oct'
            year_from = '2024'
            year_to = '2024'
            day_from = '31'
            day_to = '31'

            if auth_vos(driver, base_url, username, password):

                # Had to get the page twice before it would work due to login

                driver.get(car_system_report)
                time.sleep(2)  # Allow time for the page to load
                driver.get(car_system_report)
                time.sleep(2)  # Allow time for the page to load
                content = driver.page_source
                # url_data = ucm_car_system_report(driver, car_system_report)
                # if url_data:
                #    print("URL Content:")
                #    print(url_data)
                # else:
                #    print("Failed to fetch URL.")

                # take 2
                # url_data = ucm_car_system_report(driver, car_system_report)
                # if url_data:
                #    print("URL Content:")
                #    print(url_data)

                # Find and fill report dates
                from_month_field = driver.find_element(By.NAME, "cboMonthFrom")  # Adjust selector
                from_day_field = driver.find_element(By.NAME, "txtDateFrom")  # Adjust selector
                from_year_field = driver.find_element(By.NAME, "cboYearFrom")
                to_month_field = driver.find_element(By.NAME, "cboMonthTo")  # Adjust selector
                to_day_field = driver.find_element(By.NAME, "txtDateTo")  # Adjust selector
                to_year_field = driver.find_element(By.NAME, "cboYearTo")
                report_format = driver.find_element(By.NAME, "rdoReportFormat")

                # explicit wait for at least one of those fields to show up
                # TODO: move this higher and make a different type of wait
                wait = WebDriverWait(driver, 10)
                wait.until(lambda d: from_month_field.is_displayed())

                # update DATE fields fields and click form to submit
                from_month_field.send_keys(month_from)
                from_day_field.clear()
                from_day_field.send_keys(day_from)
                from_year_field.send_keys(year_from)

                to_month_field.send_keys(month_to)
                to_day_field.clear()
                to_day_field.send_keys(day_to)
                to_year_field.send_keys(year_to)

                # set report type to CSV instead of PDF
                report_format.send_keys('CSV')      # selects but does not 'set' value
                report_format.click()               # click to select

                # select report to run
                # Create a Select object and select report
                # 'TSD' is the "Traffic Summary - Day of Month" report
                report_select = driver.find_element("id", "cboListOfReports")
                select = Select(report_select)
                select.select_by_value("TSD")

                # apply the selection by calling the @onclick for adding to report listing
                apply_button = driver.find_element("xpath", "//a[contains(@onclick, 'fncmdAddOnClick')]")
                apply_button.click()

                # Submit request for report to VIEW report rather than SEND
                submit_report = driver.find_element(By.NAME, "cmdViewReport")   # tentative SUBMIT button
                submit_report.click()

                # TODO: document what this part does
                original_window = driver.current_window_handle
                for window_handle in driver.window_handles:
                    if window_handle != original_window:
                        driver.switch_to.window(window_handle)
                        break

                # Wait for the new page to load
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "fraReport")))

                # driver.get(url)
                # time.sleep(4)  # Allow time for the page to load
                content = driver.page_source
                print(content)
                if PAUSE:
                    click.pause()

                # Extract the value of the SRC attribute
                # <FRAME NAME="fraReport" SRC="/carreports/reports/ondemand/temp/11E055FD7B156125B083A0EF0D95B104202412484346280.csv">
                csv_link = driver.find_element(By.NAME, "fraReport")
                csv_value = csv_link.get_attribute("src")

                csv_url = f'https://{ip}{csv_value}'
                print(f'CSV_VALUE: {csv_value}')
                print(f'CSV_URL: {csv_url}')
                driver.get(csv_value)
                time.sleep(4)  # Allow time for the page to load
                content = driver.page_source
                print('-*' * 5)
                print(content)

                # Locate the <pre> tag which holds the CSV data
                # Extract and return this data
                pre_element = driver.find_element(By.TAG_NAME, "pre")
                pre_data = pre_element.text

                print('-*' * 30)
                print('FINAL DATA TO EXTRACT')
                print(pre_data)
                print('-*' * 30)
            else:
                print("Authentication failed.")
        finally:
            click.pause()
            close_driver(driver)


if __name__ == "__main__":
    main()
