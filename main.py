"""ST-Link Automation Example"""

import stlink


if __name__ == '__main__':
    print(stlink.findall())
    status, checksum = stlink.flash('G:\\test.hex', 0)
    print(status)


