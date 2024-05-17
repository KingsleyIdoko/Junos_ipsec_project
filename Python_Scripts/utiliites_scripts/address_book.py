from utiliites_scripts.commons import (get_valid_selection, validate_yes_no, 
                                       get_valid_ipv4_name, get_valid_network_address)

def generate_addr_cfg(prefix_name=None, ipv4_address=None, attached_zone_name=None,
                      address_name=None, address_book_name=None, existing_zones=None,
                      existing_names=None):
    attached_zone = attribute = sub_attribute = ""

    if address_name and attached_zone_name and attached_zone_name in existing_zones:
        attached_zone = f"""
                        <attach>
                            <zone>
                                <name>{attached_zone_name}</name>
                            </zone>
                        </attach>"""
    elif attached_zone_name in address_book_name:
        address_name = attached_zone_name
        last_existing_name = existing_names[-1] if prefix_name != existing_names[-1] else existing_names[-2]
        sub_attribute = f""" insert="after" key="[ name='{last_existing_name}' ]" operation="create" """
    else:
        address_name = attached_zone_name
        if address_book_name and address_name not in address_book_name:
            last_attached_zone = address_book_name[-1] if address_name != address_book_name[-1] else address_book_name[-2]
            attribute = f""" insert="after" key="[ name='{last_attached_zone}' ]" operation="create" """

    return f"""
    <configuration>
        <security>
            <address-book {attribute}>
                <name>{address_name}</name>
                <address{sub_attribute}>
                    <name>{prefix_name}</name>
                    <ip-prefix>{ipv4_address}</ip-prefix>
                </address>
                {attached_zone}
            </address-book>
        </security>
    </configuration>""".strip()



def gen_addressbook_config(addresses, zones, address_book_name):
    existing_zones = zones[:]  
    if "global" not in zones:
        zones = zones + ["global"]  
    attached_zone_name = get_valid_selection("Please select traffic zone: ", zones)
    matching_address = None
    for address in addresses:
        if address.get('attach', {}).get('zone', {}).get('name') == attached_zone_name or address.get('name') == attached_zone_name:
            matching_address = address
            break
    if matching_address:
        address_name = matching_address['name']
        choice = validate_yes_no(f"Address book name {address_name} exists in zone {attached_zone_name}. Add new address? (yes/no): ")
        if choice:
            print(f"Creating/Adding addresses to {address_name} in zone {attached_zone_name}")
            existing_names = [addr['name'] for addr in matching_address.get('address', [])]
            existing_prefixes = [addr['ip-prefix'] for addr in matching_address.get('address', [])]
            prefix_name, ipv4_address = create_address_name_prefix(existing_names=existing_names, existing_prefixes=existing_prefixes)
            return generate_addr_cfg(prefix_name=prefix_name, ipv4_address=ipv4_address, 
                                     attached_zone_name=attached_zone_name, address_name=address_name, 
                                     address_book_name=address_book_name, existing_zones= existing_zones,
                                     existing_names=existing_names)
        else:
            print(f"Not adding new addresses to {address_name}.")
            return None
    else:
        prefix_name, ipv4_address = create_address_name_prefix()
        print(existing_zones)  # Print the original zones without "global"
        return generate_addr_cfg(prefix_name=prefix_name, ipv4_address=ipv4_address, attached_zone_name=attached_zone_name, address_book_name=address_book_name)

        
def create_address_name_prefix(existing_names=None, existing_prefixes=None):
    if not existing_names:
        existing_prefixes = existing_names = []
    while True:
        prefix_name = get_valid_ipv4_name("Enter address name: ")
        if prefix_name in existing_names:
            print(f"Prefix name {prefix_name} already exists, try again.")
            continue
        break
    while True:
        ipv4_address = get_valid_network_address("Enter network address: ")
        if ipv4_address in existing_prefixes:
            print(f"Prefix {ipv4_address} already exists, try again.")
            continue
        break
    return prefix_name, ipv4_address



def create_zone():
    print("Creating new zone...")
    # Implement zone creation logic here

def create_address_book():
    print("Creating new address book...")
    # Implement address book creation logic here
