"""
Module with drivers for connecting to devices from different manufacturers.

Supported devices:
  - Cisco devices with IOS devices
  - Extreme netwroks devices with XOS operating system
  - Juniper devices with JunOS operating system
"""

from nocexec.drivers.juniper import JunOS
from nocexec.drivers.cisco import IOS
from nocexec.drivers.extreme import XOS

# pylint: disable=invalid-name
drivers = {
    "CiscoIOS": IOS,
    "ExtremeXOS": XOS,
    "JuniperJunOS": JunOS
}
