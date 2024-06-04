
import re, ipaddress
from utiliites_scripts.commons import (get_valid_name, get_valid_network_address,validate_yes_no,
                                       get_valid_selection, get_valid_selection_dict)

def extract_pool_names(rule_set):
    pool_names = []
    rules = rule_set.get('rule')
    if isinstance(rules, dict):
        rules = [rules]
    for rule in rules:
        if 'pool' in rule.get('then', {}).get('source-nat', {}):
            pool_name = rule['then']['source-nat']['pool'].get('pool-name')
            if pool_name:
                pool_names.append(pool_name)
    return pool_names


def select_zone(zones):
    print("Select zones..........\n")
    for i, zone in enumerate(zones, start=1):
        print(f"{i}. {zone}")
    
    while True:
        try:
            message = input("Please select zone: ")
            message_int = int(message)  
            if 1 <= message_int <= len(zones): 
                return zones[message_int - 1]  
            else:
                print(f"Please select a number between 1 and {len(zones)}.")
        except ValueError:  
            print("Invalid input. Please enter a number.")

def gen_nat_pool_config(old_nat_data, used_pool_names):
    attribute  = ""
    if isinstance(old_nat_data, dict):
        old_nat_data = [old_nat_data]
    old_pool_name = [pool_names['name'] for pool_names in old_nat_data]
    print("Creating NAT Pool.......\n")
    while True:
        pool_name = get_valid_name("Enter name of new pool: ")
        address_name = get_valid_network_address("Enter NAT pool address: ")
        print("Checking for duplicate NAT pool name and NAT prefixes......\n")
        if check_nat_pool_duplicates(old_nat_data, pool_name, address_name):
            break
        print("Duplicate NAT pool name or prefix detected. Try again.")
    if len(old_pool_name) >= 1 and pool_name != old_pool_name[-1]:
        attribute  = f"""  insert="after"  key="[ name='{old_pool_name[-1]}' ]" operation="create" """
    return f""" <configuration>
                <security>
                    <nat>
                        <source>
                            <pool {attribute} >
                                <name>{pool_name}</name>
                                <address>
                                    <name>{address_name}</name>
                                </address>
                            </pool>
                        </source>
                    </nat>
                </security>
        </configuration>""".strip()


def check_nat_pool_duplicates(old_nat_data, nat_pool_name, address_name):
    for pool in old_nat_data:
        if nat_pool_name == pool['name']:
            print("Name already exists in the pool")
            return False
        if 'address' in pool and address_name == pool['address'].get('name'):
            print("Prefix already exists in the pool")
            return False
    return True

def gen_updated_pool_config(old_nat_data, used_pool_names):
    sub_pool = del_sub =  attribute = address_change = ""
    if not isinstance(old_nat_data, list):
        old_nat_data = [old_nat_data]
    existing_pool_names = {pool['name']: pool['address']['name'] for pool in old_nat_data}
    pool_names = list(existing_pool_names.keys())
    pool_to_update = get_valid_selection("Enter pool name to update", pool_names)
    update_options = {
        'name': pool_to_update,
        'address': existing_pool_names[pool_to_update]
    }
    old_version =  update_options.copy()
    while True:
        selected = get_valid_selection_dict("Enter a selection: ", update_options)
        if selected == 'name':
            if update_options['name'] in used_pool_names:
                if validate_yes_no(f"Pool name {update_options['name']} is in use. Continue editing (yes/no)?: "):
                    continue
                print("Aborting configuration")
                return None
            else:
                update_options['name'] = get_valid_name(f"Enter new name for the pool '{pool_to_update}': ")
                if validate_yes_no(f"Pool name {update_options['name']} is in use. Continue editing (yes/no)?: "):
                    continue
                break
        elif selected == 'address':
            update_options['address'] = get_valid_network_address(f"Enter new NAT pool address {update_options['address']}: ")
            address_change = f"""  insert="first" operation="create" """
        break
    if len(pool_names) >= 1 and update_options['name'] != pool_to_update:
        last_pool = pool_names[-1]
        if update_options['name'] != last_pool:
            attribute = f'insert="after" key="[ name=\'{last_pool}\' ]" operation="create"'
        elif len(pool_names) > 1:
            second_last_pool = pool_names[-2]
            if update_options['name'] != second_last_pool:
                attribute = f'insert="after" key="[ name=\'{second_last_pool}\' ]" operation="create"'
        else:
            attribute = 'operation="create"'
    if pool_to_update != update_options['name']:
        sub_pool = f'<pool operation="delete"><name>{pool_to_update}</name></pool>'
    else:
        del_sub  = f"""<address operation="delete"><name>{old_version['address']}</name></address>"""
    payload =  f"""
    <configuration>
        <security>
            <nat>
                <source>
                    <pool {attribute}>
                        <name>{update_options['name']}</name>
                        <address {address_change}>
                            <name>{update_options['address']}</name>
                        </address>
                        {del_sub}
                    </pool>
                    {sub_pool}
                </source>
            </nat>
        </security>
    </configuration>""".strip()
    return payload

def gen_delete_pool_config(old_nat_data, used_pool_names):
    if not isinstance(old_nat_data, list):
        old_nat_data = [old_nat_data]
    existing_pool_names = {pool['name']: pool['address']['name'] for pool in old_nat_data}
    pool_names = list(existing_pool_names.keys())
    pool_to_update = get_valid_selection("Enter pool name to dlete", pool_names)
    if pool_to_update in used_pool_names:
        print(f"NAT pool {pool_to_update} is in use")
        return None
    payload = f"""
    <configuration>
            <security>
                <nat>
                    <source>
                        <pool operation="delete">
                            <name>{pool_to_update}</name>
                        </pool>
                    </source>
                </nat>
            </security>
    </configuration>"""
    return payload


