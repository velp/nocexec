from nocexec.drivers.juniper import JunOS
from nocexec.drivers.cisco import IOS
from nocexec.drivers.extreme import XOS

USER = "nocuser"
PASSWORD = "nocpassword"

with JunOS("192.168.0.3", USER, PASSWORD, protocol="netconf") as cli:
    cli.view("clear arp hostname 8.8.8.8", tostring=True)
    cli.save()

with IOS("192.168.0.1", USER, PASSWORD) as cli:
    for l in cli.edit("do sh run interface Fa0/31"):
        print(l)
    cli.edit("interface FastEthernet 0/31")
    cli.edit("description Test")
    for l in cli.view("sh run interface Fa0/31"):
        print(l)
    print(cli.save())

with XOS("192.168.0.2", USER, PASSWORD) as cli:
    for l in cli.view("show switch"):
        print(l)
    for l in cli.view("show switch"):
        print(l)
    for l in cli.view("show vlan"):
        print(l)
    try:
        cli.view("asdasdasd")
    except Exception as err:
        print(err)
    try:
        cli.view("asdasdasd")
    except Exception as err:
        print(err)
    for l in cli.view("show vlan"):
        print(l)
    try:
        cli.edit("create vlan Test tag 11")
    except Exception as err:
        print(err)
    print(cli.save())