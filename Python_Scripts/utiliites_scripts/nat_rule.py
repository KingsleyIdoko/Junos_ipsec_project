from utiliites_scripts.selectprefix import select_prefix
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.commons import (get_valid_selection,multiple_selection, get_valid_network_address, 
                                       get_valid_name, generate_zone_directions, validate_yes_no)
from sec_zone import SecurityZoneManager
from sec_addressbook import AddressBookManager
from sec_nat_pool import NatPoolManager
pool_manager = NatPoolManager()
zone_manager = SecurityZoneManager()
address_manager = AddressBookManager()
addresses = address_manager.get_address_book()
protocol =  ["ah","egp","esp","gre","icmp","ospf","pim","rsvp","sctp", "tcp","udp"]

def generate_nat_rule_config(nat_type,nat_data):
    if nat_data:
        rule_list, global_name, from_zone, to_zone, rule_name = process_nat_data(nat_data)
    else:
        global_name = get_valid_name("Enter nat global name: ")
        zones = zone_manager.get_security_zone(get_zone_name=True)
        list_zones = generate_zone_directions(zones)
        zone_dir  = get_valid_selection("Please select the security zone direction: ", list_zones)
        from_zone, to_zone = zone_dir.split('_')[1], zone_dir .split('_')[-1]
        rule_name = generate_next_rule_name(rule_list)
    selection = get_valid_selection("Select prefixes from?", ["address_book", "Manual"])
    if selection == "address_book":
        print("Fetching addresses from address_book to match...\n")
        source_address = grab_address(addresses[0])
        print(f"Source address is set: {source_address}")
        print("Selecting destination prefixes to nat...\n")
        dest_address = grab_address(addresses[0])
        print(f"Destination address is set: {dest_address}")
    elif selection == "Manual":
        print("Manually specify source/destination prefixes to match:")
        source_address = [get_valid_network_address("Specify valid source address: ")]
        dest_address = [get_valid_network_address("Specify valid destination address: ")]
    payload = nat_policy(global_name=global_name, from_zone=from_zone, to_zone=to_zone, 
                            rule_name=rule_name, source_address=source_address, 
                            dest_address=dest_address, nat_type=nat_type, rule_list=rule_list)
    return payload

def initialize_kwargs(kwargs):
    attribute = ""
    nat_types = kwargs.get("nat_type", {})
    source_prefixes = kwargs.get("source_address", [])
    remote_prefixes = kwargs.get("dest_address", [])
    global_name = kwargs.get("global_name", "")
    from_zone = kwargs.get("from_zone", "")
    to_zone = kwargs.get("to_zone", "")
    rule_name = kwargs.get("rule_name", "")
    rule_list = kwargs.get("rule_list", [])
    source_nat = kwargs.get("source_nat", {})
    track_changes = kwargs.get("track_changes", {})
    src_prefixes = []
    dest_prefixes = []
    xml_components = []
    return attribute, nat_types, source_prefixes, remote_prefixes, global_name, from_zone, to_zone, rule_name, rule_list, source_nat, track_changes, src_prefixes, dest_prefixes, xml_components

def create_payload(global_name, from_zone, to_zone, dele_rule_name, attribute, rule_name, formatted_src_prefixes, formatted_dest_prefixes, formatted_nat):
    payload = f"""
        <configuration>
            <security>
                <nat>
                    <source>
                        <rule-set>
                            <name>{global_name}</name>
                            <from><zone>{from_zone}</zone></from>
                            <to><zone>{to_zone}</zone></to>
                            {dele_rule_name}
                            <rule {attribute}>
                                <name>{rule_name}</name>
                                <src-nat-rule-match>
                                    {formatted_src_prefixes}
                                    {formatted_dest_prefixes}
                                </src-nat-rule-match>
                                <then>
                                    {formatted_nat}
                                </then>
                            </rule>
                        </rule-set>
                    </source>
                </nat>
            </security>
        </configuration>
        """
    return payload.strip()

def nat_policy(**kwargs):
    attribute, nat_types, source_prefixes, remote_prefixes, global_name, from_zone, to_zone, rule_name, rule_list, source_nat, track_changes, src_prefixes, dest_prefixes, xml_components = initialize_kwargs(kwargs)
    if source_nat:
        if isinstance(source_nat, dict):
            pool_name = source_nat['pool']['pool-name']
            xml_components.append(f"<source-nat><pool><pool-name>{pool_name}</pool-name></pool></source-nat>")
        elif source_nat == "off":
            xml_components.append("<source-nat><off/></source-nat>")
        elif source_nat == "interface":
            xml_components.append("<source-nat><interface></interface></source-nat>")
    else:
        for type_key, type_value in nat_types.items():
            if type_key == 'off':
                xml_components.append("<source-nat><off/></source-nat>")
            elif type_key == 'interface':
                xml_components.append("<source-nat><interface></interface></source-nat>")
            elif type_key == 'pool':
                nat_pool, *_ = pool_manager.get_nat(get_pool_names=True)
                if isinstance(nat_pool, dict):
                    nat_pool = [nat_pool]
                pool_names = [pool['name'] for pool in nat_pool]
                pool_name = get_valid_selection("Select pool names: ", pool_names)
                xml_components.append(f"<source-nat><pool><pool-name>{pool_name}</pool-name></pool></source-nat>")

    if 'name' in track_changes and track_changes.get("name") in rule_list:
        dele_rule_name = f"""<rule operation="delete"><name>{track_changes['name']}</name></rule>"""
    else:
        dele_rule_name = ""
    if source_prefixes:
        if not isinstance(source_prefixes, list):
            source_prefixes = [source_prefixes]
        if 'source-address' in track_changes and dele_rule_name != "":
            src_prefixes.append(f"""<source-address operation="delete"/>""")
        for src_prefix in source_prefixes:
            src_prefixes.append(f"<source-address>{src_prefix}</source-address>")

    if remote_prefixes:
        if not isinstance(remote_prefixes, list):
            remote_prefixes = [remote_prefixes]
        if 'destination-address' in track_changes and dele_rule_name != "":
            dest_prefixes.append(f"""<destination-address operation="delete"/>""")
        for dst_prefix in remote_prefixes:
            dest_prefixes.append(f"<destination-address>{dst_prefix}</destination-address>")

    formatted_src_prefixes = "\n                              ".join(src_prefixes)
    formatted_dest_prefixes = "\n                             ".join(dest_prefixes)
    formatted_nat = "\n                        ".join(xml_components)
    attribute = determine_attribute(rule_list, rule_name, track_changes, dele_rule_name)
    payload = create_payload(global_name, from_zone, to_zone, dele_rule_name, attribute, rule_name, 
                             formatted_src_prefixes, formatted_dest_prefixes, formatted_nat)
    print(payload)
    return payload.strip()


def extract_nat_config(nat_data):
    selected_data = []
    if isinstance(nat_data, dict):
        nat_data = [nat_data]
    for data in nat_data:
        global_nat_rule = data.get('name')
        from_zone = data['from'].get('zone')
        to_zone = data['to'].get('zone')
        rules_list = []
        if isinstance(data['rule'], list):
            rules_list = [rule['name'] for rule in data['rule']]
        else:
            rules_list.append(data['rule']['name'])
    selected_data.append({
        'global_name': global_nat_rule,
        'from_zone': from_zone,
        'to_zone': to_zone,
        'rules_list': rules_list
    })
    return selected_data

def grab_address(addresses):
    address_names = [items['name'] for items in addresses]
    choice = get_valid_selection("Select address_book to choose from: ", address_names)
    selected_item = next(items for items in addresses if items['name'] == choice)
    if isinstance(selected_item['address'], dict):
        address = [selected_item['address']]
    else:
        address = selected_item['address']
    address_names = [addr['name'] for addr in address]
    selections = multiple_selection("Select address_book child addresses", address_names)
    selected_addresses = [addr['ip-prefix'] for addr in address if addr['name'] in selections]
    return selected_addresses

def generate_next_rule_name(rule_names):
    if not rule_names:
        return 'rule1'
    rule_numbers = sorted([int(name.replace('rule', '')) for name in rule_names])
    for i in range(1, rule_numbers[-1] + 1):
        if i not in rule_numbers:
            return f'rule{i}'
    return f'rule{rule_numbers[-1] + 1}'

def gen_nat_update_config(rule_set, nat_data):
    track_changes = {}  # Dictionary to track changes
    rule_list = [rule['rules_list'] for rule in nat_data]
    nat_pool, *_ = pool_manager.get_nat(get_pool_names=True)
    pool_names = [rule['name'] for rule in nat_pool]
    choice = get_valid_selection("Specify the rule to update", *rule_list)
    selected_rule = next((rule for rule in rule_set['rule'] if rule['name'] == choice), None)
    continue_update = True
    old_attributes = selected_rule.copy()
    
    while continue_update:
        rule_attributes = {
            'name': selected_rule.get('name'),
            'source-address': selected_rule.get('src-nat-rule-match', {}).get('source-address'),
            'destination-address': selected_rule.get('src-nat-rule-match', {}).get('destination-address'),
            'source-nat': 'pool' if 'pool' in selected_rule.get('then', {}).get('source-nat', {}) else 'interface' if 'interface' in selected_rule.get('then', {}).get('source-nat', {}) else 'off',
            'pool-name': selected_rule.get('then', {}).get('source-nat', {}).get('pool', {}).get('pool-name') if 'pool' in selected_rule.get('then', {}).get('source-nat', {}) else None
        }
        
        attribute_keys = [f"{key}: {value}" for key, value in rule_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        selected_key = selected_attribute.split(':')[0].strip()
        
        if selected_key == 'name':
            new_value = get_valid_name(f"Enter new rule name for {selected_rule[selected_key]}: ")
            track_changes['name'] = selected_rule[selected_key]
            selected_rule['name'] = new_value

        elif selected_key == 'source-address':
            new_value = grab_address(addresses[0])
            track_changes['source-address'] = selected_rule['src-nat-rule-match']['source-address']
            selected_rule['src-nat-rule-match']['source-address'] = new_value

        elif selected_key == 'destination-address':
            new_value = grab_address(addresses[0])
            track_changes['destination-address'] = selected_rule['src-nat-rule-match']['destination-address']
            selected_rule['src-nat-rule-match']['destination-address'] = new_value

        elif selected_key == 'source-nat':
            choice = get_valid_selection("Change nat_type : ", ['interface', 'pool', 'off'])
            if choice != selected_rule['then'].get('source-nat'):
                track_changes['source-nat'] = selected_rule['then'].get('source-nat')
                if choice == 'interface':
                    selected_rule['then']['source-nat'] = 'interface'
                elif choice == 'off':
                    selected_rule['then']['source-nat'] = 'off'
                elif choice == "pool":
                    new_value = get_valid_selection("Select new pool name", pool_names)
                    selected_rule['then']['source-nat'] = {'pool': {'pool-name': new_value}}

        elif selected_key == 'pool-name':
            new_value = get_valid_selection("Select new pool name", pool_names)
            if new_value != selected_rule['then'].get('source-nat', {}).get('pool', {}).get('pool-name'):
                track_changes['pool-name'] = selected_rule['then'].get('source-nat', {}).get('pool', {}).get('pool-name')
                selected_rule['then']['source-nat'] = {'pool': {'pool-name': new_value}}

        continue_update = validate_yes_no("Do you want to continue updating this rule (yes/no): ") == True

    rule_list, global_name, from_zone, to_zone, *_ = process_nat_data(nat_data)
    rule_name = selected_rule.get('name')
    source_address = selected_rule['src-nat-rule-match'].get('source-address')
    dest_address = selected_rule['src-nat-rule-match'].get('destination-address')
    source_nat = selected_rule['then'].get('source-nat')
    pool_name = source_nat['pool']['pool-name'] if isinstance(source_nat, dict) else None
    payload = nat_policy(global_name=global_name, from_zone=from_zone, to_zone=to_zone,rule_name=rule_name, 
                         source_address=source_address, pool_name=pool_name,dest_address=dest_address, 
                         source_nat=source_nat, rule_list=rule_list, track_changes=track_changes)
    return payload



def process_nat_data(nat_data):
    rule_list = []
    if nat_data:
        for data in nat_data:
            print("Using existing nat rule configs")
            global_name = data.get("global_name")
            print(f"Global nat name is set: {global_name}")
            from_zone = data.get("from_zone")
            print(f"from_zone is set to: {from_zone}")
            to_zone = data.get("to_zone")
            print(f"to_zone is set to {to_zone}")
            rule_list = data.get('rules_list')
            rule_name = generate_next_rule_name(rule_list)  
    return rule_list, global_name, from_zone, to_zone, rule_name




def determine_attribute(
    rule_list: list, 
    rule_name: str, 
    track_changes: dict, 
    dele_rule_name: str
) -> str:
    """
    Determines the attribute for the XML rule insertion based on the given parameters.

    Parameters:
    rule_list (list): List of existing rule names.
    rule_name (str): The name of the current rule.
    track_changes (dict): Dictionary tracking changes that need to be applied.
    dele_rule_name (str): The delete rule XML string if a rule is marked for deletion.

    Returns:
    str: The attribute string for the XML rule insertion.
    """
    attribute = ""
    if rule_list and len(rule_list) >= 1:
        if rule_name != rule_list[-1]:
            if not track_changes:
                attribute = f""" insert="after"  key="[ name='{rule_list[-1]}' ]" operation="create" """
            elif dele_rule_name != "":
                if track_changes.get("name") != rule_list[-1]:
                    attribute = f""" insert="after"  key="[ name='{rule_list[-1]}' ]" operation="create" """
                else:
                    try:
                        attribute = f""" insert="after"  key="[ name='{rule_list[-2]}' ]" operation="create" """
                    except IndexError:
                        attribute = ""
    return attribute


def gen_delete_nat_rule(**kwargs) -> str:
    """
    Generates an XML payload to delete a NAT rule based on the provided parameters.
    Parameters:
    kwargs (dict): Dictionary containing 'nat_data' which is a list of dictionaries.
                   Each dictionary should contain 'global_name', 'from_zone', 'to_zone', and 'rules_list'.
    Returns:
    str: The XML payload for deleting the specified NAT rule.
    """
    nat_data = kwargs.get("nat_data")
    for params in nat_data:
        global_name = params.get('global_name')
        rule_list = params.get("rules_list")
        rule_name = get_valid_selection("Select nat rules for delete: ", rule_list)
        
        payload = f"""
        <configuration>
            <security>
                <nat>
                    <source>
                        <rule-set>
                            <name>{global_name}</name>
                            <rule operation="delete">
                                <name>{rule_name}</name>
                            </rule>
                        </rule-set>
                    </source>
                </nat>
            </security>
        </configuration>""".strip()
        print(payload)
        return payload


def order_nat_rule(nat_data):
    for params in nat_data:
        global_name = params.get('global_name')
        rule_list = params.get("rules_list")
        
        if len(rule_list) <= 1:
            print("Only one rule exists and cannot be re-ordered.")
            return None
        
        selected_name = get_valid_selection("Select NAT rule you want to re-order: ", rule_list)
        rule_list.remove(selected_name)
        
        position = get_valid_selection("Move selected NAT rule: ", ["before", "after"])
        
        if position == "before" and rule_list:
            new_position_policy = get_valid_selection("Select NAT rule to position before: ", rule_list)
            if rule_list.index(new_position_policy) == 0:
                key = "insert=\"first\""
            else:
                key = f"insert=\"before\" key=\"[ name='{new_position_policy}' ]\""
        elif position == "after" and rule_list:
            new_position_policy = get_valid_selection("Select NAT rule to position after: ", rule_list)
            if rule_list.index(new_position_policy) == len(rule_list) - 1:
                key = f"insert=\"after\" key=\"[ name='{rule_list[-1]}' ]\""
            else:
                key = f"insert=\"after\" key=\"[ name='{new_position_policy}' ]\""
        else:
            key = "insert=\"first\""

        payload = f"""
        <configuration>
            <security>
                <nat>
                    <source>
                        <rule-set>
                            <name>{global_name}</name>
                            <rule {key} operation="merge">
                                <name>{selected_name}</name>
                            </rule>
                        </rule-set>
                    </source>
                </nat>
            </security>
        </configuration>""".strip()
        
        print(payload)
        return payload