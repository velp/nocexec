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

# pylint: disable=invalid-name,line-too-long
drivers = {
    "CiscoIOS": {
        "class": IOS,
        "defaults": {
            "protocol": "ssh",
            "port": 22,
            "timeout": 5
        },
        "commands": {
            "get_fdb": {
                "cmd": "show mac address-table",
                "parser": r"\s?(?P<vlan>[0-9]+)\s{4}(?P<mac>[\w\.]{14})\s{4}\w+\s+(?P<port>[G,F,T]{1}[a-z]{1}[0-9]+\/[0-9]+)",
                "parser_type": "regexp"
            },
            "get_vlans": {
                "cmd": "show vlan brief",
                "parser": r"(?P<tag>\d+)\s+(?P<name>[\w\-]+)\s+[\w,\s]{9}\s{1}",
                "parser_type": "regexp"
            },
            "get_ports": {
                "cmd": "show interfaces description",
                "parser": r"(?P<name>[G,F,T]{1}[a-z]{1}(\d{1}\/){0,2}\d+)\s+(?P<admin_status>[up|down]{2,4})\s+(?P<oper_status>[up|down]{2,4})\s+(?P<description>[\w\-\.]+)?",
                "parser_type": "regexp"
            }
        }
    },
    "ExtremeXOS": {
        "class": XOS,
        "defaults": {
            "protocol": "ssh",
            "port": 22,
            "timeout": 5
        },
        "commands": {
            "get_fdb": {
                "cmd": "show fdb",
                "parser": r"(?P<mac>([0-9a-f]{2}[:]){5}([0-9a-f]{2}){1})\s+[\-\w]+?\(0+(?P<vlan>\d+)\)\s+\d{4}(\s{1}[\w,\s]){7}\s{1}(?P<port>\d+)",
                "parser_type": "regexp"
            },
            "get_vlans": {
                "cmd": "show vlan",
                "parser": r"(?P<name>\w+)\s+(?P<tag>\d+)\s+[\-\w]{48}\s{1}[A-Z]+\s+[\d,\s]{2}\/[\d,\s]{3}\s{1}[\w\-]+",
                "parser_type": "regexp"
            },
            "get_ports": {
                "cmd": "show ports no-refresh",
                "parser": r"(?P<name>\d+)\s+(?P<description>[\w\-\.]+)?\s+([\w\-\(\)]+)?\s+(?P<admin_status>[D,E]{1})\s+(?P<oper_status>[A,R,NP,L,D,d]{1,2})\s+(\d+[A-Z]?)?\s+([FULL|HALF]{4})?",
                "parser_type": "regexp"
            }
        }
    },
    "JuniperJunOS": {
        "class": JunOS,
        "defaults": {
            "protocol": "netconf",
            "port": 22,
            "timeout": 5
        },
        "commands": {
            "get_fdb": {
                "cmd": "show ethernet-switching table",
                "parser": "ethernet-switching-table-information/ethernet-switching-table/mac-table-entry",
                "parser_type": "etree"
            },
            "get_vlans": {
                "cmd": "show vlans",
                "parser": "vlan-information/vlan",
                "parser_type": "etree"
            },
            "get_ports": {
                "cmd": "show interfaces descriptions",
                "parser": "interface-information/physical-interface",
                "parser_type": "etree"
            }
        }
    }
}
