"""
ST-Link CLI Interface

The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:


THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
import subprocess
from typing import List
import win32com.client


def _find_probe_and_sn():
    """
    Finds ST-Link programmer's probe and hardware serial number.

    The method uses ST-Link Utility's CLI interface to find ST-Link V2 programmers if there are any.

    Returns:
        probe_list: A list of dictionaries consists of probe number and hardware serial
            number. If no ST-Link programmers can be found then the method will return None.

        Example -> probe_list = [{'probe': '0', 'sn': '21324515'}, {'probe': '1', 'sn': '21ABC54'}]

    Raises:
        FileNotFoundError: ST-Link Utility CLI isn't present in the current directory or on PATH.
    """

    try:
        stlink_output = subprocess.run(
            ["ST-LINK_CLI.exe", "-List"],
            check=False,
            stdout=subprocess.PIPE).stdout.decode().splitlines()
    except FileNotFoundError:
        print('ST-LINK_CLI.exe is missing! Put in the same directory or add path into PATH.')
        return None

    if 'No ST-LINK detected!' in stlink_output:
        print('No ST-LINK detected!')
        return None

    probe_list = list()
    for i, line in enumerate(stlink_output):
        if re.search('^ST-LINK Probe', line):
            device = dict()
            device['probe'] = re.findall('([0-9]+):', line)[0]
            device['sn'] = re.findall('SN: ([A-Z0-9]+)', stlink_output[i + 1])[0]
            probe_list.append(device)

    return probe_list


def _find_port_and_sn():
    """
    Finds ST-Link programmer's COM port and hardware serial number.

    The method traverse through device manager to find ST-Link V2 programmers if there are any.

    Returns:
        com_list: A list of dictionaries consists of com port number and hardware serial
            number. If no ST-Link programmers can be found then the method will return None.

        Example:
        com_list = [{'sn': '213SD12F', 'com': 'COM30'}, {'sn': '21AF154S', 'com': 'COM95'}]

    """
    com_list = list()
    wmi = win32com.client.GetObject("winmgmts:")

    # pylint: disable=anomalous-backslash-in-string
    for serial_port in wmi.InstancesOf("Win32_SerialPort"):

        if 'STMicroelectronics' in serial_port.name:
            device = dict()
            device['sn'] = re.findall('(USB\S+)\\\\', serial_port.PNPDeviceID)[0]
            device['com'] = serial_port.DeviceID
            com_list.append(device)

    for usb in wmi.InstancesOf("Win32_USBHub"):
        device_id = re.findall('(USB\S+)\\\\', usb.DeviceID)[0]
        for port in com_list:
            if device_id in port['sn']:
                port['sn'] = re.findall('PID_\S+\\\([A-Z0-9]+)', usb.DeviceID)[0]

    # pylint: enable=anomalous-backslash-in-string
    return com_list


def findall():
    """
    Finds ST-Link programmer's COM port and Probe number.

    The method maps ST-LINK debug serial com port with probe number.

    Returns:
        stlink_list: A list of dictionaries consists of com port number and probe number.
            If no ST-Link programmers can be found then the method will return None.

        Example - stlink_list = [{'probe': '0', 'com': 'COM30'}, {'probe': '1', 'com': 'COM95'}]

    """
    ports = _find_port_and_sn()
    probes = _find_probe_and_sn()

    if ports is None or probes is None:
        return None

    stlink_list = list()
    for probe in probes:
        for i, port in enumerate(ports):
            if probe['sn'] == port['sn']:
                stlink_list.append({'probe': probe['probe'], 'com': port['com']})
                del ports[i]
                break

    return stlink_list


def flash(hex_file_path: str, probe: int = 0):
    """
    Flashes microcontroller.

    The method flashes mcu using ST-Link Utility's CLI interface.
    To keep things simple most of the flags are hardcoded.

    Args:
        hex_file_path: Path of the hex file that will be used to flash the mcu
        probe: the probe number of the ST-Link programmer. Default is zero.

    Returns:
        flash_status: Either 'successful' or 'failed'
        checksum: the hex file checksum provided by ST-Link Utility CLI.
            It will be zero if programming fails.
    """
    try:
        programming_output = subprocess.check_output(
            [
                'ST-LINK_CLI.exe',
                '-c',
                'ID=' + str(probe),
                'SWD',
                'UR',
                'Hrst',
                '-Q',
                '-P',
                hex_file_path,
                '-V',
                '-HardRST',
                'HIGH',
                '-Rst',
            ],
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE).decode().splitlines()
    except subprocess.CalledProcessError as err:
        programming_output = err.output.decode().splitlines()

    return _check_flash_output(programming_output)


def _check_flash_output(output: List[str]):
    checksum = 0
    flash_status = 'failed'

    for i, line in enumerate(output):
        if line.startswith('Memory programmed'):
            if output[i + 1] == 'Verification...OK' and output[i + 2] == 'Programming Complete.':
                checksum = output[i + 3].split()[3]  # type: ignore
                flash_status = 'successful'
                break

    return flash_status, checksum
