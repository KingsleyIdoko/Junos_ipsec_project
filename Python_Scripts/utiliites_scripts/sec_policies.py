from utiliites_scripts.commons import (get_valid_selection, get_valid_name, get_valid_string, validate_yes_no, 
                                       get_policy_names_by_zone,generate_zone_directions)
from sec_addressbook import AddressBookManager
from sec_zone import SecurityZoneManager
from sec_ipsec_vpn import IpsecVpnManager
zone_manager = SecurityZoneManager()
address_manager = AddressBookManager()
vpn_manager = IpsecVpnManager()
import itertools, re

app = ["any","junos-aol","junos-bgp","junos-biff","junos-bootpc","junos-bootps","junos-defaults","junos-dhcp-client","junos-dhcp-relay","junos-dhcp-server",    
  "junos-discard","junos-dns-tcp","junos-dns-udp","junos-echo","junos-finger","junos-ftp","junos-ftp-data"]
actions = ["permit", "deny","log","reject"]


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
        if 'attach' in address_entry and 'zone' in address_entry['attach'] and address_entry['attach']['zone']['name'] == zone_name:
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
    for zone in zone_direction:
        if zone['from_zone'] == from_zone and zone['to_zone'] == to_zone:
            return True, zone  
    return False, None  


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
    from_zone, to_zone = zone_dir.split('_')[1], zone_dir .split('_')[-1]
    old_policy_names = get_policy_names_by_zone(raw_data, from_zone, to_zone)
    print(f"Selected from_zone: {from_zone}, to_zone: {to_zone}")
    if policy_data:
        zone_dir = update_zone_dir(policy_data, zone_dir )
    else:
        zone_dir = zone_dir 
    zone_dir  = confirm_policy_name(zone_dir)
    desc = get_valid_string("Enter policy description: ")
    addresses, *_ = address_manager.get_address_book(get_addresses=True)
    if not addresses:
        print("Address book is empty. Please create addresses and try again")
        return None
    src_address_options = get_subnet_names_by_zone(addresses, from_zone)
    dst_address_options = get_subnet_names_by_zone(addresses, to_zone)
    src_address = get_valid_selection("Select source address: ", src_address_options)
    dst_address = get_valid_selection("Select Remote address: ", dst_address_options)
    application = get_valid_selection("Select application to allow: ", app)
    action = get_valid_selection("Selection match action: ", actions )
    tunnel_config = get_tunnel_config(from_zone, to_zone, get_vpn, policy_data, zone_direction)
    policy_parameters = {
        'from_zone': from_zone,
        'to_zone': to_zone,
        'zone_dir': zone_dir,
        'desc': desc,
        'src_address': src_address,
        'dst_address': dst_address,
        'application': application,
        'action': action,
        'tunnel_config': tunnel_config,
        'raw_data': raw_data,
        'old_policy_names': old_policy_names,
        'zone_direction': zone_direction
    }
    policy_xml = build_policy_xml(**policy_parameters)
    return policy_xml

def update_zone_dir(policy_data, zone_dir_choice):
    if any(zone_dir_choice == policy_key for policy_key in policy_data):       
        new_zone_dir = get_valid_name(f"{zone_dir_choice} is already in use. Please enter a new zone direction name: ")
        return new_zone_dir
    return zone_dir_choice

def get_reverse_policy(policies, from_zone, to_zone):
    return [policy['name'] for policy in policies] if policies else []

def get_tunnel_config(from_zone, to_zone, get_vpn, policy_data, zone_direction):
    selected_vpn = pair_policy = ""
    choice = get_valid_selection("Enter valid Permit action", ['tunnel', 'None'])
    if choice == "tunnel":
        if get_vpn:
            selected = get_valid_selection("Enter IPsec VPN: ", get_vpn)
            reverse_policy = get_reverse_policy(policy_data, from_zone, to_zone)
            if reverse_policy:
                reverse_policy_choice = get_valid_selection("Select Pair: ", reverse_policy)
                pair_policy = f"""<pair-policy>{reverse_policy_choice}</pair-policy>"""
            else:
                print("No reverse policy found. No pair policy will be created.")
            selected_vpn = f"""<tunnel>
                                    <ipsec-vpn>{selected}</ipsec-vpn>
                                    {pair_policy}
                               </tunnel>"""
        else:
            print("No VPN options available.")
    return selected_vpn

def extract_policy_parameters(kwargs):
    from_zone = kwargs.get('from_zone')
    to_zone = kwargs.get('to_zone')
    zone_dir = kwargs.get('zone_dir')
    desc = kwargs.get('desc')
    src_address = kwargs.get('src_address')
    dst_address = kwargs.get('dst_address')
    application = kwargs.get('application')
    action = kwargs.get('action')
    tunnel_config = kwargs.get('tunnel_config')
    raw_data = kwargs.get('raw_data')
    old_policy_names = kwargs.get('old_policy_names')
    zone_direction = kwargs.get('zone_direction')
    attribute = sub_attribute = ""
    return (from_zone, to_zone, zone_dir, desc, src_address, dst_address, application, 
            action, tunnel_config, raw_data, old_policy_names, zone_direction, attribute, sub_attribute)

def build_policy_xml(**kwargs):
    (from_zone, to_zone, zone_dir, desc, src_address, dst_address, application, action, 
    tunnel_config, raw_data, old_policy_names, zone_direction, attribute, sub_attribute) = extract_policy_parameters(kwargs)
    if raw_data:
        is_present, existing_zone = check_exact_zone_match(zone_direction, from_zone, to_zone)
        if is_present:
            if zone_dir != old_policy_names[-1]:
                sub_attribute = f"""insert="after" key="[name='{old_policy_names[-1]}']" operation="create" """
        else:
            attribute = f"""insert="after" key="[from-zone-name={from_zone} to-zone-name={to_zone}]" operation="create" """

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
                                {tunnel_config if tunnel_config else ""}
                            </{action}>
                        </then>
                    </policy>
                </policy>
            </policies>
        </security>
    </configuration>""".strip()


def initial_setup_and_selection(raw_data):
    old_policy_data = []
    zones = zone_manager.get_security_zone(get_zone_name=True)
    get_vpn = vpn_manager.get_ipsec_vpn(get_vpn_name=True)
    list_zones = generate_zone_directions(zones)
    zone_dir = get_valid_selection("Please select traffic zone: ", list_zones)
    from_zone, to_zone = zone_dir.split('_')[1], zone_dir.split('_')[-1]
    old_policy_data.extend([from_zone, to_zone])
    policy_names = get_policy_names_by_zone(raw_data, from_zone, to_zone)
    selected_policies, reverse_policy = selected_zone_with_reverse(raw_data, from_zone, to_zone)
    reverse_policy = [reverse_policy] if isinstance(reverse_policy, dict) else reverse_policy
    reverse_policy_names = [rev_policy['name'] for rev_policy in reverse_policy]
    edit_policy_name = get_valid_selection("Please select a policy to view details: ", policy_names)
    selected_policies = [selected_policies] if isinstance(selected_policies, dict) else selected_policies
    selected_policy = next((policy for policy in selected_policies if policy['name'] == edit_policy_name), None)
    if not selected_policy:
        print("Policy not found.")
        return None, None, None, None, None
    return selected_policy, reverse_policy_names, from_zone, to_zone, old_policy_data

def update_policy_loop(selected_policy, reverse_policy_names, from_zone, to_zone):
    continue_update = True
    while continue_update:
        policy_then = selected_policy.get('then', {})
        details = extract_policy_details(policy_then)
        action = list(policy_then.keys())[0] if policy_then else None
        traffic = list(policy_then[action].keys())[0] if action and policy_then[action] else None
        pair_policy = details.get(f"{action}_{traffic}_ipsec-vpn") if action and traffic else None
        attributes = {
            "name": selected_policy.get('name'),
            "description": selected_policy.get('description'),
            "source_address": selected_policy['match'].get('source-address'),
            "destination_address": selected_policy['match'].get('destination-address'),
            "application": selected_policy['match'].get('application'),
            "action": action,
            "traffic": traffic,
            "pair_policy": pair_policy
        }
        attribute_keys = [f"{key}: {value}" for key, value in attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update: ", attribute_keys)
        selected_key = selected_attribute.split(':')[0].strip()
        if selected_key == 'source_address':
            addresses, *_ = address_manager.get_address_book(get_addresses=True)
            src_address_options = get_subnet_names_by_zone(addresses, from_zone)
            new_value = get_valid_selection("Select source address: ", src_address_options)
            selected_policy['match'][selected_key.replace('_', '-')] = new_value
            attributes[selected_key] = new_value
        elif selected_key == 'destination_address':
            addresses, *_ = address_manager.get_address_book(get_addresses=True)
            dst_address_options = get_subnet_names_by_zone(addresses, to_zone)
            new_value = get_valid_selection("Select destination address: ", dst_address_options)
            selected_policy['match'][selected_key.replace('_', '-')] = new_value
            attributes[selected_key] = new_value
        elif selected_key == 'application':
            new_value = get_valid_selection("Select application to allow: ", app)
            selected_policy['match'][selected_key.replace('_', '-')] = new_value
            attributes[selected_key] = new_value
        elif selected_key == 'action':
            new_value = get_valid_selection(f"Enter new value for {selected_key}: ", ['permit', 'deny'])
            selected_policy['then'] = {new_value: {}}
            traffic_type = get_valid_selection("Specify the traffic type: ", ["None", "tunnel"])
            if traffic_type == 'tunnel':
                vpn_names = vpn_manager.get_ipsec_vpn(get_vpn_name=True)
                tunnel_name = get_valid_selection("Select ipsec vpn name: ", vpn_names)
                selected_policy['then'][new_value] = {'tunnel': {'ipsec-vpn': tunnel_name}}
                pair_policy_name = get_valid_selection("Select pair policy names: ", reverse_policy_names)
                selected_policy['then'][new_value]['tunnel']['pair-policy'] = pair_policy_name
            else:
                selected_policy['then'][new_value] = None
        elif selected_key == 'traffic':
            new_value = get_valid_selection(f"Enter new value for {selected_key}: ", ['tunnel', 'None'])
            if new_value == 'tunnel':
                vpn_names = vpn_manager.get_ipsec_vpn(get_vpn_name=True)
                tunnel_name = get_valid_selection("Select ipsec vpn name: ", vpn_names)
                selected_policy['then'][action] = {'tunnel': {'ipsec-vpn': tunnel_name}}
                pair_policy_name = get_valid_selection("Select pair policy names: ", reverse_policy_names)
                selected_policy['then'][action]['tunnel']['pair-policy'] = pair_policy_name
            else:
                selected_policy['then'] = {'permit': None}
        elif selected_key == 'pair_policy':
            new_value = get_valid_selection("Select pair policy names: ", reverse_policy_names)
            selected_policy['then'][action][traffic]['pair-policy'] = new_value
        continue_update = validate_yes_no("Do you want to continue updating? (yes/no): ")

def gen_update_config(raw_data):
    selected_policy, reverse_policy_names, from_zone, to_zone, old_policy_data = initial_setup_and_selection(raw_data)
    if selected_policy:
        update_policy_loop(selected_policy, reverse_policy_names, from_zone, to_zone)








    # sub_attribute = ""
    # if len(policy_names) > 1:
    #     try:
    #         index = policy_names.index(edit_policy_name)
    #         if index + 1 < len(policy_names):
    #             sub_attribute = f"insert=\"after\" key=\"[name='{policy_names[index + 1]}']\" operation=\"create\""
    #     except ValueError:
    #         pass
    # payload = f"""
    # <configuration>
    #     <security>
    #         <policies>
    #             <policy {attribute}>
    #                 <from-zone-name>{from_zone}</from-zone-name>
    #                 <to-zone-name>{to_zone}</to-zone-name>
    #                 <policy {sub_attribute}>
    #                     <name>{updated['name']}</name>
    #                     <description>{updated['description']}</description>
    #                     <match>
    #                         <source-address>{updated['match']['source-address']}</source-address>
    #                         <destination-address>{updated['match']['destination-address']}</destination-address>
    #                         <application>{updated['match']['application']}</application>
    #                     </match>
    #                     <then>
    #                         <{updated_action}>
    #                             {tunnel_config_xml}
    #                         </{updated_action}>
    #                     </then>
    #                 </policy>
    #             </policy>
    #         </policies>
    #     </security>
    # </configuration>""".strip()
    # return (payload, None) if old_policy_name == updated['name'] else (payload, old_policy_data)

def extract_policy_details(policy_then):
    result = {}
    def recursive_extraction(d, parent_key=''):
        if d is None:
            result[parent_key] = None
            return
        for k, v in d.items():
            new_key = parent_key + '_' + k if parent_key else k
            if isinstance(v, dict):
                recursive_extraction(v, new_key)
            else:
                result[new_key] = v
    recursive_extraction(policy_then)
    return result


def selected_zone_with_reverse(raw_data, from_zone, to_zone):
    selected_policies = []
    reverse_policies = []
    for entry in raw_data:
        if entry['from-zone-name'] == from_zone and entry['to-zone-name'] == to_zone:
            selected_policies = entry['policy']
        elif entry['from-zone-name'] == to_zone and entry['to-zone-name'] == from_zone:
            reverse_policies = entry['policy']
    return selected_policies, reverse_policies


def get_new_value(key, from_zone, to_zone, reverse_policy):
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
    elif key == "pair-policy":
            reverse_policy = get_reverse_policy(reverse_policy, from_zone, to_zone)
            if reverse_policy:
                return get_valid_selection("Select Pair: ", reverse_policy)
            print("No reverse policy exist on the device")
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

 
def gen_delete_config(raw_data, old_policy_name=None):
    if old_policy_name:
        from_zone, to_zone, selected_policy_name = old_policy_name
    else:
        zones = zone_manager.get_security_zone(get_zone_name=True)
        list_zones = generate_zone_directions(zones)
        zone_dir = get_valid_selection("Please select traffic zone: ", list_zones)
        from_zone, to_zone = zone_dir.split('_')[1], zone_dir.split('_')[-1]
        policy_names = get_policy_names_by_zone(raw_data, from_zone, to_zone)
        selected_policy_name = get_valid_selection("Please select a policy to view details: ", policy_names)
    payload = f"""
    <configuration>
        <security>
            <policies>
                <policy>
                    <from-zone-name>{from_zone}</from-zone-name>
                    <to-zone-name>{to_zone}</to-zone-name>
                    <policy operation="delete">
                        <name>{selected_policy_name}</name>
                    </policy>
                </policy>
            </policies>
        </security>
    </configuration>""".strip()
    return payload

def re_order_policy(raw_data):
    zones = zone_manager.get_security_zone(get_zone_name=True)
    list_zones = generate_zone_directions(zones)
    zone_dir = get_valid_selection("Please select traffic zone: ", list_zones)
    from_zone, to_zone = zone_dir.split('_')[1], zone_dir.split('_')[-1]
    policy_names = get_policy_names_by_zone(raw_data, from_zone, to_zone)
    if len(policy_names) <= 1:
        print("Only one policy exists and cannot be re-ordered.")
        return None
    selected_name = get_valid_selection("Select Policy you want to re-order: ", policy_names)
    policy_names.remove(selected_name)
    position = get_valid_selection("Move selected  security policy: ", ["before", "after"])
    if position == "before" and policy_names:
        new_position_policy = get_valid_selection("Select selected security Policy to position before: ", policy_names)
        if policy_names.index(new_position_policy) == 0:
            key = "insert=\"first\""
        else:
            key = f"insert=\"before\" key=\"[ name='{new_position_policy}' ]\""
    elif position == "after" and policy_names:
        new_position_policy = get_valid_selection("Select Security Policy to position after: ", policy_names)
        if policy_names.index(new_position_policy) == len(policy_names) - 1:
            key = f"insert=\"after\" key=\"[ name='{policy_names[-1]}' ]\""
        else:
            key = f"insert=\"after\" key=\"[ name='{new_position_policy}' ]\""
    else:
        key = "insert=\"first\""
    
    policy_config = f"""<policy {key} operation=\"merge\"> 
                        <name>{selected_name}</name> 
                    </policy>"""
    payload = f"""
    <configuration>
        <security>
            <policies>
                <policy>
                    <from-zone-name>{from_zone}</from-zone-name>
                    <to-zone-name>{to_zone}</to-zone-name>
                    {policy_config}
                </policy>
            </policies>
        </security>
    </configuration>""".strip()
    return payload


    


