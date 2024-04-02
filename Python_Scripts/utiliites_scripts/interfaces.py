import re
import ipaddress
from vlansOper import VlansManager
from utiliites_scripts.commons import (get_valid_ipv4_address, 
                                       get_valid_integer, 
                                       get_valid_string,
                                       get_vlan_name_by_id)
                                       
vlan_manager = VlansManager(config_file="config.yml")
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
            try:
                ip_address_name = filtered_interface['unit']['family']['inet']['address']['name']
            except:
                ip_address_name = None
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
                gen_config = set_int_params(interface_name, ip_address_name, filtered_interface)
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


def set_int_params(interface_name, ip_address_name=None, filtered_interface=None):
    data = []
    while True:
        try:
            unit = get_valid_integer("Enter unit number: ")
            print("Configure interface as :Layer(2), Layer(2.5)(ISO), or Laywer(3)  \n")
            choice = float(input("Enter choice 2 or 2.5 or 3:  "))
            if choice == 2: 
                data = configure_layer2(data=data,filtered_interface=filtered_interface)
            elif choice == 3: 
                data =  configure_layer3(data=data, filtered_interface=filtered_interface, 
                                        ip_address_name=ip_address_name)
            elif choice == 2.5:
                return configure_layer25(data=data)
            else:
                print("Invalid layer choice specified.")
                continue
            if isinstance(data, list):
                data = "\n".join(data)
            payload = f"""<interface>
                                <name>{interface_name}</name>
                                <unit>
                                    <name>{unit}</name>
                                    <family>
                                        {data}
                                    </family>       
                                </unit>
                            </interface>"""
            payload
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


def enable_interface_config(interface_name, unit):
    payload = f"""
                <configuration>
                    <interfaces>
                        <interface operation="create">
                            <name>{interface_name}</name>
                            <unit>
                                <name>{unit}</name>
                            </unit>
                    </interface>
                </interfaces>
                </configuration>"""
    return payload

def configure_layer2(data, filtered_interface):
    while True:
        try: 
            rm_l3_config = filtered_interface['unit']['family'].get('inet')
            if rm_l3_config:
                print("Layer 3 configuration exist on the interface removing it")
                inet_family = f"""<inet operation="delete"/>"""
                data.append(inet_family)
        except:
            print("No existing Layer 2 configurations") 
        port_type = str(input("Specify 0 as access, 1 as trunk: "))
        if port_type in ["0", "1"]:
            eth_switch_config = []
            port_mode = "access" if port_type == "0" else "trunk"
            vlan_members, *_ = vlan_manager.get_vlans()
            assign_vlan  = get_valid_string("Assign vlan? Enter yes/no: ")
            if assign_vlan == "yes":
                if vlan_members:
                    while True:
                        updated_vlan_members, *_ = vlan_manager.get_vlans()
                        vlan_name, exist_vlan = get_vlan_name_by_id(updated_vlan_members)
                        if exist_vlan:
                            vlan_name = f"""<vlan>
                                    <members>{vlan_name}</members>
                                </vlan>"""
                            eth_switch_config.append(vlan_name)
                            break
                        else:
                            vlan_id = vlan_name
                            print(f"Creating Vlan {vlan_id}")
                            vlan_name = get_valid_string("Enter vlan name: ")
                            payload = vlan_manager.create_vlan(vlan_id, vlan_name, commit_directly=True)
                            print(f"Vlan {vlan_id} successfully created, Please select it again")
            else:
                return None
            port_type =  f"""
                                <interface-mode>{port_mode}</interface-mode>
                            """
            eth_switch_config.append(port_type)
            final_eth_config = "\n".join(eth_switch_config)
            eth_switch = f"""<ethernet-switching>
                                {final_eth_config}
                            </ethernet-switching>"""
            data.append(eth_switch)
            break
        else:
            print("Invalid choice selected, try again.")

def configure_layer3(data, filtered_interface, ip_address_name):
    data = []
    while True:
        try:
            rm_l2_config = filtered_interface['unit']['family'].get('ethernet-switching')
            if rm_l2_config:
                print("Layer 2 configuration exist on the interface removing it")
                eth_switch = f"""<ethernet-switching operation="delete"/>"""
                data.append(eth_switch)
        except:
            print("No existing Layer 2 configurations")
        subnet = get_valid_ipv4_address("Enter the IP address (e.g. 192.168.1.1/24): ")
        if subnet == ip_address_name:
            print(f"IP Address already exist on the interface ({interface_name})")
        elif is_valid_ipv4_address(subnet):
            if ip_address_name:
                inet =      f"""<inet>
                                <address insert="after"  key="[ name='{ip_address_name}' ]" operation="create">
                                        <name>{subnet}</name>
                                    </address>
                            </inet>"""  
                data.append(inet)
            else:
                inet =      f"""<inet>
                                    <address>
                                        <name>{subnet}</name>
                                    </address>
                            </inet>"""  
                data.append(inet) 
            break
        else:
            print("IP address specified is not valid.")

def configure_layer25():
    data  = f"""<iso operation="create">
                </iso>"""