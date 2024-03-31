
def gen_vlan_config(vlan_id, vlan_name):
    payload  = f"""
                <configuration>
                        <vlans>
                            <vlan operation="create">
                                <name>{vlan_name}</name>
                                <vlan-id>{vlan_id}</vlan-id>
                            </vlan>
                        </vlans>
                </configuration>"""
    return payload

def gen_delete_vlan_config(vlan_name):
    payload = f"""
            <configuration>
                    <vlans>
                        <vlan operation="delete">
                            <name>{vlan_name}</name>
                        </vlan>
                    </vlans>
            </configuration>"""
    return payload

def extract_vlan_members(interface_config):
    vlan_members = []
    for interface in interface_config['interface']:
        int_name = interface.get('name', {})
        unit = interface.get('unit', {})
        family = unit.get('family', {})
        ethernet_switching = family.get('ethernet-switching', {})
        vlan = ethernet_switching.get('vlan', {})
        if 'members' in vlan:
            members = vlan['members']
            vlan_members.append(members)
    return vlan_members, int_name


def match_vlan_id(choice, vlans):
    for vlan in vlans['vlan']:
        if str(choice) == vlan['vlan-id']:  # Convert choice to str for comparison
            vlan_name = vlan['name']
            return vlan_name
    return None  # Move return None outside the loop


