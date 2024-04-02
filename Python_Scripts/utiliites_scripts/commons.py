import re
import ipaddress

def get_valid_string(prompt="Enter a valid name: "):
    pattern = r'^[a-zA-Z0-9_* ]+$'
    while True:
        input_string = input(prompt)
        if re.match(pattern, input_string):
            words = input_string.split()
            if len(words) <= 5:
                return input_string  
            else:
                print("The string contains more than 5 words. Please try again.")
        else:
            print("Invalid input. Please ensure the string contains only alphanumeric characters, underscores, asterisks, and spaces.")


def get_valid_integer(prompt="Enter a number: "):
    while True:
        try:
            user_input = input(prompt)
            user_input_as_int = int(user_input)
            return user_input_as_int
        except ValueError:
            print("Invalid input. Please enter a valid Number.")


def get_valid_ipv4_address(prompt="Enter an IPv4 address: "):
    while True:
        try:
            user_input = input(prompt)
            network = ipaddress.ip_network(user_input, strict=False)
            if network.prefixlen == 32:  
                return user_input
            else:
                ip_addr = ipaddress.ip_address(user_input.split('/')[0])
                if ip_addr == network.network_address or ip_addr == network.broadcast_address:
                    print("The IP address cannot be the network or broadcast address. Please try again.")
                else:
                    return user_input 
        except ValueError:
            print("Invalid input. Please enter a valid IPv4 address.")

def get_vlan_name_by_id(vlans):
    vlan_id = str(get_valid_integer("Enter vlan to assign: (Default vlan.0): ")) 
    vlan_exist = False
    vlan_name = None
    for vlan in vlans['vlan']:
        if vlan['vlan-id'] == vlan_id:  
            vlan_exist = True
            vlan_name = vlan['name']
            break  
    if vlan_exist:
        return vlan_name, vlan_exist
    else:
        print(f"VLAN {vlan_id} does not exist.")
        return vlan_id, vlan_exist
    

def is_valid_interfaces():
    pattern = r"^(ge|xe|et)-[0-9]/[0-9]/(?:[0-5]?[0-9]|60)$"
    while True:
        interface_name = input("Enter the interface name (or 'exit' to stop): ")
        if interface_name.lower() == 'exit':  # Provide a way to exit the loop
            print("Exiting...")
            return None
        if bool(re.match(pattern, interface_name)):
            print(f"{interface_name} is a valid interface name.")
            return interface_name  # Return the valid interface name
        else:
            print(f"{interface_name} is not a valid interface name. Please try again.")




