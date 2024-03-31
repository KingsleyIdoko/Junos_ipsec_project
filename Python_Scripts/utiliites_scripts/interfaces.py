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
        network = ipaddress.ip_network(address, strict=False)
        if network.prefixlen == 32:
            return True
        else:
            ip_addr = ipaddress.ip_address(address.split('/')[0])
            if ip_addr == network.network_address or ip_addr == network.broadcast_address:
                return False
            else:
                return True

    except ValueError:
        return False

    
def get_lacp_periodic_mode():
    pattern = re.compile(r'^(fast|slow)$', re.IGNORECASE)  
    while True:
        lacp_periodic = input("Enter LACP periodic mode (fast/slow): ")
        if pattern.match(lacp_periodic):
            return lacp_periodic.lower()  
        else:
            print("Invalid input. Please enter 'fast' or 'slow'. Try again.")

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
            choice = int(input("\nEnter choice: ")) - 1
            if choice < 0 or choice >= len(interfaces):
                print("Invalid choice. Please enter a number listed above.\n")
                continue  
            selected_interface = interfaces[choice]
            print(f"\nYou selected: {selected_interface['name']}")
            return selected_interface 
        except ValueError:
            print("Invalid input. Please enter a number.\n")

def config_interface(int_params, filtered_interface, lacp_chasis):
    delete_int = None
    print(f"Configuring interface {filtered_interface['name']}:\n")
    for index, name in enumerate(int_params, start=1):
        print(f"{index}. {name}")
    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if choice < 1 or choice > len(int_params):
                print("Invalid choice. Please enter a number listed above.\n")
                continue
            selected_param = int_params[choice - 1]
            print(f"\nYou selected: {selected_param}")
            interface_name = filtered_interface.get('name')
            old_description =  filtered_interface.get('description')
            ip_address_name = filtered_interface['unit']['family']['inet']['address']['name']
            gen_config = None  
            if choice == 1: 
                while True:
                    desc = input(f"Enter description for {filtered_interface['name']}: ")
                    if is_valid_string(desc):
                        gen_config = config_description(desc, interface_name, old_description)
                        break
                    else:
                        print("Invalid description. Please try again.")
                        continue
            elif choice == 2:
                gen_config = config_int_status(interface_name, filtered_interface)
            elif choice == 3:
                gen_config = set_int_params(interface_name, ip_address_name)
            elif choice == 4:
                delete_int = default_interface(filtered_interface)
                gen_config = config_lacp(lacp_chasis, filtered_interface)
            if gen_config:  
                payload = f"""
                    <configuration>
                        <interfaces>
                            {gen_config}
                        </interfaces>
                    </configuration>"""
                print(payload)
                return (delete_int, payload) if delete_int else payload
            else:
                print("No configuration changes to apply.")
                return delete_int if delete_int else None
        except ValueError:
            print("Invalid input. Please enter a number.\n")

   
def config_description(desc, interface_name, old_description=None):
        if old_description:
            xml_data = f"""   <interface>
                                    <name>{interface_name}</name>
                                    <description operation="delete"/>
                                    <description operation="create">{desc}</description>
                                    </interface>"""
            return xml_data
        else:
            xml_data = f"""   <interface>
                                    <name>{interface_name}</name>
                                    <description operation="create">{desc}</description>
                                    </interface>"""
            return xml_data
def config_int_status(interface_name, filtered_interface):
    while True:
        try:
            choice = int(input("Enter 1 to enable or 0 to disable the interface: "))
            disabled_interface = check_interface_disabled(filtered_interface)           
            if choice == 1:
                if disabled_interface:  
                    print("Interface will be enabled (removing <disable/> if present).")
                    payload = f"""
                                <interface>
                                    <name>{interface_name}</name>
                                    <disable operation="delete"/>
                                </interface>"""
                else:
                    print("Interface is already enabled.")
                    payload = None  
                break
            elif choice == 0:
                if not disabled_interface:  
                    print("Interface will be disabled (adding <disable/>).")
                    payload = f"""
                                <interface>
                                    <name>{interface_name}</name>
                                    <disable operation="create"/>
                                </interface>"""
                else:
                    print("Interface is already disabled.")
                    payload = None  
                break
            else:
                print("Invalid choice. Please enter 1 to enable or 0 to disable.")
        except ValueError:
            print("Invalid input. Please enter a valid number (1 or 0).")
    return payload


def set_int_params(interface_name, ip_address_name):
    while True:
        try:
            unit = int(input("Enter unit number: "))
            print("Configure interface as :Layer(2), Layer(2.5)(ISO), or Laywer(3)  \n")
            choice = float(input("Enter choice 2 or 2.5 or 3:  "))
            data = ""

            if choice == 2:
                while True:
                    port_type = str(input("Specify 0 as access, 1 as trunk: "))
                    if port_type in ["0", "1"]:
                        port_mode = "access" if port_type == "0" else "trunk"
                        data = f"""<ethernet-switching>
                                            <interface-mode>{port_mode}</interface-mode>
                                        </ethernet-switching>"""
                        break
                    else:
                        print("Invalid choice selected, try again.")
            elif choice == 3:
                while True:
                    subnet = input("Enter the IP address (e.g. 192.168.1.1/24): ")
                    if subnet == ip_address_name:
                        print(f"IP Address already exist on the interface ({interface_name})")
                    elif is_valid_ipv4_address(subnet):
                        if ip_address_name:
                            data =      f"""<inet>
                                            <address insert="after"  key="[ name='{ip_address_name}' ]" operation="create">
                                                    <name>{subnet}</name>
                                                </address>
                                        </inet>"""  
                        else:
                            data =      f"""<inet>
                                                <address>
                                                    <name>{subnet}</name>
                                                </address>
                                        </inet>"""   
                        break
                    else:
                        print("IP address specified is not valid.")
            elif choice == 2.5:
                data  = f"""<iso operation="create">
                                        </iso>"""
            else:
                print("Invalid layer choice specified.")
                continue
            payload = f"""<interface>
                                <name>{interface_name}</name>
                                <unit>
                                    <name>{unit}</name>
                                    <family>
                                        {data}
                                    </family>       
                                </unit>
                            </interface>"""
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

def config_mtu():
    pass

def config_speed():
    pass

def config_lacp(lacp_chasis, filtered_interface):
    interface_name = filtered_interface['name']
    if lacp_chasis:
        logical_ports_count = int(lacp_chasis['device-count'])
        print(logical_ports_count)
        while True:
            try:
                ae_port = int(input("Enter logical port number: "))
                if 0 <= ae_port < logical_ports_count:
                    print(f"ae{ae_port} was selected!")
                    ae_port_str = f"ae{ae_port}"
                    break
                else:
                    print(f"You entered an invalid number, select number (0 - {logical_ports_count -1 })")
            except ValueError:
                print("Invalid input. Please enter a numeric value.")
        lacp_periodic_mode = get_lacp_periodic_mode()

        payload = f"""
                        <gigether-options>
                            <ieee-802.3ad>
                                <bundle>{ae_port_str}</bundle>
                            </ieee-802.3ad>
                        </gigether-options>
                        <aggregated-ether-options>
                            <lacp>
                                <active/>
                                <periodic>{lacp_periodic_mode}</periodic>
                            </lacp>
                        </aggregated-ether-options>"""
        return payload
    else:
        device_count = int(input("Enter number of logical ports to create: "))
        payload = f"""
            <configuration>
                <chassis operation="create">
                    <aggregated-devices>
                        <ethernet>
                            <device-count>{device_count}</device-count>
                        </ethernet>
                    </aggregated-devices>
                </chassis>
            </configuration>"""
        return payload


def default_interface(interface_name):
    name = interface_name.get("name")
    payload = f"""
        <configuration>
            <interfaces>
                <interface operation="delete">
                    <name>{name}</name>
                </interface>
            </interfaces>
    </configuration>"""
    return payload



def check_interface_disabled(interface_config):
    if 'disable' in interface_config:
        if interface_config['disable'] is None:
            return True
        else:
            return True
    else:
        return False


