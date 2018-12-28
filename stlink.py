"""
ST-Link CLI Interface

The MIT License (MIT)

Copyright (c) 2016 mtchavez

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

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
from infi.devicemanager import DeviceManager


def find_probe_and_sn():
    """
    Finds ST-Link programmer's probe and hardware serial number.

    The method uses ST-Link Utility's CLI interface to find ST-Link V2 programmers if there are any.

    Returns:
        stlink_probe_list: A list of dictionaries consists of probe number and hardware serial
            number. If no ST-Link programmers can be found then the method will return None.

        Example -> stlink_list = [{'sn': 213245154sdf, 'probe': 0}, {'sn': 21abc544sdf, 'probe': 1}]

    Raises:
        FileNotFoundError: ST-Link Utility CLI isn't present in the current directory or on PATH.
    """
    stlink_probe_list = dict()

    try:
        stlink_output = subprocess.run(
            ["ST-LINK_CLI.exe", "-List"],
            check=False,
            stdout=subprocess.PIPE).stdout.decode().splitlines()
    except FileNotFoundError:
        print('ST-LINK_CLI.exe is missing! Put in the same directory or add path into PATH.')
        return None
    except subprocess.CalledProcessError:
        print('No ST-Link is available!')
        return None

    for line in probe_list:
        if re.search('^ST-LINK Probe', line):
            probe_number = re.findall('([0-9]+):', line)[0]
            serial_number = re.findall('SN: ([A-Z0-9]+)', probe_list[probe_list.index(line) + 1])[0]

            stlink_probe_list['sn'] = serial_number
            stlink_probe_list['probe'] = probe_number

    if not stlink_probe_list:
        return None
    else:
        return stlink_probe_list


def find_stlink_com_and_sn(stlink_list):
    """
    Finds ST-Link programmer's COM port and hardware serial number.

    The method traverse through device manager to find ST-Link V2 programmers if there are any.

    Returns:
        stlink_com_list: A list of dictionaries consists of com port number and hardware serial
            number. If no ST-Link programmers can be found then the method will return None.

        Example - stlink_list = [{'sn': 213sd12f, 'com': 'COM30'}, {'sn': 21af154s, 'com': 'COM95'}]

    """
    no_of_comport = 0
    dev_man = DeviceManager()
    devices = dev_man.all_devices

    for device in devices:
        # pylint: disable=anomalous-backslash-in-string
        if re.search('^STMicroelectronics STLink Virtual COM Port', device.description):
            com_port = re.findall('\(([A-Z0-9]+)\)', device.friendly_name)[0]
            usb_serial_number = re.findall('PID_\S+\\\([A-Z0-9]+)', device.parent.instance_id)[0]
        # pylint: enable=anomalous-backslash-in-string

            for stlink in stlink_list.values():
                if stlink['sn'] == usb_serial_number:
                    stlink['com'] = com_port
                    no_of_comport += 1
                    break

    return no_of_comport


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

