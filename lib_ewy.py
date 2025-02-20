# Expressway Certificate testing methods
#
# need a method for getting all certificates from EWY by some API means
# trying different ideas
#       selenium and pulling from admin page
#       api/management API (doesn't seem to have them all in there)
#       xCommand or xConfiguration (doesn't seem to be there)

"""
It's looking like Selenium is the most useful method for accessing this information.
It requires you to authenticate using hte login page (you can't just basic Auth to the final web page)
After authenticated in selenium, it is possible to get pop screens with the PEM text.
Once the PEM text is downloaded, the certs can be processed similar to the UC_CERT_API using cryptography library.

So these methods below may not get used.
Selenium code is currently in lib_selenium.py module

"""

import click
import requests
from requests.auth import HTTPBasicAuth


def get_ewy_certs(base_url, auth, verify_ssl=True, type='certs'):
    """

    /api/management/configuration/xcp/cucmcerts         # ucm certs
    /api/management/configuration/xcp/xcpcerts          # imps certs
    /api/management/commands/result/certs
    api/management/commands/result/domaincerts

    NOTE: These 2 links WILL give the output but htey require seperate authentication
        The authentication is popping up a form rather than just taking the authentication
        I think I have to pre-authenticate and have a JSESSION to use these two links
    https://10.10.48.185:445/download?file=CA_CERTIFICATE
    https://10.10.48.185:445/download?file=SERVER_CERTIFICATE
    """

    if type == 'certs':
        endpoint = f"{base_url}/api/management/commands/result/certs"
    elif type == 'cucm':
        endpoint = f"{base_url}/api/management/configuration/xcp/cucmcerts"
    elif type == 'xcp':
        endpoint = f"{base_url}/api/management/configuration/xcp/xcpcerts"
    elif type == 'domain':
        endpoint = f"{base_url}/api/management/commands/result/domaincerts"
    elif type == 'self':
        endpoint = f"{base_url}/download?file=SERVER_CERTIFICATE"
    elif type == 'trust':
        endpoint = f"{base_url}/download?file=CA_CERTIFICATE"

    try:
        response = requests.get(endpoint, auth=auth, verify=verify_ssl)
        if response.status_code == 200:
            click.secho("Certs successfully retrieved.")
            if type in ['self', 'trust']:
                return response.text
            return response.json()
        else:
            click.secho(f"Failed to retrieve certs: HTTP {response.status_code}")
            click.secho(response.text)
            return None
    except Exception as e:
        click.secho(f"Error accessing Cisco EWY API: {e}")
        return None


def get_certificates(expressway_url, username, password):
    api_endpoint = f"{expressway_url}/putxml"
    payload = """
    <Command>
        <Security>
            <Certificates>
                <Get/>
            </Certificates>
        </Security>
    </Command>
    """
    # headers = {'Content-Type': 'text/xml'}

    response = requests.post(
        api_endpoint,
        auth=HTTPBasicAuth(username, password),
        data=payload,
        verify=False
    )
    if response.status_code == 200:
        print("Certificates retrieved successfully.")
        print(response.text)  # XML response
    else:
        print(f"Failed to retrieve certificates. Status: {response.status_code}")
        print(response.text)
