from utiliites_scripts.commons import get_valid_selection, get_valid_name, get_valid_string
from sec_addressbook import AddressBookManager
from sec_zone import SecurityZoneManager
from sec_ipsec_vpn import IpsecVpnManager
zone_manager = SecurityZoneManager()
address_manager = AddressBookManager()
vpn_manager = IpsecVpnManager()
import itertools

app = ["any","junos-aol","junos-bgp","junos-biff","junos-bootpc","junos-bootps","junos-defaults","junos-dhcp-client","junos-dhcp-relay","junos-dhcp-server",    
  "junos-discard","junos-dns-tcp","junos-dns-udp","junos-echo","junos-finger","junos-ftp","junos-ftp-data"]

def gen_sec_policies_config(**kwargs):
    raw_data = kwargs.get('raw_data', [])
    get_vpn = vpn_manager.get_ipsec_vpn(get_vpn_name=True)
    zones = zone_manager.get_security_zone(get_zone_name=True)
    expected_combinations = len(zones) * (len(zones) - 1)
    if raw_data:
        policy_data, zone_direction = extract_policy_names(raw_data)
        list_zones = list(policy_data.keys())
        if len(list_zones) != expected_combinations:
            new_list_zones = generate_zone_directions(zones)
            list_zones = list(set(list_zones).union(new_list_zones))
    else:
        print("Automatically generating Security zone names")
        list_zones = generate_zone_directions(zones)
    zone_dir = get_valid_selection("Please select the security zone direction: ", list_zones)
    from_zone, to_zone = zone_dir.split('_')[1], zone_dir.split('_')[-1]
    print(f"Selected from_zone: {from_zone}, to_zone: {to_zone}")
    print(f"set new policy name to {zone_dir}")
    desc = get_valid_string("Enter policy description: ")
    addresses = address_manager.get_address_book(get_addresses=True)
    src_addresses = get_subnet_names_by_zone(addresses, from_zone)
    dst_addresses = get_subnet_names_by_zone(addresses, to_zone)
    src_addres = [addr for addr in src_addresses]
    src_address = get_valid_selection("Select source address: ", src_addres)
    dest_addres = [addr for addr in dst_addresses]
    dst_address = get_valid_selection("Select Remote address: ", dest_addres)
    application = get_valid_selection("Select application to allow: ", app)
    action = get_valid_selection("Selection match action: ", ["permit", "deny"])
    selected_vpn = get_valid_selection("Enter IPsec VPN: ", get_vpn)
    if raw_data:
        is_present, existing_zone = check_exact_zone_match(zone_direction, from_zone, to_zone)
        if existing_zone:
            for zonn in existing_zone:
                attribute =  f""" insert="after"  key="[ from-zone-name={zonn.get('from_zone')}to-zone-name={zonn.get('to_zone')} ]" operation="create"""
        sub_attribute = f""" insert="after"  key="[ name='zone_trust_to_untrust' ]" operation="create"""
    payload = f"""
        <configuration>
                <security>
                    <policies {attribute}>
                        <policy>
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
                                        <tunnel>
                                            <ipsec-vpn>{selected_vpn}</ipsec-vpn>
                                        </tunnel>
                                    </{action}>
                                </then>     
                            </policy>       
                        </policy>           
                    </policies>             
                </security>                 
        </configuration>""".strip()
    print(payload)
    return payload

def generate_zone_directions(zones):
    if len(zones) < 2:
        raise ValueError("At least two zones are needed to create directions.")
    directions = []
    for first_zone, second_zone in itertools.combinations(zones, 2):
        directions.append(f"zone_{first_zone}_to_{second_zone}")
        directions.append(f"zone_{second_zone}_to_{first_zone}")
    return directions

def get_subnet_names_by_zone(addresses, zone_name):
    subnet_names = []
    for address_entry in addresses:
        if address_entry['attach']['zone']['name'] == zone_name:
            if isinstance(address_entry['address'], list):
                subnet_names.extend([addr['name'] for addr in address_entry['address']])
            else:
                subnet_names.append(address_entry['address']['name'])
    return subnet_names

def find_zone_policies(from_zone, to_zone, raw_data):
    matching_policies = [policy['policy']['name'] for policy in raw_data if policy['from-zone-name'] == from_zone and policy['to-zone-name'] == to_zone]
    if matching_policies:
        print("The zones below already exist:")
        for idx, policy_name in enumerate(matching_policies, start=1):
            print(f"{idx}. {policy_name}")


def get_subnet_names_by_zone(address_book, zone_name):
    subnets = []
    for addr_book in address_book:
        if addr_book['attach']['zone']['name'] == zone_name:
            for addr in addr_book['address']:
                subnets.append(addr['name'])
    return subnets

def extract_policy_names(data):
    policies_by_zone = {}
    zone_direction = []
    if data:
        for entry in data:
            from_zone = entry['from-zone-name']
            to_zone = entry['to-zone-name']
            zone_key = f"zone_{from_zone}_to_{to_zone}"
            if not any(d['from_zone'] == from_zone and d['to_zone'] == to_zone for d in zone_direction):
                zone_direction.append({'from_zone': from_zone, 'to_zone': to_zone})
            if zone_key not in policies_by_zone:
                policies_by_zone[zone_key] = {
                    'from_zone': from_zone,
                    'to_zone': to_zone,
                    'policies': []
                }
            policies = entry['policy'] if isinstance(entry['policy'], list) else [entry['policy']]
            for policy in policies:
                policy_name = policy['name']
                policies_by_zone[zone_key]['policies'].append(policy_name)
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


