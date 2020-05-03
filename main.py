"""ST-Link Automation Example"""

import stlink

if __name__ == '__main__':
    print(f'List of ST-Link: {stlink.findall()}')
    print('Flashing:...', end='')
    status, checksum = stlink.flash('G:\\test.hex')
    print(status)
