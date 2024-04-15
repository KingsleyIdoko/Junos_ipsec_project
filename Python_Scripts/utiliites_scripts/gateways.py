from utiliites_scripts.commons import (get_valid_name,get_valid_selection,
                                       get_valid_ipv4_address)
from interfacesOper import InterfaceManager
from securityikepolicy import IkePolicyManager
interface_manager = InterfaceManager()
policy_manager = IkePolicyManager()

def gen_ikegateway_config(**kwargs):
    old_gateways = kwargs.get('old_gateways', None)
    if old_gateways:
        print(f"There are {len(old_gateways)} existing IKE Policy on the device")
        for i, choice in enumerate(old_gateways, start=1):
            print(f"{i}. {choice}")
    gateway_name = get_valid_name("Enter new IKE gateway name: ")
    interface_data = interface_manager.get_interfaces()
    choices = policy_manager.get_ike_policy(get_policy_name=True)
    gateway_names =  get_valid_selection("Select IKE Policy", choices)
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
    print(payload)
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
    valid_interfaces = []
    interfaces = interfaces[0]
    if not interfaces or not isinstance(interfaces, list):
        print("No interfaces found or data is in the incorrect format.")
        return None
    for interface in interfaces[0]:
        unit = interface.get('unit', {})
        family = unit.get('family', {})
        inet = family.get('inet', {})
        address = inet.get('address', {})
        ip_address = address.get('name')
        if interface.get('name') != 'fxp0' and ip_address:
            valid_interfaces.append({
                'external-interface': interface['name'],
                'local-address': ip_address
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
    
def select_gateways_to_update(ike_gateways):
    print("Select a policy to update:")
    for i, gateway in enumerate(ike_gateways, start=1):
        print(f"{i}. {gateway['name']}")
    selection = input("Enter the number of the gateway: ")
    if selection.isdigit() and 1 <= int(selection) <= len(ike_gateways):
        return ike_gateways[int(selection) - 1]
    else:
        print("Invalid selection.")
        return None

def extract_gateways_params(**kwargs):
    ike_gateways = kwargs.get('ike_gateways')
    old_gateways = [gateway['name'] for gateway in ike_gateways if 'name' in gateway]
    ike_policies = policy_manager.get_ike_policy(get_policy_name=True)
    selected_gateway = select_gateways_to_update(ike_gateways)
    if not selected_gateway:
        print("No gateway selected or invalid selection. Exiting update process.")
        return None, None
    old_gateway_name = selected_gateway['name']
    continue_update = True
    while continue_update:
        policy_attributes = {
            'name': selected_gateway['name'],
            'ike-policy': selected_gateway['ike-policy'],
            'address': selected_gateway['address'],
            'external-interface': selected_gateway['external-interface'],
            'local-address': selected_gateway['local-address'],
            'version': selected_gateway['version'],
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        selected_key = selected_attribute.split(':')[0].strip()
        if selected_key in ['external-interface', 'local-address']:
            interface_data = interface_manager.get_interfaces()
            device_interface = select_interface_with_ip(interface_data)
            selected_gateway['external-interface'] = device_interface['external-interface']
            selected_gateway['local-address'] = device_interface['local-address']
            print(f"Updated external interface to {selected_gateway['external-interface']}")
            print(f"Updated local address to {selected_gateway['local-address']}")
        elif selected_key == 'ike-policy':
            selected_gateway[selected_key] = get_valid_selection("Select a new ike policy: ", ike_policies)
        elif selected_key == 'address':
            selected_gateway[selected_key] = get_valid_ipv4_address("Enter a new IP address: ")
        elif selected_key == 'version':
            selected_gateway[selected_key] = get_valid_selection("Select a new version: ", ["v1-only", "v2-only"])
        else:
            selected_gateway[selected_key] = get_valid_name(f"Enter the new value for {selected_key}: ")
        another_change = input("Would you like to make another change? (yes/no): ").strip().lower()
        if another_change != 'yes':
            continue_update = False
    insert_attribute = ""
    if old_gateways and len(old_gateways) > 1:
        if old_gateways[-1] == old_gateway_name:
            last_gateway_name = old_gateways[-2]
        else:
            last_gateway_name = old_gateways[-1]
        insert_attribute = f'insert="after" key="[ name=\'{last_gateway_name}\' ]"'
    else:
        print("No existing IKE policies found. Creating the first policy.")
    payload = f"""
    <configuration>
            <security>
                <ike>
                    <gateway {insert_attribute} operation="create">
                        <name>{selected_gateway['name']}</name>
                        <ike-policy>{selected_gateway['ike-policy']}</ike-policy>
                        <address>{selected_gateway['address']}</address>
                        <external-interface>{selected_gateway['external-interface']}</external-interface>
                        <local-address>{selected_gateway['local-address']}</local-address>
                        <version>{selected_gateway['version']}</version>
                    </gateway>
                </ike>
            </security>
    </configuration>""".strip()
    print(payload)
    return (payload, old_gateway_name) if old_gateway_name != selected_gateway['name'] else (payload, None)


def del_ike_gateway(**kwargs):
    try:
        gateway_names = kwargs.get("gateway_name")
        if not gateway_names:
            raise ValueError("No gateway names provided for deletion.")
        used_gateway = kwargs.get("used_gateway", [])
        if isinstance(used_gateway, list):
            used_gateway = [used_gateway]
        if not isinstance(gateway_names, list):
            del_gateway_name = gateway_names
        else:
            del_gateway_name = get_valid_selection("Select Policy to delete: ", gateway_names)
        if not del_gateway_name:
            raise ValueError("Invalid selection or no selection made.")
        if used_gateway != None:
            if del_gateway_name in used_gateway:
                message = f"{del_gateway_name} is referenced in an IKE Gateway and cannot be deleted."
                raise ReferenceError(message)
        payload = f"""
            <configuration>
                    <security>
                        <ike>
                            <gateway operation="delete">
                                <name>{del_gateway_name}</name>
                            </gateway>
                        </ike>
                    </security>
            </configuration>""".strip()
        return payload
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
