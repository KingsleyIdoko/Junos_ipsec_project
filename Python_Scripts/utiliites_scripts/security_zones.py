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
                zone_name = input("Enter zone name: ")
                if not is_valid_name(zone_name):
                    print("Name is not valid. Please try again.")
                    continue  
                zone_description = input("Enter zone description: ")
                if not is_valid_string(zone_description):
                    print("Name is not valid. Please try again.")
                    continue  
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
    print("\nSelected Zone Configuration Details:")
    print(f"1. Name: {zone['name']}")
    print(f"2. Description: {zone['description']}")
    print("3. Host-Inbound-Traffic:")
    print(f"   System-Services: {zone['host-inbound-traffic']['system-services']['name']}")
    print(f"   Protocols: {zone['host-inbound-traffic']['protocols']['name']}\n")
    print("What would you like to update?")
    print("1. Name (Cannot be updated, create a new zone)")
    print("2. Description")
    print("3. Host-Inbound-Traffic")
    services, protocols, zone_description = None, None, zone['description'] 
    services = protocols = None
    while True:
        try:
            choice = int(input("Enter your choice (1-3): "))
            if choice == 1:
                print("Name cannot be updated. Please create a new zone.")
                break  
            elif choice == 2:
                while True:
                    zone_description = input("Specify new description: ")
                    if is_valid_string(zone_description):
                        break
                    else:
                        print("Description is not valid. Please enter a valid description (no more than 5 words).")
                break
            elif choice == 3:
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
        except ValueError:
            print("Invalid input. Please enter a number.")
    print("Do you want to update the zone interface? (yes/no): ")
    update_interface = input().lower()
    interface = None
    if update_interface == 'yes':
        interface = get_interfaze(list_interfaces)
    else:
        interface = get_interface_name(zone)
    zone_name = zone['name']
    print(services, protocols)
    if services == None:
        services, protocols = get_traffic_details(zone)
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

def create_new_zone(zone_name, zone_description, services, protocols, select_interface):
    print("Creating a new zone...")
    payload = f"""
        <configuration>
            <security>
                <zones>
                    <security-zone>
                        <name>{zone_name}</name>
                        <description>{zone_description}</description>
                        <host-inbound-traffic>
                            <system-services>
                                <name>{services}</name>
                                <except/>
                            </system-services>
                            <protocols>     
                                <name>{protocols}</name>
                                <except/>
                            </protocols>
                        </host-inbound-traffic>
                        <interfaces>
                            <name>{select_interface}</name>
                        </interfaces>
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
    print("Select a system service:\n")
    for i, service in enumerate(services, start=1):
        print(f"{i}. {service}")
    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if 1 <= choice <= len(services):
                selected_service = services[choice - 1]
                print(f"You selected: {selected_service}")
                return selected_service
            else:
                print(f"Please select a number between 1 and {len(services)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_system_protocols():
    protocols = [
        "all", "bfd", "bgp", "dvmrp", "igmp", "ldp", "msdp", "nhrp", "ospf", "ospf3",
        "pgm", "pim", "rip", "ripng", "router-discovery", "rsvp", "sap", "vrrp"
    ]
    print("Select a system protocol:\n")
    for i, protocol in enumerate(protocols, start=1):
        print(f"{i}. {protocol}")
    
    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if 1 <= choice <= len(protocols):
                selected_protocol = protocols[choice - 1]
                print(f"You selected: {selected_protocol}")
                return selected_protocol
            else:
                print(f"Please select a number between 1 and {len(protocols)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_interfaze(interfaces):
    print("Select a system protocol:\n")
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

