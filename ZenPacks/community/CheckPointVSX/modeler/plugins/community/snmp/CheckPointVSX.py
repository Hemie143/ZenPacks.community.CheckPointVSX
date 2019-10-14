
__doc__ = """CheckPointVSX
Use the CheckPoint MIB to gather info about virtual VSX Firewalls.
"""

from Products.DataCollector.plugins.CollectorPlugin import SnmpPlugin, GetMap, GetTableMap
from Products.DataCollector.plugins.DataMaps import ObjectMap, RelationshipMap, MultiArgs

# TODO:
# Monitor based on VSId, not on snmpindex
# If change is seen, remodel.

class CheckPointVSX(SnmpPlugin):
    """
    Doc about this CheckPointVSX plugin
    """

    snmpGetMap = GetMap({
        '.1.3.6.1.4.1.2620.1.16.12.0': 'vsxVsConfigured',
    })

    snmpGetTableMaps = (
        GetTableMap('vsxStatusTable', '.1.3.6.1.4.1.2620.1.16.22.1.1', {
            '.1': 'vsxStatusVSId',
            '.3': 'vsxStatusVsName',
            '.4': 'vsxStatusVsType',
            '.9': 'vsxStatusHAState',
        }),
        GetTableMap('vsxCountersTable', '.1.3.6.1.4.1.2620.1.16.23.1.1', {
            '.4': 'vsxCountersConnTableLimit',
        }),
    )

    def process(self, device, results, log):
        log.info("Processing %s for device %s", self.name(), device.id)
        getdata, tabledata = results
        if not getdata['vsxVsConfigured'] > 0:
            log.debug('No Virtual System found {}'.format(getdata['vsxVsConfigured']))
            return []

        vsxFirewallMap = RelationshipMap(
            relname='vsxfirewalls',
            compname=self.compname,
            modname='ZenPacks.community.CheckPointVSX.VSXFirewall'
        )

        maps = []
        vsxStatusTable = tabledata.get('vsxStatusTable', {})
        vsxCountersTable = tabledata.get('vsxCountersTable', {})
        for snmpindex, vs in vsxStatusTable.items():
            if not vs['vsxStatusVsType'] == 'Virtual System':
                continue
            snmpindex = snmpindex.strip('.')
            name = vs['vsxStatusVsName']
            haState = vs['vsxStatusHAState']
            # TODO: The connection limit is retrieved, based on the snmpindex. However, I don't think there's
            # any guarantee that the snmpindex in the vsxCountersTable is identical. It would be preferable to
            # use the VSId. Same for the data collection, but it would then require a PythonPlugin.
            vsxFirewallMap.append(ObjectMap(
                compname=self.compname,
                modname='ZenPacks.community.CheckPointVSX.VSXFirewall',
                data={
                    'id': self.prepId(name),
                    'title': '{} ({})'.format(name, haState),
                    'snmpindex': snmpindex,
                    'VSId': vs['vsxStatusVSId'],
                    'HAState': haState,
                    'ConnLimit': vsxCountersTable.get(snmpindex, {})['vsxCountersConnTableLimit']
                }
            ))
        maps.extend([vsxFirewallMap])

        return maps
