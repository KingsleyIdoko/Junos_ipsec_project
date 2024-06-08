from utiliites_scripts.commons import (get_valid_name,get_valid_selection,
                                       get_valid_ipv4_address,validate_yes_no)
from sec_interfaces import InterfaceManager
from sec_ike_policy import IkePolicyManager
interface_manager = InterfaceManager()
policy_manager = IkePolicyManager()

def gen_ikegateway_config(**kwargs):
    old_gateways = kwargs.get('old_gateways', [])
    if old_gateways:
        print(f"There are {len(old_gateways)} existing IKE Policy on the device")
        for i, choice in enumerate(old_gateways, start=1):
            print(f"{i}. {choice}")
    while True:
        gateway_name = get_valid_name("Enter new IKE gateway name: ")
        if old_gateways and gateway_name in old_gateways:
            print("This gateway name is already in use. Please choose another name.")
        else:
            break
    interface_data = interface_manager.get_interfaces(get_only_interfaces=True)
    ike_policy_names = policy_manager.get_ike_policy(get_policy_name=True)
    gateway_names =  get_valid_selection("Select IKE Policy", ike_policy_names)
    selected_data = select_interface_with_ip(interface_data)
    if selected_data:
        external_interface = selected_data['external-interface']
        local_address = selected_data['local-address'].split('/')[0]
        print(f"external_interface: {external_interface}")
        print(f"local_address: {local_address}")
    else:
        print("No valid interface selected, cannot proceed.")
        return
    remote_address = get_valid_ipv4_address("Enter remote-address: ")
    version = prompt_for_ike_gataway_version()
    if old_gateways:
        last_gateway_name = old_gateways[-1] 
        insert_attribute = f'insert="after" key="[ name=\'{last_gateway_name}\' ]"'
    else:
        insert_attribute = ""
        print("No existing IKE policies found. Creating the first policy.")
    payload = f"""
    <configuration>
            <security>
                <ike>
                    <gateway {insert_attribute} operation="create">
                        <name>{gateway_name}</name>
                        <ike-policy>{gateway_names}</ike-policy>
                        <address>{remote_address}</address>
                        <external-interface>{external_interface}</external-interface>
                        <local-address>{local_address}</local-address>
                        <version>{version}</version>
                    </gateway>
                </ike>
            </security>
    </configuration>""".strip()
    return payload


def prompt_for_ike_gataway_version():
    while True:
        sel_version = ["v1-only", "v2-only"]
        version = get_valid_selection("Select IKE Version: ", sel_version)
        if version.lower() in ["v1-only", "v2-only"]:
            print(f"{version} is selected!")
            return version
        print("Invalid mode selected. Please choose either 'v1-only' or 'v2-only'.")

def select_interface_with_ip(interfaces):
    if not interfaces or not isinstance(interfaces, list) or not interfaces[0]:
        print("No interfaces found or data is in the incorrect format.")
        return None
    valid_interfaces = []
    for interface in interfaces[0]:
        unit = interface.get('unit', {})
        family = unit.get('family', {})
        inet = family.get('inet', {})
        addresses = inet.get('address')
        if isinstance(addresses, list):
            for address in addresses:
                ip_address = address.get('name')
                if ip_address:
                    valid_interfaces.append({
                        'external-interface': interface['name'],
                        'local-address': ip_address.split('/')[0]
                    })
        elif isinstance(addresses, dict):
            ip_address = addresses.get('name')
            if ip_address:
                valid_interfaces.append({
                    'external-interface': interface['name'],
                    'local-address': ip_address.split('/')[0]
                })
    for index, intf in enumerate(valid_interfaces, start=1):
        print(f"{index}. {intf['external-interface']}: {intf['local-address']}")
    try:
        selection = int(input("Select an External-Interface by number: "))
        if 1 <= selection <= len(valid_interfaces):
            return valid_interfaces[selection - 1]
        else:
            print("Invalid selection number.")
            return None
    except ValueError:
        print("Invalid input; please enter a number.")
        return None
    
def del_ike_gateway(**kwargs):
    gateway_names = kwargs.get('gateway_names', [])
    if not gateway_names:
        raise ValueError("No gateway names provided for deletion.")
    if not isinstance(gateway_names, list):
        gateway_names = [gateway_names]
    used_gateways = kwargs.get('get_used_gateways', [])
    if not isinstance(used_gateways, list):
        used_gateways = [used_gateways]
    if len(gateway_names) > 1:
        while True:
            del_gateway_name = get_valid_selection("Select Policy to delete: ", gateway_names)
            if del_gateway_name:
                break
            print("Invalid selection, please try again.")
    else:
        del_gateway_name = gateway_names[0]
    if del_gateway_name in used_gateways:
        message = f"{del_gateway_name} is referenced in an IKE Gateway and cannot be deleted."
        raise ReferenceError(message)
    payload = f"""
    <configuration>
        <security>
            <ike>
                <gateway operation='delete'>
                    <name>{del_gateway_name}</name>
                </gateway>
            </ike>
        </security>
    </configuration>"""
    return payload.strip()

def gen_ike_gateway_config(**kwargs):
    track_changes = {}
    ike_gateways = kwargs.get('ike_gateways', [])
    used_gateways = kwargs.get('used_ike_gateways', [])
    old_gateways = [gateway['name'] for gateway in ike_gateways if 'name' in gateway]
    ike_policies = policy_manager.get_ike_policy(get_policy_name=True)
    ike_gateway_names = [gates['name'] for gates in ike_gateways]
    choice = get_valid_selection("Select IKE gateway to update: ", ike_gateway_names)
    selected_gateway = next((gateway for gateway in ike_gateways if gateway['name'] == choice), None)
    if not selected_gateway:
        print("No gateway selected or invalid selection. Exiting update process.")
        return None, None
    old_gateway_name = selected_gateway['name']
    old_gateway_values = selected_gateway.copy()
    continue_update = True
    while continue_update:
        policy_attributes = {
            'name': selected_gateway.get('name'),
            'ike-policy': selected_gateway.get('ike-policy'),
            'address': selected_gateway.get('address'),
            'external-interface': selected_gateway.get('external-interface'),
            'local-address': selected_gateway.get('local-address'),
            'version': selected_gateway.get('version'),
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update: ", attribute_keys)
        selected_key = selected_attribute.split(':')[0].strip()
        if selected_key in ['external-interface', 'local-address']:
            interface_data = interface_manager.get_interfaces(get_only_interfaces=True)
            device_interface = select_interface_with_ip(interface_data)
            if 'external-interface' in selected_key:
                track_changes[selected_key] = old_gateway_values['external-interface']
                selected_gateway['external-interface'] = device_interface.get('external-interface')
                print(f"Updated external interface to {selected_gateway['external-interface']}")
            if 'local-address' in selected_key:
                track_changes[selected_key] = old_gateway_values['local-address']
                selected_gateway['local-address'] = device_interface.get('local-address')
                print(f"Updated local address to {selected_gateway['local-address']}")
        elif selected_gateway[selected_key] in used_gateways:
            print(f"{selected_gateway[selected_key]} is in use by IPsec VPN, Cannot be modified")
            return None, None
        else:
            track_changes[selected_key] = old_gateway_values[selected_key]
            selected_gateway[selected_key] = handle_key_selection(selected_key, ike_policies, old_gateways, used_gateways)
            print(f"Updated {selected_key} to {selected_gateway[selected_key]}")   
        continue_update = validate_yes_no("Would you like to make another change? (yes/no): ")
    insert_attribute = get_insert_attribute(old_gateways, selected_gateway, track_changes)
    payload = create_payload(selected_gateway, insert_attribute, track_changes)
    print(payload)
    return payload

def handle_key_selection(key, policies, old_gateways, used_gateways):
    if key == 'ike-policy':
        return get_valid_selection("Select a new IKE policy: ", policies)
    elif key == 'address':
        return get_valid_ipv4_address("Enter a new IP address: ")
    elif key == 'version':
        return get_valid_selection("Select a new version: ", ["v1-only", "v2-only"])
    elif key == 'name':
        while True:
            new_value = get_valid_name(f"Enter the new value for {key}: ")
            if new_value in old_gateways or new_value in used_gateways:
                print(f"{new_value} is in use. Try again.")
            else:
                return new_value


def get_insert_attribute(old_names, gateway, track_changes):
    if 'name' in track_changes and track_changes['name'] != gateway['name']:
        if old_names:
            last_gateway_name = None
            if old_names[-1] != gateway['name']:
                last_gateway_name = old_names[-1]
            elif len(old_names) > 1:
                last_gateway_name = old_names[-2]
            if last_gateway_name == track_changes['name']:
                last_gateway_name = old_names[-2] if len(old_names) > 1 else None
            return f'insert="after" key="[name=\'{last_gateway_name}\']" operation="create"' if last_gateway_name else ""
    print("No existing IKE policies found. Creating the first policy.")
    return ""

def create_payload(gateway, insert_attribute, track_changes):
    update_new_name = f"""<gateway operation="delete"><name>{track_changes['name']}</name></gateway>""" if 'name' in track_changes else ""
    ike_policy = f"<ike-policy>{gateway['ike-policy']}</ike-policy>" if 'ike-policy' in gateway else ""
    address = f"<address>{gateway['address']}</address>" if 'address' in gateway else ""
    update_address = f"""<address operation="delete"/><address>{gateway['address']}</address>""" if "address" in track_changes else ""
    update_external_interface = f"""<external-interface operation="delete"/><external-interface>{gateway['external-interface']}</external-interface>""" if 'external-interface' in track_changes else ""
    update_local_address = f"""<local-address operation="delete"/>""" if 'local-address' in track_changes else ""
    external_interface = f"<external-interface>{gateway['external-interface']}</external-interface>" if 'external-interface' in gateway else ""
    local_address = f"<local-address>{gateway['local-address']}</local-address>" if 'local-address' in gateway else ""
    version = f"<version>{gateway['version']}</version>" if 'version' in gateway else ""
    return f"""
    <configuration>
        <security>
            <ike>
                {update_new_name}
                <gateway {insert_attribute}>
                    <name>{gateway['name']}</name>
                    {ike_policy}
                    {update_address}
                    {address}
                    {update_external_interface}
                    {external_interface}
                    {update_local_address}
                    {local_address}
                    {version}
                </gateway>
            </ike>
        </security>
    </configuration>""".strip()

