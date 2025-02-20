# Generic CERTIFICATE methods using cryptography library
#

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from datetime import datetime, timedelta
import click

# #############################################
# Get Cert Data
#

# dir(cert)
# ['__class__', '__deepcopy__', '__delattr__', '__dir__', '__doc__', '__eq__', '__format__',
# '__ge__', '__getattribute__', '__gt__', '__hash__', '__init__', '__init_subclass__',
# '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__',
# '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__',
# 'extensions', 'fingerprint', 'issuer', 'not_valid_after', 'not_valid_after_utc',
# 'not_valid_before', 'not_valid_before_utc', 'public_bytes', 'public_key',
# 'public_key_algorithm_oid', 'serial_number', 'signature', 'signature_algorithm_oid',
# 'signature_algorithm_parameters', 'signature_hash_algorithm', 'subject',
# 'tbs_certificate_bytes', 'tbs_precertificate_bytes', 'verify_directly_issued_by', 'version']
#
# what about things like SAN and other capabilities?
# How do we get those?
#


# this could also be named "decode_certificate"
def load_pem_certificate_from_data(pem_data):
    """Load a certificate from PEM data string.

    :return: a CERT object of type <class 'cryptography.hazmat.bindings._rust.x509.Certificate'>
    """
    try:
        return x509.load_pem_x509_certificate(pem_data.encode(), default_backend())
    except Exception as e:
        click.secho(f"Error loading certificate from data: {e}")
        return None


def load_pem_certificate(file_path):
    """Load a PEM certificate file."""
    try:
        with open(file_path, "rb") as cert_file:
            cert_data = cert_file.read()
        return x509.load_pem_x509_certificate(cert_data, default_backend())
    except Exception as e:
        click.secho(f"Error loading certificate: {e}")
        return None


# #############################################
# Process Cert Data
#
#   These methods assume that cert is being passed as a PEM string
#
# in these methods "cert" is of type <class 'cryptography.hazmat.bindings._rust.x509.Certificate'>
#

def get_certificate_expiration(cert):
    """Get the expiration date of a certificate."""
    if cert:
        return cert.not_valid_after
    return None


def get_serial_number(cert):
    """Get the serial number of a certificate."""
    if cert:
        return cert.serial_number
    return None


def get_san_names(cert):
    """
    Extracts and returns the Subject Alternative Names (SAN) from a certificate.

    Args:
        cert (x509.Certificate): The certificate object.

    Returns:
        dict: A dictionary containing lists of SAN entries grouped by type, such as DNS, IP, etc.
    """
    san_names = {"DNS": [], "IP": [], "Other": []}
    try:
        san_extension = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
        san = san_extension.value
        # Collect DNS Names
        san_names["DNS"].extend(san.get_values_for_type(x509.DNSName))
        # Collect IP Addresses
        san_names["IP"].extend(san.get_values_for_type(x509.IPAddress))
        # Handle other types if needed
    except x509.ExtensionNotFound:
        pass  # SAN extension not found, return empty lists

    return san_names


def is_certificate_expired(cert):
    """Check if a certificate is expired."""
    if cert:
        return datetime.utcnow() > cert.not_valid_after
    return False


def is_certificate_near_expiration(cert, days_until_expiration):
    """Check if a certificate is near expiration."""
    if cert:
        threshold_date = datetime.utcnow() + timedelta(days=days_until_expiration)
        return cert.not_valid_after <= threshold_date
    return False


def print_certificate_details(cert, format='long'):
    """
    Prints decoded details of a certifcate.  Format determines how much information
    to priont out.  All capabilities of a certificate, including extensions,
    subject alternative names, and other properties.

    Still working out 'format' options.
        all
        brief
        subject_only
        cn_only
        cn_serialnumber


    # [Hierarchy - chain]
    # print basic information
    # Issues To:
    # Issued By:
    # Validity Period:
    # Fingerprints
    # Extensions
    # Key Usage
    # Extended Key Usage
    """
    if not cert:
        click.secho("Invalid certificate.", fg="red")
        return

    click.secho("Certificate Capabilities:")
    click.secho("-" * 50)
    click.secho(f"Subject: {cert.subject}")
    click.secho(f"Issuer: {cert.issuer}")
    click.secho(f"Serial Number: {cert.serial_number}")
    click.secho("Validity Period:")
    click.secho(f"  Not Before: {cert.not_valid_before}")
    click.secho(f"  Not After: {cert.not_valid_after}")

    if format in ['long', 'LONG', 'Long']:

        # Fingerprints
        #

        # List Extensions
        click.secho("\nExtensions:")
        for ext in cert.extensions:
            click.secho(f"  - {ext.oid.dotted_string}: {ext.oid._name}")
            try:
                click.secho(f"    Value: {ext.value}")
            except Exception as e:
                click.secho(f"    Could not display extension value: {e}")

        # Subject Alternative Names
        try:
            san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName)
            click.secho("\nSubject Alternative Names:")
            click.secho(f"  {san.value.get_values_for_type(x509.DNSName)}")
        except x509.ExtensionNotFound:
            click.secho("\nSubject Alternative Names: None found")

        # Key Usage
        try:
            key_usage = cert.extensions.get_extension_for_class(x509.KeyUsage).value
            click.secho("\nKey Usage:")
            click.secho(f"  Digital Signature: {key_usage.digital_signature}")
            click.secho(f"  Content Commitment: {key_usage.content_commitment}")
            click.secho(f"  Key Encipherment: {key_usage.key_encipherment}")
            click.secho(f"  Data Encipherment: {key_usage.data_encipherment}")
            click.secho(f"  Key Agreement: {key_usage.key_agreement}")
            click.secho(f"  Certificate Sign: {key_usage.key_cert_sign}")
            click.secho(f"  CRL Sign: {key_usage.crl_sign}")
            try:
                click.secho(f"  Encipher Only: {key_usage.encipher_only}")
            except Exception as e:
                print(e)
            try:
                click.secho(f"  Decipher Only: {key_usage.decipher_only}")
            except Exception as e:
                print(e)
        except x509.ExtensionNotFound:
            click.secho("\nKey Usage: None found")

        # Extended Key Usage
        try:
            ext_key_usage = cert.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
            click.secho("\nExtended Key Usage:")
            for usage in ext_key_usage:
                click.secho(f"  - {usage.dotted_string}   {usage._name}")
        except x509.ExtensionNotFound:
            click.secho("\nExtended Key Usage: None found")

    click.secho("-" * 50)


# this is assuming files - need to change to just data that is already loaded
# loading should be a sperate method.
# should have a single process method that takes data.  certificate(s) should be another method
#
# NOT USED FOR NOW
# this routine is being duplicated in multiple places
# ultimately it could be removed as it is a testing routine
def process_certificates(cert_files, days_until_expiration=30):
    """Process a list of certificates and print their statuses.

    Takes a list of certificate files to process

    """
    expired = []
    near_expiration = []
    valid = []

    for cert_file in cert_files:
        click.secho(f"\nProcessing {cert_file}...")
        cert = load_pem_certificate(cert_file)
        if not cert:
            click.secho("Failed to load certificate.")
            continue

        print_certificate_details(cert, format='brief')

        if is_certificate_expired(cert):
            expired.append(cert_file)
        elif is_certificate_near_expiration(cert, days_until_expiration):
            near_expiration.append(cert_file)
        else:
            valid.append(cert_file)

    click.secho("\nSummary:")
    click.secho("Expired Certificates:")
    for cert_file in expired:
        click.secho(f" - {cert_file}")

    click.secho("\nCertificates Near Expiration:")
    for cert_file in near_expiration:
        click.secho(f" - {cert_file}")

    click.secho("\nValid Certificates:")
    for cert_file in valid:
        click.secho(f" - {cert_file}")
