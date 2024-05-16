from utiliites_scripts.commons import (get_valid_selection, validate_yes_no, 
                                       get_valid_name, get_valid_network_address)

def generate_addr_cfg(prefix_name=None, ipv4_address=None, 
                      zone_address_book=None, address_name=None, list_attached_zones=None):
    print(list_attached_zones)
    attached_zone = attribute = ""
    if address_name:
        attached_zone = f"""
                        <attach>
                            <zone>
                                <name>{zone_address_book}</name>
                            </zone>
                        </attach>"""
    else:
        address_name = zone_address_book
        if list_attached_zones:
            last_attached_zone = list_attached_zones[-1]  
            attribute = f"""insert="after" key="[name='{last_attached_zone}']" operation="create" """
    
    return f"""
    <configuration>
        <security>
            <address-book {attribute}>
                <name>{address_name}</name>
                <address>
                    <name>{prefix_name}</name>
                    <ip-prefix>{ipv4_address}</ip-prefix>
                </address>
                {attached_zone}
            </address-book>
        </security>
    </configuration>""".strip()

def gen_addressbook_config(addresses, zones):
    list_attached_zones =  zones
    if "global" not in zones:
        zones.append("global")
    zone_address_book = get_valid_selection("Please select traffic zone: ", zones)
    for address in addresses:
        if address['attach']['zone']['name'] == zone_address_book:
            address_name = address['name']
            choice = validate_yes_no(f"Address book name {address_name} exists in zone {zone_address_book}. Add new address? (yes/no): ")
            if choice:
                print(f"Creating/Adding addresses to {address_name} in zone {zone_address_book}")
                existing_names = [addr['name'] for addr in address.get('address', [])]
                existing_prefixes = [addr['ip-prefix'] for addr in address.get('address', [])]
                prefix_name, ipv4_address = create_address_name_prefix(existing_names=existing_names,existing_prefixes=existing_prefixes)
                return generate_addr_cfg(prefix_name=prefix_name, ipv4_address=ipv4_address, 
                                         zone_address_book=zone_address_book, address_name=address_name,
                                         list_attached_zones=list_attached_zones)
            else:
                print(f"Not adding new addresses to {address_name}.") 
                return None
        else:
            prefix_name, ipv4_address = create_address_name_prefix()
            return generate_addr_cfg(prefix_name=prefix_name, ipv4_address=ipv4_address, 
                                     zone_address_book=zone_address_book, list_attached_zones=list_attached_zones)

def create_address_name_prefix(existing_names=None, existing_prefixes=None):
    if not existing_names:
        existing_prefixes = existing_names = []
    while True:
        prefix_name = get_valid_name("Enter address name: ")
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
