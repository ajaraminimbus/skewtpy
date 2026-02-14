import re
import requests
import pandas as pd
from io import StringIO
from datetime import datetime

import re
import requests
import pandas as pd
from io import StringIO


def sounding_exists(url: str, timeout: int = 30):
    """
    Check whether a University of Wyoming sounding request returns valid data.

    This function performs an HTTP request to the provided URL and verifies
    that the response contains a valid sounding rather than an error message
    or empty content.

    Parameters
    ----------
    url : str
        Full University of Wyoming CGI URL for a TEXT:LIST sounding query.
    timeout : int, optional
        Timeout in seconds for the HTTP request (default is 30).

    Returns
    -------
    exists : bool
        True if the sounding appears to contain valid data, False otherwise.
    response : requests.Response or None
        The HTTP response object if the request succeeded, or None if a
        network-level error occurred.

    Notes
    -----
    The function identifies unavailable soundings using typical textual
    markers returned by the UWyo server (e.g., "Can't get", "No data available"),
    and by checking for unusually short responses.
    """
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        if "Can't get" in response.text or "No data available" in response.text:
            return False, response

        if len(response.text.strip()) < 200:
            return False, response

        return True, response

    except requests.RequestException:
        return False, None


def get_wyoming_sounding(
    year: int,
    month: int,
    day: int,
    hour: int,
    station: int,
    region: str,
    header_idx: int = 2,
):
    """
    Retrieve and parse a radiosonde sounding from the University of Wyoming archive.

    This function downloads a TEXT:LIST formatted radiosonde observation from
    the University of Wyoming sounding server, extracts the tabular data
    contained in the HTML <pre> block, and returns it as a pandas DataFrame.

    Parameters
    ----------
    year : int
        Year (UTC) of the sounding.
    month : int
        Month (1–12).
    day : int
        Day of month.
    hour : int
        Hour in UTC (typically 00 or 12).
    station : int
        WMO station number (e.g., 76679).
    region : str
        University of Wyoming regional identifier (e.g., "naconf").
        
        Valid options typically include:
        - "naconf" : North America
        - "samer"  : South America
        - "europe" : Europe
        - "africa" : Africa
        - "asia"   : Asia
        - "pac"    : Pacific
        - "antar"  : Antarctica
        
    header_idx : int, optional
        Zero-based index inside the <pre> block where the column names appear.
        Default is 2, which matches the standard UWyo TEXT:LIST format.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the sounding variables parsed from the fixed-width
        table. Column names are inferred from the header line. Units are stored
        in `df.attrs["units"]` when available.

    Raises
    ------
    ValueError
        If the sounding is not available, the HTML does not contain a <pre>
        block, or no data rows are found.

    Notes
    -----
    The function:
    1. Builds the UWyo CGI request URL.
    2. Verifies that the sounding exists.
    3. Extracts the HTML <pre> block containing the ASCII table.
    4. Identifies the header and unit lines.
    5. Parses the fixed-width table using pandas.read_fwf().
    6. Removes trailing metadata after the data section.

    The returned DataFrame typically contains columns such as:
    PRES, HGHT, TEMP, DWPT, RELH, MIXR, DRCT, SKNT, etc.,
    depending on the server format.
    """
    month = f"{month:02d}"
    ddhh = f"{day:02d}{hour:02d}"

    url = (
        "https://weather.uwyo.edu/cgi-bin/sounding?"
        f"region={region}&TYPE=TEXT%3ALIST&YEAR={year}&MONTH={month}"
        f"&FROM={ddhh}&TO={ddhh}&STNM={station}"
    )

    exists, response = sounding_exists(url)

    if not exists:
        raise ValueError("Sounding not available for this datetime/station.")

    match = re.search(
        r"<pre[^>]*>(.*?)</pre>",
        response.text,
        flags=re.DOTALL | re.IGNORECASE
    )

    if not match:
        raise ValueError("No <pre> block found in response.")

    pre_block = match.group(1)
    lines = pre_block.splitlines()

    header_line = lines[header_idx].strip()
    units_line = lines[header_idx + 1].strip() if header_idx + 1 < len(lines) else ""

    data_start = header_idx + 2

    if data_start < len(lines) and re.match(r"^\s*-{5,}\s*$", lines[data_start]):
        data_start += 1

    data_lines = lines[data_start:]

    stop_markers = ("###", "Station information", "Observations")
    cut = None
    for i, ln in enumerate(data_lines):
        if any(mk in ln for mk in stop_markers):
            cut = i
            break
    if cut is not None:
        data_lines = data_lines[:cut]

    data_lines = [
        ln for ln in data_lines
        if ln.strip() and not re.match(r"^\s*-{5,}\s*$", ln)
    ]

    data_text = "\n".join(data_lines).strip()
    if not data_text:
        raise ValueError("No data rows found.")

    colnames = header_line.split()

    df = pd.read_fwf(StringIO(data_text), header=None, names=colnames)
    df.attrs["units"] = units_line

    return df
