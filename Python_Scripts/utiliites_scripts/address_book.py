from utiliites_scripts.commons import (get_valid_selection,validate_yes_no,get_valid_name,multiple_selection,
                                       get_valid_ipv4_name,get_valid_network_address)
def generate_addr_cfg(**kwargs):
    zone_address_name = kwargs.get("zone_address_name")
    new_prefix_name = kwargs.get("new_prefix_name")
    new_ipv4_address = kwargs.get("new_ipv4_address")
    selected_zone_name = kwargs.get("selected_zone_name")
    default_sec_zones = kwargs.get("default_sec_zones")
    existing_address_names = kwargs.get("existing_address_names")
    address_book_name = kwargs.get("address_book_name")
    global_address_names = kwargs.get("global_address_names")
    attached_zone = attribute = sub_attribute = ""
    if selected_zone_name in default_sec_zones:
        attached_zone = f"""
                        <attach>
                            <zone>
                                <name>{selected_zone_name}</name>
                            </zone>
                        </attach>"""
    if existing_address_names:
        last_address_name = existing_address_names[-1]
        sub_attribute = f""" insert="after" key="[ name='{last_address_name}' ]" operation="create" """
    elif zone_address_name == "global":
        sub_attribute = f""" insert="after"  key="[ name='{global_address_names[-1]}' ]" operation="create" """
    else:
        if address_book_name:
            attribute = f""" insert="after"  key="[ name='{address_book_name[-1]}' ]" operation="create" """
        else:
            attribute = f""" operation="create" """
    return f"""
    <configuration>
        <security>
            <address-book {attribute}>
                <name>{zone_address_name}</name>
                <address{sub_attribute}>
                    <name>{new_prefix_name}</name>
                    <ip-prefix>{new_ipv4_address}</ip-prefix>
                </address>
                {attached_zone}
            </address-book>
        </security>
    </configuration>""".strip()


def gen_address_set_config(addresses, zone, address_book_by_name):
    selected = get_valid_selection("Select address book name: ", address_book_by_name)
    address_names = default_address_set = []
    if addresses:
        for address in addresses:
            if address['name'] == selected:
                if address.get('address-set'):
                    default_address_set = [addrr_set['address-set']['name'] for addrr_set in addresses if 'address-set' in addrr_set]
                address_names = [item['name'] for item in address.get('address', [])]
                while True:
                    address_set_name = get_valid_name("Create new address-set name: ")
                    if address_set_name in default_address_set or address_set_name in address_names:
                        print("Address set name already exists. Please enter a different name.")
                        continue
                    break
        members = multiple_selection("Select and add address names", address_names)
        addr_set = '\n'.join([f'<address><name>{member}</name></address>' for member in members])
    return f"""<configuration>
    <security>
        <address-book>
            <name>{selected}</name>
            <address-set operation="create">
                <name>{address_set_name}</name>
                {addr_set}
            </address-set>
        </address-book>
    </security>
</configuration>""".strip()


def gen_addressbook_config(existing_address_book, raw_sec_zones, address_book_name):
    try:
        if not raw_sec_zones:
            raise ValueError("No raw_sec_zones available. Please create a sec zone first.")
        default_sec_zones = raw_sec_zones[:]  
        if "global" not in raw_sec_zones:
            raw_sec_zones = raw_sec_zones + ["global"]  
        selected_zone_name = get_valid_selection("Please select traffic zone: ", raw_sec_zones)
        matching_address = None
        if existing_address_book:
            if not isinstance(existing_address_book, list):
                existing_address_book = [existing_address_book]
            global_address_names = [addr['address']['name'] for addr in existing_address_book if addr['name'] == 'global']
            print(global_address_names)
            for address in existing_address_book:
                if address.get('attach', {}).get('zone', {}).get('name') == selected_zone_name or address.get('name') == selected_zone_name:
                    matching_address = address
                    break
            if matching_address:
                address_name = matching_address['name']
                choice = validate_yes_no(f"Address book name {address_name} exists in zone {selected_zone_name}. Add new address? (yes/no): ")
                if choice == True:
                    print(f"Creating/Adding addresses to {address_name} in zone {selected_zone_name}")
                    new_prefix_name, new_ipv4_address, zone_address_name, existing_address_names = create_address_name_prefix(existing_address_book, selected_zone_name,
                                                                                                    default_sec_zones=default_sec_zones)
                    return generate_addr_cfg(new_prefix_name=new_prefix_name, new_ipv4_address=new_ipv4_address, 
                                             zone_address_name=zone_address_name,address_book_name=address_book_name,
                                             selected_zone_name=selected_zone_name,default_sec_zones=default_sec_zones,
                                             existing_address_names=existing_address_names,global_address_names=global_address_names)
                else:
                    print(f"Not adding new addresses to {address_name}.")
                    return None
        new_prefix_name, new_ipv4_address, zone_address_name, existing_address_names = create_address_name_prefix(existing_address_book, selected_zone_name,
                                                                                        default_sec_zones=default_sec_zones)
        return generate_addr_cfg(new_prefix_name=new_prefix_name, new_ipv4_address=new_ipv4_address,
                                 default_sec_zones=default_sec_zones,address_book_name=address_book_name,
                                 zone_address_name=zone_address_name,selected_zone_name=selected_zone_name,
                                 existing_address_names=existing_address_names,global_address_names=None)
    except ValueError as ve:
        print(f"Error: {ve}")
        return None

def create_address_name_prefix(existing_address_book=None, selected_zone_name=None,default_sec_zones=None):
    existing_address_names = []
    existing_address_prefixes = []
    zone_addressbook_name =  ""
    if existing_address_book:
        for addr in existing_address_book:
            try:
                if addr['attach']['zone'].get('name') == selected_zone_name:
                    zone_addressbook_name = addr.get('name')
                    if isinstance(addr.get('address'), dict):
                        existing_address_names.append(addr['address'].get('name'))
                        existing_address_prefixes.append(addr['address'].get('ip-prefix'))
                    elif isinstance(addr.get('address'), list):
                        for address in addr['address']:
                            existing_address_names.append(address.get('name'))
                            existing_address_prefixes.append(address.get('ip-prefix'))
                    break
            except (KeyError, AttributeError):
                continue
    if zone_addressbook_name ==  "" and selected_zone_name in default_sec_zones:
        print(f"Address book for {selected_zone_name} zone does not exist.")
        zone_addressbook_name = get_valid_name("Create new security zone address_book name: ")
    elif zone_addressbook_name ==  "" and selected_zone_name not in default_sec_zones:
        zone_addressbook_name = selected_zone_name
    while True:
        new_prefix_name = get_valid_ipv4_name(f"Enter address name under {zone_addressbook_name} address_book: ")
        if new_prefix_name in existing_address_names:
            print(f"Prefix name {new_prefix_name} already exists, try again.")
            continue
        break
    while True:
        new_ipv4_address = get_valid_network_address(f"Specify network address under {new_prefix_name} address_book: ")
        if new_ipv4_address in existing_address_prefixes:
            print(f"Prefix {new_ipv4_address} already exists, try again.")
            continue
        break
    if existing_address_names:
        return new_prefix_name, new_ipv4_address, zone_addressbook_name, existing_address_names
    return new_prefix_name, new_ipv4_address, zone_addressbook_name, None


def gen_updated_config(addresses, address_book_by_name):
    updated_name_prefix = []
    selected_book = get_valid_selection("Please select address book: ", address_book_by_name)
    selected_addresses = None
    address_set = None
    zone = None
    for address_book in addresses:
        if address_book['name'] == selected_book:
            selected_addresses = address_book.get('address', [])
        if 'address-set' in address_book:
                if isinstance(address_book['address-set'], list):
                    address_set = [addr for addr_set in address_book['address-set'] for addr in addr_set['address']]
                else:
                    address_set = [addr for addr in address_book['address-set']['address']]
                break
    if not selected_addresses:
        print(f"No addresses found for the selected address book: {selected_book}")
        return None
    address_names = [addr['name'] for addr in selected_addresses]
    selected_address_name = get_valid_selection("Select address name", address_names)
    subnet_to_update = next((subnet for subnet in selected_addresses if subnet['name'] == selected_address_name), None)
    if not subnet_to_update:
        print(f"No subnet found with the name: {selected_address_name}")
        return
    original_values = {
        "name": subnet_to_update['name'],
        "ip-prefix": subnet_to_update.get('ip-prefix')
    }
    while True:
        policy_attributes = {
            "name": subnet_to_update['name'],
            "ip-prefix": subnet_to_update.get('ip-prefix')
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        key_to_update = selected_attribute.split(":")[0].strip()
        new_value = None
        if key_to_update == "name":
            print(f"Please double check subnet {original_values['name']} is not in use!")
            if address_set:
                if any(addr['name'] == original_values['name'] for addr in address_set):
                    print(f"{original_values['name']} is in use in address-set. First delete from address-set")
                    return
                new_value = get_valid_name(f"Enter new value for {key_to_update}: ").strip()
        elif key_to_update == "ip-prefix":
            new_value = get_valid_network_address(f"Enter new value for {key_to_update}: ").strip()
        else:
            print("Invalid Selection, Please try again")
            continue
        if original_values[key_to_update] != new_value and {key_to_update: original_values[key_to_update]} not in updated_name_prefix:
            updated_name_prefix.append({key_to_update: original_values[key_to_update]})
        subnet_to_update[key_to_update] = new_value
        if not validate_yes_no("Do you want to update another parameter? (yes/no): "):
            break
    sub_attribute = prefix_name = ip_prefix = old_prefix_name = old_ip_prefix = ""
    if subnet_to_update['name'] != original_values['name']:
        old_prefix_name = f"""<address operation="delete"><name>{original_values['name']}</name></address>"""
        prefix_name = f"""<name>{subnet_to_update['name']}</name>"""
    else:
        prefix_name = f"""<name>{subnet_to_update['name']}</name>"""
    if subnet_to_update['ip-prefix'] != original_values['ip-prefix']:
        if old_prefix_name == "":
            old_ip_prefix = f"""<ip-prefix operation="delete"/>"""
            ip_prefix = f"""<ip-prefix operation="create">{subnet_to_update['ip-prefix']}</ip-prefix>"""
        else:
            ip_prefix = f"""<ip-prefix>{subnet_to_update['ip-prefix']}</ip-prefix>"""
    else:
        ip_prefix = f"""<ip-prefix>{subnet_to_update['ip-prefix']}</ip-prefix>"""
    if old_prefix_name and len(address_names) >= 1:
        if subnet_to_update['name'] != address_names[-1]:
            sub_attribute = f""" insert="after" key="[name='{address_names[-1]}']" operation="create" """
        else:
            sub_attribute = f""" insert="after" key="[name='{address_names[0]}']" operation="create" """
    new_config = f"""
    <configuration>
        <security>
            <address-book>
                <name>{selected_book}</name>
                <address{sub_attribute}>
                    {prefix_name}
                    {old_ip_prefix}
                    {ip_prefix}
                </address>
                {old_prefix_name}
            </address-book>
        </security>
    </configuration>""".strip()
    return new_config

def gen_delete_config(addresses, address_book_by_name):
    selected_addresses = address_set = zone = None
    option = ["delete_address_book","delete_address_name","delete_address_set"]
    operation  = get_valid_selection("Please select delete operation", option)

    if operation == "delete_address_name":
        selected_book = get_valid_selection("Please select address book?: ", address_book_by_name)
        selected_addresses, address_set = extract_addresses(addresses, selected_book)
        address_names = [addr['name'] for addr in selected_addresses]
        selected_address_name = get_valid_selection("Select address name", address_names)
        result  = check_address_set(addresses, selected_book, selected_address_name)
        if result == True:
            print(f"{selected_address_name } is used in address-set, Please first delete from address-set ")
            return None
        del_config  = f"""<address-book>
                    <name>{selected_book}</name>
                    <address operation="delete">
                        <name>{selected_address_name}</name>
                    </address>
                </address-book>"""
    elif operation == "delete_address_set":
        selected_book = get_valid_selection("Please select address book?: ", address_book_by_name)
        selected_addresses, address_set= extract_addresses(addresses, selected_book)
        if not address_set:
            print(f"No address sets found in the address book: {selected_book}")
            return None
        print(f"The following address_set exist under the selected {selected_book} address book:")
        select_address_set = get_valid_selection("Select address_set for deletion: ", address_set)
        address_set_members = extract_address_set_member(addresses, selected_book, select_address_set)
        if len(address_set_members) >= 1:
            print(f"The address_set {select_address_set} contain address listed below: ")
            for i, address in enumerate(address_set_members, 1):
                print(f"{i}. {address}")
        choice = validate_yes_no(f"The address_set contains addresses that might be in use. Do you still want to proceed? (yes/no) ")
        if choice == True:
            del_config = f"""<address-book>
                        <name>{selected_book}</name>
                            <address-set operation="delete">
                                <name>{select_address_set}</name>
                            </address-set>
                    </address-book>"""
        else:
            print("Operation cancelled by the user.")
            return None
    elif operation == "delete_address_book":
        selected_book = get_valid_selection("Please select address book to delete?: ", address_book_by_name)
        selected_addresses, address_set = extract_addresses(addresses, selected_book)
        if selected_addresses:
            print(f"The following addresses exist under the selected {selected_book} address book:")
            for i, address in enumerate(selected_addresses, 1):
                print(f"{i}. {address}")
        if address_set:
            print(f"The following address_set exist under the selected {selected_book} address book:")
            for i, address in enumerate(selected_addresses, 1):
                print(f"{i}. {address}")
        choice = validate_yes_no(f"The {selected_book} contains addresses. Do you still want to proceed? (yes/no): ")
        if choice == True:
                del_config = f"""
                <address-book operation="delete">
                    <name>{selected_book}</name>
                </address-book>"""
        else:
            print("Operation cancelled by the user.")
            return None
    payload = f"""<configuration>
            <security>
                {del_config}
            </security>
    </configuration>""".strip()
    return payload



def extract_addresses(addresses, selected_book):
    if addresses is None:
        return [], []
    selected_addresses = []
    address_set = []
    for address_book in addresses:
        if address_book['name'] == selected_book:
            selected_addresses = address_book.get('address', [])
            if selected_book == "global":
                pass
            if 'address-set' in address_book:
                if isinstance(address_book['address-set'], list):
                    address_set = [addr_set['name'] for addr_set in address_book['address-set']]
                else:
                    address_book['address-set'] = [address_book['address-set']]
                    address_set = [addr_set['name'] for addr_set in address_book['address-set']]
            break
    return selected_addresses, address_set

def extract_address_set_member(addresses, selected_book, select_address_set):
    address_set_members = []
    if not addresses:
        return address_set_members
    for address_book in addresses:
        if address_book['name'] == selected_book and 'address-set' in address_book:
            address_sets = address_book['address-set']
            if not isinstance(address_sets, list):
                address_sets = [address_sets]
            for addr_set in address_sets:
                if addr_set['name'] == select_address_set:
                    addresses = addr_set['address']
                    if not isinstance(addresses, list):
                        addresses = [addresses]
                    address_set_members = [addr['name'] for addr in addresses]
                    return address_set_members
    return address_set_members


def check_address_set(addresses, selected_book, selected_address):
    for address_book in addresses:
        if address_book['name'] == selected_book:
            if 'address-set' in address_book:
                address_sets = address_book['address-set']
                if not isinstance(address_sets, list):
                    address_sets = [address_sets]
                for addr_set in address_sets:
                    addresses_in_set = addr_set['address']
                    if not isinstance(addresses_in_set, list):
                        addresses_in_set = [addresses_in_set]
                    for addr in addresses_in_set:
                        if addr['name'] == selected_address:
                            return True
    return False

