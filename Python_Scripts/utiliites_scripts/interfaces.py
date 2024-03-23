import re
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



def config_interface(int_params, filtered_interface):
    print(f"Please what would you like to configure for interface {filtered_interface['name']}:\n")
    for index, name in enumerate(int_params, start=1):
        print(f"{index}. {name}")

    while True:  
        try:
            choice = int(input("\nEnter choice: ")) - 1  
            if choice < 0 or choice >= len(int_params):
                print("Invalid choice. Please enter a number listed above.\n")
                continue  
            selected_param = int_params[choice]
            print(f"\nYou selected: {selected_param}")
            if choice == 0:
                description = input("Enter Description: ")
                print(description)  
            elif choice == 1:
                response = interface_status(filtered_interface['name'])
            elif choice == 2:
                response = ether_options(filtered_interface['name'])
        except ValueError:
            print("Invalid input. Please enter a number.\n")


def create_interface(interface_name):
    ['ethernet-switching','inet','inet6','iso','mpls']               
    payload = f"""
    <configuration>
            <interfaces>
                <interface operation="create">
                    <name>{interface_name}</name>
                    <unit>
                        <name>{config_unit()}</name>
                    </unit>
                </interface>
            </interfaces>
    </configuration>"""
    return payload 

def ether_options(interface_name):
    pass
def gigabit_options(interface_name):
    pass
def config_mac(interface_name):
    pass
def config_speed(interface_name):
    pass
def config_unit(interface_name):
    pass
def config_linkmode(interface_name):
    pass
def config_vlan_tagging(interface_name):
    pass
