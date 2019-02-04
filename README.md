# ST-Link Utility Automation
Python API to automate STMicroelectonics flash using ST-Link CLI Utility.

#### Required Packages:
- pywin32
- pypiwin32

#### Hardware used
ST-Link V2 that comes with STMicroelectronics Nucleo development boards. These ST-Links
also provide USB-to-Serial ports. 

#### Download
Download [ST-Link Utility](https://www.st.com/en/development-tools/stsw-link004.html) and install. 
Make sure to add the "ST-LINK_CLI.exe" 's directory in the PATH.

#### Supported programmers
Check ST-Link Utility guide.

## How to install and use 
There aren't any installations. Clone the repository and use the methods.
There are only two public methods: 
  - **findall()**<br>
  This method returns all the ST-Link Probe number and corresponding COM port number.
  - **flash(hex_path, probe_no)**<br>
  This method takes the hex file path and the probe number (*default = 0*). It returns status
  ('successful' / 'failed') and the checksum of the hex/binary file. 
  


#### Example
  ```buildoutcfg
import stlink

if __name__ == '__main__':
    print(stlink.findall())
    status, checksum = stlink.flash('G:\\test.hex')
    print(status)
```

Output:
```buildoutcfg
[{'probe': '0', 'com': 'COM4'}]
successful
```

## TAGS
ST-Link/V2, stlink, SWD, Python, ARM, CortexM, STM32, FLASH, USB