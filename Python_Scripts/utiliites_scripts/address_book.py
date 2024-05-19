from utiliites_scripts.commons import (get_valid_selection, validate_yes_no,get_valid_name,get_valid_ipv4_name, 
                                       get_valid_network_address)

def generate_addr_cfg(**kwargs):
    zone_address_name = kwargs.get("zone_address_name")
    new_prefix_name = kwargs.get("new_prefix_name")
    new_ipv4_address = kwargs.get("new_ipv4_address")
    selected_zone_name = kwargs.get("selected_zone_name")
    default_sec_zones = kwargs.get("default_sec_zones")
    existing_address_names = kwargs.get("existing_address_names")
    address_book_name = kwargs.get("address_book_name")
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
    else:
        if address_book_name:
            attribute = f""" insert="after"  key="[ name='{[address_book_name[-1]]}' ]" operation="create" """
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
            for address in existing_address_book:
                if address.get('attach', {}).get('zone', {}).get('name') == selected_zone_name or address.get('name') == selected_zone_name:
                    matching_address = address
                    break
            if matching_address:
                address_name = matching_address['name']
                choice = validate_yes_no(f"Address book name {address_name} exists in zone {selected_zone_name}. Add new address? (yes/no): ")
                if choice:
                    print(f"Creating/Adding addresses to {address_name} in zone {selected_zone_name}")
                    new_prefix_name, new_ipv4_address, zone_address_name, existing_address_names = create_address_name_prefix(existing_address_book, selected_zone_name,
                                                                                                    default_sec_zones=default_sec_zones)
                    return generate_addr_cfg(new_prefix_name=new_prefix_name, new_ipv4_address=new_ipv4_address, zone_address_name=zone_address_name,address_book_name=address_book_name,
                                             selected_zone_name=selected_zone_name,default_sec_zones=default_sec_zones,existing_address_names=existing_address_names)
                else:
                    print(f"Not adding new addresses to {address_name}.")
                    return None
        new_prefix_name, new_ipv4_address, zone_address_name, existing_address_names = create_address_name_prefix(existing_address_book, selected_zone_name,
                                                                                        default_sec_zones=default_sec_zones)
        return generate_addr_cfg(new_prefix_name=new_prefix_name, new_ipv4_address=new_ipv4_address,default_sec_zones=default_sec_zones,address_book_name=address_book_name,
                                 zone_address_name=zone_address_name,selected_zone_name=selected_zone_name,existing_address_names=existing_address_names)
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


def create_zone():
    print("Creating new zone...")
    # Implement zone creation logic here

def create_address_book():
    print("Creating new address book...")
    # Implement address book creation logic here
