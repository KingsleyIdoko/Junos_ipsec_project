import re
import ipaddress
def is_valid_mac_address(mac):
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))

def is_valid_string(input_string):
    pattern = r'^[a-zA-Z0-9_ ]+$'
    if re.match(pattern, input_string):
        words = input_string.split()
        return len(words) <= 5
    else:
        return False
def is_valid_ipv4_address(address):
    try:
        ipaddress.ip_network(address, strict=False)
        return True
    except ValueError:
        return False

def get_interfaces(device_interfaces):
    interface_names = []
    for interface in device_interfaces['interface']:
        if interface['name'].startswith('fab') or interface['name'].startswith('fxp'):
            continue
        gigether_options = interface.get('gigether-options')
        if gigether_options:
            parent = gigether_options.get('redundant-parent', {}).get('parent')
            if parent:
                interface_names.append(parent)
                continue  
        interface_names.append(interface['name'])
    return list(set(interface_names))

def is_valid_string(input_string):
    pattern = r'^[a-zA-Z0-9_ ]+$'
    if re.match(pattern, input_string):
        words = input_string.split()
        return len(words) <= 10
    else:
        return False
        
def select_interface(nested_interfaces):
    if not nested_interfaces or not isinstance(nested_interfaces[0], list):
        print("Invalid interface data provided.")
        return
    interfaces = nested_interfaces[0]  
    while True:  
        print("Please choose an interface for configuration by entering its number:\n")
        for index, interface in enumerate(interfaces, start=1):
            print(f"{index}. {interface['name']}")
        
        try:
            choice = int(input("\nEnter choice: "))
            if choice < 0 or choice >= len(interfaces):
                print("Invalid choice. Please enter a number listed above.\n")
                continue  
            selected_interface = interfaces[choice]
            print(f"\nYou selected: {selected_interface['name']}")
            return selected_interface 
        except ValueError:
            print("Invalid input. Please enter a number.\n")



def config_interface(int_params, filtered_interface, lacp_chasis):
    print(f"Configuring interface {filtered_interface['name']}:\n")
    for index, name in enumerate(int_params, start=1):
        print(f"{index}. {name}")
    while True:
        try:
            choice = int(input("\nEnter your choice: ")) 
            if choice < 0 or choice >= len(int_params):
                print("Invalid choice. Please enter a number listed above.\n")
                continue
            selected_param = int_params[choice - 1]
            print(f"\nYou selected: {selected_param}")
            print(choice)
            if choice == 1: 
                while True:
                    desc = input(f"Enter description for {filtered_interface['name']}: ")
                    if is_valid_string(desc):
                        gen_config = config_description(desc) 
                        break
                    else:
                        print("Invalid description. Please try again.")
            elif choice == 2:
                gen_config =  config_int_status()
            elif choice == 3:
                gen_config = set_int_params()
            elif choice == 4:
                gen_config = config_lacp()
            elif choice == 5:
                gen_config = config_lacp(lacp_chasis, filtered_interface)
            payload = f"""
            <configuration>
                <interfaces>
                    <interface operation="create">
                        <name>{filtered_interface['name']}</name>
                        {gen_config}
                    </interface>
                </interfaces>
            </configuration>"""
            print(payload)
            return payload
        except ValueError:
            print("Invalid input. Please enter a number.\n")

   
def config_description(desc):
        xml_data = f"""<description>{desc}</description>"""
        return xml_data

def config_int_status():
    while True:
        try:
            choice = int(input("Enter 1 to enable or 0 to disable the interface: "))
            if choice == 1:
                print("Interface will be enabled (removing <disable/> if present).")
                payload = """<disable operation="delete"/>"""
                break  
            elif choice == 0:
                print("Interface will be disabled (adding <disable/>).")
                payload = "<disable/>"
                break  
            else:
                print("Invalid choice. Please enter 1 to enable or 0 to disable.")
        except ValueError:
            print("Invalid input. Please enter a valid number (1 or 0).")
    return payload

def set_int_params():
    while True:
        try:
            unit = int(input("Enter unit number: "))
            print("Configure interface as L2, L2.5 (ISO), or L3  \n")
            choice = float(input("Enter choice 2 or 2.5 or 3:  "))
            data = ""

            if choice == 2:
                while True:
                    port_type = str(input("Specify 0 as access, 1 as trunk: "))
                    if port_type in ["0", "1"]:
                        port_mode = "access" if port_type == "0" else "trunk"
                        data = f"""
                                <ethernet-switching>
                                    <interface-mode>{port_mode}</interface-mode>
                                </ethernet-switching>"""
                        break
                    else:
                        print("Invalid choice selected, try again.")
            elif choice == 3:
                while True:
                    subnet = input("Enter the IP address (e.g., 192.168.1.1/24): ")
                    if is_valid_ipv4_address(subnet):
                        data = f"""
                                <inet>
                                    <address>
                                        <name>{subnet}</name>
                                    </address>
                                </inet>"""  
                        break
                    else:
                        print("IP address specified is not valid.")
            elif choice == 2.5:
                data  = """
                        <iso operation="create">
                        </iso>"""
            else:
                print("Invalid layer choice specified.")
                continue

            payload = f"""<unit>
                            <name>{unit}</name>
                            <family>
                                {data}
                            </family>       
                          </unit>"""
            return payload
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def config_mac():
    while True:
        mac_address = input("Please enter Mac Address (e.g., 50:00:00:0f:00:03): ")
        if is_valid_mac_address(mac_address):
            payload = f"""
                        <mac>{mac_address}</mac>"""
            print("MAC address configured successfully configured.")
            return payload
        else:
            print("You entered an invalid MAC address. Please try again.")


def config_lacp(lacp_chasis, filtered_interface):
    interface_name  = filtered_interface['name']
    if lacp_chasis:
        print(f"There are device_count {lacp_chasis['device-count']} already created")
        payload = """
            <configuration>
                <interfaces>
                    <interface operation="create">
                        <name>{interface_name}</name>
                        <gigether-options>
                            <ieee-802.3ad>
                                <bundle>{ae0}</bundle>
                            </ieee-802.3ad>
                        </gigether-options>
                        <aggregated-ether-options>
                            <lacp>          
                                <active/>   
                                <periodic>{fast}</periodic>
                            </lacp>         
                        </aggregated-ether-options>
                    </interface>            
                </interfaces>               
            </configuration>"""
        return payload
    else:
        print("No logical interfaces currently exist")
        print("Enable device_count before creating logical interfaces")
        device_count = int(input("Enter number of count: "))
        payload = """
            <configuration>
                <chassis operation="create">
                    <aggregated-devices>
                        <ethernet>
                            <device-count>{device_count}</device-count>
                        </ethernet>
                    </aggregated-devices>
                </chassis>
            <configuration>"""
        return payload 

