"""
Module with helper functions
"""

import re


class NetconfRPCDict(dict):
    '''
    Part of the code is taken from recipe:
        http://code.activestate.com/recipes/410469-xml-as-dictionary/

    Example usage:

        >>> # Form netconf RPC reply
        >>> from ncclient import manager
        >>> from ncclient.xml_ import NCElement
        >>> test_xml = """<rpc-reply message-id="urn:uuid:9ac6b9f3">
        ...   <ethernet-switching-table-information style="brief">
        ...     <ethernet-switching-table style="brief">
        ...       <mac-table-entry style="brief">
        ...         <mac-vlan>hosting</mac-vlan>
        ...         <mac-address>*</mac-address>
        ...         <mac-type>Flood</mac-type>
        ...         <mac-age>-</mac-age>
        ...         <mac-interfaces-list>
        ...           <mac-interfaces>All-members</mac-interfaces>
        ...         </mac-interfaces-list>
        ...       </mac-table-entry>
        ...       <mac-table-entry style="brief">
        ...         <mac-vlan>hosting</mac-vlan>
        ...         <mac-address>00:00:5e:00:01:0a</mac-address>
        ...         <mac-type>Learn</mac-type>
        ...         <mac-age seconds="0">0</mac-age>
        ...         <mac-interfaces-list>
        ...           <mac-interfaces>xe-0/1/1.0</mac-interfaces>
        ...         </mac-interfaces-list>
        ...       </mac-table-entry>
        ...       <mac-table-entry style="brief">
        ...         <mac-vlan>hosting</mac-vlan>
        ...         <mac-address>00:00:5e:00:01:0b</mac-address>
        ...         <mac-type>Learn</mac-type>
        ...         <mac-age seconds="0">0</mac-age>
        ...         <mac-interfaces-list>
        ...           <mac-interfaces>xe-0/1/1.0</mac-interfaces>
        ...         </mac-interfaces-list>
        ...       </mac-table-entry>
        ...       <mac-table-count>380</mac-table-count>
        ...       <mac-table-learned>364</mac-table-learned>
        ...       <mac-table-persistent>0</mac-table-persistent>
        ...     </ethernet-switching-table>
        ...   </ethernet-switching-table-information>
        ... </rpc-reply>"""
        >>> device_handler = manager.make_device_handler({'name': 'junos'})
        >>> rpc_reply = NCElement(test_xml, device_handler.transform_reply())
        >>> # Usage
        >>> from nocexec.helpers import NetconfRPCDict
        >>> NetconfRPCDict(rpc_reply._NCElement__root)
        ... {
        ...     "ethernet-switching-table-information": {
        ...         "ethernet-switching-table": {
        ...             "mac-table-persistent": "0",
        ...             "mac-table-learned": "364",
        ...             "mac-table-entry": [
        ...                 {
        ...                     "mac-age": "-",
        ...                     "mac-interfaces-list": {
        ...                         "mac-interfaces": "All-members"
        ...                     },
        ...                     "mac-vlan": "hosting",
        ...                     "mac-type": "Flood",
        ...                     "mac-address": "*"
        ...                 },
        ...                 {
        ...                     "mac-age": "0",
        ...                     "mac-interfaces-list": {
        ...                         "mac-interfaces": "xe-0/1/1.0"
        ...                     },
        ...                     "mac-vlan": "hosting",
        ...                     "mac-type": "Learn",
        ...                     "mac-address": "00:00:5e:00:01:0a"
        ...                 },
        ...                 {
        ...                     "mac-age": "0",
        ...                     "mac-interfaces-list": {
        ...                         "mac-interfaces": "xe-0/1/1.0"
        ...                     },
        ...                     "mac-vlan": "hosting",
        ...                     "mac-type": "Learn",
        ...                     "mac-address": "00:00:5e:00:01:0b"
        ...                 }
        ...             ],
        ...             "mac-table-count": "380"
        ...         }
        ...     }
        ... }
    '''

    def __init__(self, parent_element):  # pylint: disable=super-init-not-called
        # check all child tags in parent_element
        for element in parent_element:
            # if found child tags
            if len(element) > 0: # pylint: disable=len-as-condition
                # if this element is not one with the same
                # tag (list of elements)
                if not self._uniq_tag(parent_element, element.tag):
                    # list for identical tags
                    if element.tag not in self:
                        self[element.tag] = list()
                    self.get(element.tag).append(NetconfRPCDict(element))
                # if element with same tag is uniq, add as a dict
                else:
                    self.update({element.tag: NetconfRPCDict(element)})
            # finally, if there are no child tags and no attributes, extract
            # the text
            else:
                if element.text:
                    element.text = element.text.replace('\n', '')
                self.update({element.tag: element.text})

    @staticmethod
    def _uniq_tag(element, tag):
        return len([e.tag for e in element if e.tag == tag]) == 1


def rpc_to_dict(rpc_reply, path=None):
    """
    Convert Netconf RPC reply from XML to dictionary

        :param rpc_reply: Netconf RPC reply
        :param path: get dictionary element by path
        :type rpc_reply: ncclient.xml_.NCElement
        :type path: string
        :returns: dictionary of RPC reply
        :rtype: dict
    """
    # pylint: disable=protected-access
    rpc_dict = NetconfRPCDict(rpc_reply._NCElement__root)
    if path is not None:
        return reduce(lambda d, key: d[key], path.split('/'), rpc_dict)
    return rpc_dict


def unix_mac(mac):
    """
    Convert Ethernet MAC address to UNIX format 00:11:aa:bb:cc:dd.

        :param mac: MAC address
        :type mac: string
        :returns: MAC address in UNIX format
        :rtype: string
    """
    bad_chars = set([' ', '-', '.', ':'])
    c_mac = ''.join([c.lower() for c in mac if c not in bad_chars])
    if not re.search(r'^[0-9a-f]{12}$', c_mac):
        return None
    return c_mac[:2] + ":" + ":".join([c_mac[i] + c_mac[i + 1]
                                       for i in range(2, 12, 2)])
