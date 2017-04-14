# NOCExec #
[![Build Status](https://travis-ci.org/velp/nocexec.svg?branch=master)](https://travis-ci.org/velp/nocexec)
[![Coverage Status](https://coveralls.io/repos/velp/nocexec/badge.svg)](https://coveralls.io/r/velp/nocexec)

NOCExec is a python (2 and 3 version) library for automating the processes of configuration and administration of network infrastructure. Provides a high level of performance for working with network devices without distinction of each operating system.

Supported protocols for connecting to devices:

 * SSH
 * Telnet
 * [NetConf](https://tools.ietf.org/html/rfc6241)

The following vendors of network equipment are supported (now in development, see the issues):
 * Cisco (IOS)
 * Juniper (JunOS)
 * Extreme (XOS)

## Installation
NOCExec can be installed from PyPi:
```bash
pip install nocexec
```

## Usage
Using a basic SSH client

```python
    >>> from nocexec import SSHClient
    >>> with SSHClient("192.168.0.1", "user", "password") as cli:
    ...     cli.execute("terminal length 0", wait=["#"])
    ...     cli.send("exit")
    ...
    ['terminal length 0', 'cisco-router']
```

Using a basic NetConf client

```python
    >>> from nocexec import NetConfClient
    >>> with NetConfClient("192.168.0.1", "user", "password") as cli:
    ...     cli.view("show system uptime", tostring=True)
    ...     cli.validate()
    ...     if cli.compare() is not None:
    ...         cli.commit()
    ...
    '<rpc-reply message-id="urn:uuid:a89b27fb-209c-4e61-9a38-993b51b54eae">\n
    <system-uptime-information>\n
    <current-time>\n
    .....
    </current-time>\n
    </system-uptime-information>\n
    </rpc-reply>\n'
```

Using a basic JunOS driver

```python
>>> with JunOS("192.168.0.1", "user", "password") as cli:
...     cli.view("clear arp hostname 8.8.8.8", tostring=True)
...     cli.save()
... 
True
```


## Tests
You can run the tests by invoking
```bash
tox
```
in the repository root.