from utiliites_scripts.commons import get_valid_selection, get_valid_name, get_valid_string
from sec_addressbook import AddressBookManager
from sec_zone import SecurityZoneManager
from sec_ipsec_vpn import IpsecVpnManager
zone_manager = SecurityZoneManager()
address_manager = AddressBookManager()
vpn_manager = IpsecVpnManager()
import itertools, re, pprint

app = ["any","junos-aol","junos-bgp","junos-biff","junos-bootpc","junos-bootps","junos-defaults","junos-dhcp-client","junos-dhcp-relay","junos-dhcp-server",    
  "junos-discard","junos-dns-tcp","junos-dns-udp","junos-echo","junos-finger","junos-ftp","junos-ftp-data"]

def generate_zone_directions(zones):
    if len(zones) < 2:
        raise ValueError("At least two zones are needed to create directions.")
    directions = []
    for first_zone, second_zone in itertools.combinations(zones, 2):
        directions.append(f"zone_{first_zone}_to_{second_zone}")
        directions.append(f"zone_{second_zone}_to_{first_zone}")
    return directions


def confirm_policy_name(zone_dir):
    pattern = r'^(yes|no)$'
    while True:
        choice = input(f"Automatically setting the policy name to: {zone_dir}. Confirm? (yes/no) ")
        if re.match(pattern, choice, re.IGNORECASE):
            if choice.lower() == 'yes':
                return zone_dir
            else:
                zone_dir = get_valid_name("Please enter new policy name: ")

def get_subnet_names_by_zone(addresses, zone_name):
    subnet_names = []
    for address_entry in addresses:
        if address_entry['attach']['zone']['name'] == zone_name:
            if isinstance(address_entry['address'], list):
                subnet_names.extend([addr['name'] for addr in address_entry['address']])
            else:
                subnet_names.append(address_entry['address']['name'])
    subnet_names.append("any")
    return subnet_names

def find_zone_policies(from_zone, to_zone, raw_data):
    matching_policies = [policy['policy']['name'] for policy in raw_data if policy['from-zone-name'] == from_zone and policy['to-zone-name'] == to_zone]
    if matching_policies:
        print("The zones below already exist:")
        for idx, policy_name in enumerate(matching_policies, start=1):
            print(f"{idx}. {policy_name}")

def extract_policy_names(raw_data):
    policies_by_zone = {}
    zone_direction = []
    for entry in raw_data:
        from_zone = entry['from-zone-name']
        to_zone = entry['to-zone-name']
        zone_key = f"zone_{from_zone}_to_{to_zone}"
        if not any(d['from_zone'] == from_zone and d['to_zone'] == to_zone for d in zone_direction):
            zone_direction.append({'from_zone': from_zone, 'to_zone': to_zone})
        if zone_key not in policies_by_zone:
            policies_by_zone[zone_key] = {
                'from_zone': from_zone,
                'to_zone': to_zone,
                'policies': [],
                'description': []
            }
        policies = entry['policy'] if isinstance(entry['policy'], list) else [entry['policy']]
        for policy in policies:
            policy_name = policy['name']
            policy_description = policy.get('description')
            policies_by_zone[zone_key]['policies'].append(policy_name)
            policies_by_zone[zone_key]['description'].append(policy_description)
    return policies_by_zone, zone_direction

def check_exact_zone_match(zone_direction, from_zone, to_zone):
    is_present = None
    unmatched_zones = []
    for zone in zone_direction:
        if zone['from_zone'] == from_zone and zone['to_zone'] == to_zone:
            is_present = True
            break
        else:
            unmatched_zones.append(zone)
    if not is_present:
        return None, unmatched_zones
    else:
        return is_present, None
   

def gen_sec_policies_config(**kwargs):
    raw_data = kwargs.get('raw_data', [])
    get_vpn = vpn_manager.get_ipsec_vpn(get_vpn_name=True)
    zones = zone_manager.get_security_zone(get_zone_name=True)
    expected_combinations = len(zones) * (len(zones) - 1)
    policy_data = {}  
    zone_direction = []
    if raw_data:
        policy_data, zone_direction = extract_policy_names(raw_data)
        list_zones = list(policy_data.keys())
        if len(list_zones) != expected_combinations:
            list_zones = list(set(list_zones).union(generate_zone_directions(zones)))
    else:
        print("Automatically generating Security zone names")
        list_zones = generate_zone_directions(zones)
    zone_dir  = get_valid_selection("Please select the security zone direction: ", list_zones)
    from_zone, to_zone = zone_dir .split('_')[1], zone_dir .split('_')[-1]
    print(f"Selected from_zone: {from_zone}, to_zone: {to_zone}")
    if policy_data:
        zone_dir = update_zone_dir(policy_data, zone_dir )
    else:
        zone_dir = zone_dir 
    zone_dir  = confirm_policy_name(zone_dir)
    desc = get_valid_string("Enter policy description: ")
    addresses = address_manager.get_address_book(get_addresses=True)
    src_address_options = get_subnet_names_by_zone(addresses, from_zone)
    dst_address_options = get_subnet_names_by_zone(addresses, to_zone)
    src_address = get_valid_selection("Select source address: ", src_address_options)
    dst_address = get_valid_selection("Select Remote address: ", dst_address_options)
    application = get_valid_selection("Select application to allow: ", app)
    action = get_valid_selection("Selection match action: ", ["permit", "deny"])
    tunnel_config = get_tunnel_config(from_zone, to_zone, get_vpn, policy_data, zone_direction)
    policy_xml = build_policy_xml(from_zone, to_zone, zone_dir, desc, src_address, dst_address, application, action, tunnel_config)
    print(policy_xml)
    return policy_xml

def update_zone_dir(policy_data, zone_dir_choice):
    if any(zone_dir_choice == policy_key for policy_key in policy_data):
        new_zone_dir = get_valid_name(f"{zone_dir_choice} is already in use. Please enter a new zone direction name: ")
        return new_zone_dir
    return zone_dir_choice

def get_reverse_policy(policy_data, from_zone, to_zone):
    reverse_key = f'zone_{to_zone}_to_{from_zone}'
    if reverse_key in policy_data:
        return policy_data[reverse_key].get('policies', [])
    return []

def get_tunnel_config(from_zone, to_zone, get_vpn, policy_data, zone_direction):
    selected_vpn = pair_policy = ""
    choice = get_valid_selection("Enter valid Permit action", ['tunnel', 'None'])
    if choice == "tunnel":
        vpn_options = get_vpn 
        if vpn_options:
            selected = get_valid_selection("Enter IPsec VPN: ", vpn_options)
            reverse_policy = get_reverse_policy(policy_data, from_zone, to_zone)
            if reverse_policy:
                reverse_policy_choice = get_valid_selection("Select Pair: ", reverse_policy)
                pair_policy = f"<pair-policy operation='create'>{reverse_policy_choice}</pair-policy>"
            else:
                print("No reverse policy found. No pair policy will be created.")
            selected_vpn = f"<tunnel><ipsec-vpn>{selected}</ipsec-vpn>{pair_policy}</tunnel>"
        else:
            print("No VPN options available.")
    return selected_vpn

def build_policy_xml(from_zone, to_zone, zone_dir, desc, src_address, dst_address, application, action, tunnel_config):
    attribute = sub_attribute = ""
    return f"""
    <configuration>
        <security>
            <policies>
                <policy {attribute}>
                    <from-zone-name>{from_zone}</from-zone-name>
                    <to-zone-name>{to_zone}</to-zone-name>
                    <policy {sub_attribute}>
                        <name>{zone_dir}</name>
                        <description>{desc}</description>
                        <match>
                            <source-address>{src_address}</source-address>
                            <destination-address>{dst_address}</destination-address>
                            <application>{application}</application>
                        </match>
                        <then>
                            <{action}>
                                {tunnel_config}
                            </{action}>
                        </then>
                    </policy>
                </policy>
            </policies>
        </security>
    </configuration>""".strip()


def gen_update_config(raw_data):
    zones = zone_manager.get_security_zone(get_zone_name=True)
    list_zones = generate_zone_directions(zones)
    zone_dir = get_valid_selection("Please select traffic zone: ", list_zones)
    from_zone, to_zone = zone_dir.split('_')[1], zone_dir.split('_')[-1]
    policy_data, zone_direction = extract_policy_names(raw_data)
    selected_policies = selected_zone(raw_data, from_zone, to_zone)
    list_policy_names = [policy['name'] for policy in selected_policies]
    edit_policy_name = get_valid_selection("Please select a policy to view details: ", list_policy_names)
    selected_policy = next((policy for policy in selected_policies if policy['name'] == edit_policy_name), None)
    choice = display_and_select_policy_details(selected_policy, from_zone, to_zone, policy_data)
    print(choice)
    if not selected_policy:
        print("Selected policy not found.")
        return {}
    return selected_policy


def selected_zone(raw_data, from_zone, to_zone):
    selected_policies = []  
    for entry in raw_data:
        if entry['from-zone-name'] == from_zone and entry['to-zone-name'] == to_zone:
            if isinstance(entry['policy'], list):
                selected_policies = entry['policy']
            else:
                selected_policies = [entry['policy']]
            break 
    return selected_policies

def display_and_select_policy_details(selected_policy, from_zone, to_zone, policy_data):
    policy = selected_policy
    while True:
        keys = list(policy.keys())
        print("\nPlease select a detail to view or modify:")
        for index, key in enumerate(keys):
            value = policy[key]
            print(f"{index + 1}. {key}: {'{...}' if isinstance(value, dict) else value}")
        
        choice_input = input("Enter the number of the detail (0 to exit or 'back' to go up): ")
        if choice_input.isdigit():
            choice = int(choice_input) - 1
        else:
            if choice_input.lower() == 'back' or choice_input == '0':
                print("Exiting or going back.")
                break
            else:
                print("Invalid input. Please enter a number or 'back' to go up.")
                continue

        if 0 <= choice < len(keys):
            selected_key = keys[choice]
            selected_value = policy[selected_key]
            if isinstance(selected_value, dict):
                display_and_select_policy_details(selected_value, from_zone, to_zone, policy_data)
            else:
                if confirm_edit(f"Do you want to edit '{selected_key}'? (yes/no): "):
                    new_value = get_new_value(selected_key, from_zone, to_zone)
                    policy[selected_key] = new_value
                    return policy
        else:
            print("Invalid selection. Please try again.")

def confirm_edit(prompt):
    response = input(prompt)
    return response.lower() == 'yes'

def get_new_value(key, from_zone, to_zone, policy_data):
    if key in ['source-address', 'destination-address']:
        addresses = address_manager.get_address_book(get_addresses=True)
        address_options = get_subnet_names_by_zone(addresses, from_zone if key == 'source-address' else to_zone)
        return get_valid_selection(f"Select new {key}: ", address_options)
    elif key == 'application':
        return get_valid_selection("Enter new application to permit: ",app)
    elif key == 'description':
        return get_valid_string("Enter new description: ")
    elif key == "ipsec-vpn":
        get_vpn = vpn_manager.get_ipsec_vpn(get_vpn_name=True)
        return get_valid_selection("Select new Ipsec VPN tunnel: ",get_vpn)
    # elif key == "pair-policy":
    #         reverse_policy = get_reverse_policy(policy_data, from_zone, to_zone)
    #         if reverse_policy:
    #             reverse_policy_choice = get_valid_selection("Select Pair: ", reverse_policy)
    #             return get_valid_selection("Select new Pair-Policy:", )
    else:
        return get_valid_name(f"Enter new value for '{key}': ")
    
def confirm_deeper_navigation():
    response = input("Do you want to explore this section further? (yes/no): ")
    return response.lower() == 'yes'


def confirm_action(prompt):
    import re
    while True:
        user_input = input(prompt)
        if re.match(r'^(yes|no)$', user_input, re.IGNORECASE):
            return user_input.lower() == 'yes'
        else:
            print("Please enter 'yes' or 'no'.")