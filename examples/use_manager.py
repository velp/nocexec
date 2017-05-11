from nocexec.manager import Manager

USER = "nocuser"
PASSWORD = "nocpassword"

devices = {
    "CiscoIOS": "192.168.0.1",
    "ExtremeXOS": "192.168.0.2",
    "JuniperJunOS": "192.168.0.3"
}

for driver, device in devices.items():
    with Manager(driver, device, USER, PASSWORD) as cli:
        for l in cli.get_fdb():
            print(l)

    with Manager(driver, device, USER, PASSWORD) as cli:
        for l in cli.get_vlans():
            print(l)

    with Manager(driver, device, USER, PASSWORD) as cli:
        for l in cli.get_ports():
            print(l)