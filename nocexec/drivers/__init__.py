from nocexec import TelnetClient, SSHClient, NetConfClient

protocols = {
    "ssh": SSHClient,
    "telnet": TelnetClient,
    "netconf": NetConfClient
}