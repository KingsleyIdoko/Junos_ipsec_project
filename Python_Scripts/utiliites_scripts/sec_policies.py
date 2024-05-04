from utiliites_scripts.commons import get_valid_selection, get_valid_name, get_valid_string
from sec_addressbook import AddressBookManager
from sec_zone import SecurityZoneManager
from sec_ipsec_vpn import IpsecVpnManager
zone_manager = SecurityZoneManager()
address_manager = AddressBookManager()
vpn_manager = IpsecVpnManager()
import itertools, re

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
        choice = input(f"Automatically setting the policy_name to: {zone_dir}. Confirm? (yes/no) ")
        if re.match(pattern, choice, re.IGNORECASE):
            return choice.lower() == 'yes'

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
        old_policy_names = [policy for zone in policy_data.values() for policy in zone['policies']]
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
        reverse_policy = get_reverse_policy(policy_data, from_zone, to_zone)
    else:
        zone_dir = zone_dir 
        reverse_policy = []
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
        new_zone_dir = input(f"{zone_dir_choice} is already in use. Please enter a new zone direction name: ")
        return new_zone_dir
    return zone_dir_choice

def get_reverse_policy(policy_data, from_zone, to_zone):
    reverse_key = f'zone_{to_zone}_to_{from_zone}'
    if reverse_key in policy_data:
        return policy_data[reverse_key].get('policies', [])
    return []

def get_tunnel_config(from_zone, to_zone, get_vpn, policy_data, zone_direction):
    selected_vpn = pair_policy = ""
    if not policy_data:
        print("No policy data available.")
        return ""
    choice = get_valid_selection("Enter valid Permit action", ['tunnel', 'None'])
    if choice == "tunnel":
        vpn_options = get_vpn()  
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
