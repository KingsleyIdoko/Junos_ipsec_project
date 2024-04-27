from utiliites_scripts.pool_data import is_valid_name 
import re

def is_valid_string(input_string):
    pattern = r'^[a-zA-Z0-9_ ]+$'
    if re.match(pattern, input_string):
        words = input_string.split()
        return len(words) <= 5
    else:
        return False

def select_zone(zones, list_interfaces):
    print("Select a zone:\n")
    for i, zone in enumerate(zones, start=1):
        print(f"{i}. {zone}")
    print(f"{len(zones) + 1}. Create new zone")
    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if 1 <= choice <= len(zones):
                print(f"You selected: {zones[choice - 1]}")
                return zones[choice - 1], None
            elif choice == len(zones) + 1:
                print("Option to create a new zone selected.")
                while True:
                    zone_name = input("Enter zone name: ")
                    if is_valid_name(zone_name):
                        break
                    else:
                        print("Name is not valid. Please try again.")
                while True:
                    zone_description = input("Enter zone description: ")
                    if is_valid_string(zone_description):
                        break
                    else:
                        print("Description is not valid. Please enter a valid description (no more than 5 words).")
                services = get_system_services()
                protocols = get_system_protocols()  
                interface = get_interfaze(list_interfaces)  
                response = create_new_zone(zone_name, zone_description, services, protocols, interface)
                return response
            else:
                print(f"Please select a number between 1 and {len(zones) + 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def select_zone_info(zone, list_interfaces):
    print(zone)
    print("\nSelected Zone Configuration Details:")
    print(f"1. Name: {zone['name']}")
    print(f"2. Description: {zone['description']}")
    print("3. Host-Inbound-Traffic:")

    system_services = zone['host-inbound-traffic']['system-services']
    services_names = ', '.join([service['name'] for service in system_services])
    print(f"   System-Services: {services_names}")

    protocols = zone['host-inbound-traffic']['protocols']
    if isinstance(protocols, list):
        protocols_names = ', '.join([protocol['name'] for protocol in protocols])
    else:
        protocols_names = protocols['name']
    print(f"   Protocols: {protocols_names}\n")

    print("What would you like to update?")
    print("1. Name (Cannot be updated, create a new zone)")
    print("2. Description")
    print("3. Host-Inbound-Traffic")

    # Initialize services and protocols with default or existing values
    services = [service['name'] for service in system_services]  # Adjust as needed
    protocols = [protocols_names] if isinstance(protocols_names, str) else protocols_names
    zone_description = zone['description']

    while True:
        choice = input("Enter your choice (1-3): ")
        if choice == '1':
            print("The zone name cannot be updated. Please choose another option.")
            continue  
        elif choice == '2':
            zone_description = input("Specify new description: ")
            if is_valid_string(zone_description):
                break  
            else:
                print("Description is not valid. Please enter a valid description (no more than 5 words).")
                continue
        elif choice == '3':
            print("1. System-Services")
            print("2. Protocols")
            choice2 = int(input("Enter your choice (1-2): "))
            if choice2 == 1:
                print("Select System-Services")
                services = get_system_services()  
            elif choice2 == 2:
                print("Select Protocols")
                protocols = get_system_protocols()  
            break  
        else:
            print("Please select a valid option (1-3).")
            continue

    update_interface = input("Do you want to update the zone interface? (yes/no): ").lower()
    if update_interface == 'yes' and list_interfaces:
        interface = get_interfaze(list_interfaces)
    else:
        if not list_interfaces:
            print("There are no free interfaces. Using the existing interface.")
        interface = zone['interfaces']['name']

    zone_name = zone['name']
    response = create_new_zone(zone_name, zone_description, services, protocols, interface)
    return response

def get_interface_name(zone_info):
    return zone_info.get('interfaces', {}).get('name', 'No interface name found')

def get_traffic_details(zone_info):
    system_services = None
    protocols = None
    if 'host-inbound-traffic' in zone_info:
        if 'system-services' in zone_info['host-inbound-traffic'] and 'name' in zone_info['host-inbound-traffic']['system-services']:
            system_services = zone_info['host-inbound-traffic']['system-services']['name']
        if 'protocols' in zone_info['host-inbound-traffic'] and 'name' in zone_info['host-inbound-traffic']['protocols']:
            protocols = zone_info['host-inbound-traffic']['protocols']['name']
    return system_services, protocols

def update_zone(zones, list_interfaces):
    if not isinstance(zones, list):
        zones = [zones]
    print("Select a zone to update:\n")
    for i, zone in enumerate(zones, start=1):
        print(f"{i}. {zone['name']}")
    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if 1 <= choice <= len(zones):
                selected_zone = zones[choice - 1]
                print(f"You selected: {selected_zone['name'].upper()}")
                print(f"Retrieving {selected_zone['name'].upper()} config details")
                response = select_zone_info(selected_zone, list_interfaces)
                return response
            else:
                print(f"Please select a number between 1 and {len(zones)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def create_new_zone(zone_name, zone_description, services, protocols, select_interfaces):
    print("Creating a new zone...")

    if isinstance(services, list):
        services_xml = ''.join([f"<system-services><name>{service}</name></system-services>" for service in services])
    else:
        services_xml = f"<system-services><name>{services}</name></system-services>"
    if isinstance(protocols, list):
        protocols_xml = ''.join([f"<protocols><name>{protocol}</name></protocols>" for protocol in protocols])
    else:
        protocols_xml = f"<protocols><name>{protocols}</name></protocols>"
    if isinstance(select_interfaces, list):
        interfaces_xml = ''.join([f"<interfaces><name>{interface}</name></interfaces>" for interface in select_interfaces])
    else:
        interfaces_xml = f"<interfaces><name>{select_interfaces}</name></interfaces>"
    payload = f"""
        <configuration>
            <security>
                <zones>
                    <security-zone>
                        <name>{zone_name}</name>
                        <description>{zone_description}</description>
                        <host-inbound-traffic>
                            {services_xml}
                            {protocols_xml}
                        </host-inbound-traffic>
                        {interfaces_xml}
                    </security-zone>
                </zones>                
            </security>                 
    </configuration>"""
    return payload


def get_system_services():
    services = [
        "all", "any-service", "appqoe", "bootp", "dhcp", "dhcpv6", "dns", "finger", "ftp", "high-availability",
        "http", "https", "ident-reset", "ike", "lsping", "netconf", "ntp", "ping", "r2cp", "reverse-ssh",
        "reverse-telnet", "rlogin", "rpm", "rsh", "snmp", "snmp-trap", "ssh", "tcp-encap", "telnet", "tftp",
        "traceroute", "webapi-clear-text", "webapi-ssl", "xnm-clear-text"
    ]
    print("Select system services (e.g., 1, 4, 7):\n")
    for i, service in enumerate(services, start=1):
        print(f"{i}. {service}")

    selected_services = []
    choices = input("\nEnter your choices: ").split(',')
    for choice in choices:
        try:
            choice_int = int(choice.strip())  # Remove any extra whitespace
            if 1 <= choice_int <= len(services):
                selected_services.append(services[choice_int - 1])
            else:
                print(f"Choice {choice} is out of range. Ignoring.")
        except ValueError:
            print(f"Invalid choice '{choice}'. Ignoring.")

    print(f"You selected: {', '.join(selected_services)}")
    return selected_services

def get_system_protocols():
    protocols = [
        "all", "bfd", "bgp", "dvmrp", "igmp", "ldp", "msdp", "nhrp", "ospf", "ospf3",
        "pgm", "pim", "rip", "ripng", "router-discovery", "rsvp", "sap", "vrrp"
    ]
    print("Select system protocols (e.g., 2, 5, 8):\n")
    for i, protocol in enumerate(protocols, start=1):
        print(f"{i}. {protocol}")

    selected_protocols = []
    choices = input("\nEnter your choices: ").split(',')
    for choice in choices:
        try:
            choice_int = int(choice.strip())  # Remove any extra whitespace
            if 1 <= choice_int <= len(protocols):
                selected_protocols.append(protocols[choice_int - 1])
            else:
                print(f"Choice {choice} is out of range. Ignoring.")
        except ValueError:
            print(f"Invalid choice '{choice}'. Ignoring.")

    print(f"You selected: {', '.join(selected_protocols)}")
    return selected_protocols


def get_interfaze(interfaces):
    try:
        print("Select a system Interfaces:\n")
        for i, interface in enumerate(interfaces, start=1):
            print(f"{i}. {interface}")
        while True:
            try:
                choice = int(input("\nEnter your choice: "))
                if 1 <= choice <= len(interfaces):
                    selected_interfaces = interfaces[choice - 1]
                    print(f"You selected: {selected_interfaces}")
                    return selected_interfaces
                else:
                    print(f"Please select a number between 1 and {len(interfaces)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    except:
        print("There are no free interfaces....\n")
        # create_new_intefaces()
        # get_interfaze(interfaces)


def zone_interface_names(data):
    # Ensure data is a list for uniform processing
    if isinstance(data, dict):
        data = [data]
    
    # Extract interface names where available
    interface_names = [zone['interfaces']['name'] for zone in data if 'interfaces' in zone]
    
    return interface_names


def find_available_interfaces(all_interfaces, used_interfaces):
    used_base_names = {iface.split('.')[0] for iface in used_interfaces}
    available_interfaces = [iface for iface in all_interfaces if iface not in used_base_names]
    return available_interfaces


def delete_sec_zone(name):
    payload = f"""
    <configuration>
            <security>
                <zones>
                    <security-zone operation="delete">
                        <name>{name}</name>
                    </security-zone>
                </zones>
            </security>
    </configuration>"""
    return payload

def list_zone(zones):
    try:
        print("Select Zones for deletion:\n")
        for i, interface in enumerate(zones, start=1):
            print(f"{i}. {interface}")
        while True:
            try:
                choice = int(input("\nEnter your choice: "))
                if 1 <= choice <= len(zones):
                    selected_zones = zones[choice - 1]
                    print(f"You selected: {selected_zones}")
                    return selected_zones
                else:
                    print(f"Please select a number between 1 and {len(zones)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")
    except:
        print("There are no free interfaces....\n")
        # create_new_intefaces()
        # get_interfaze(interfaces)

def extract_zone_names(data):
    # Ensure data is a list for uniform processing
    if isinstance(data, dict):
        data = [data]
    
    # Using list comprehension to extract zone names
    zone_names = [entry['attach']['zone']['name'] for entry in data]
    
    return zone_names
