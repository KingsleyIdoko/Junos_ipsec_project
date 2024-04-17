import re
import ipaddress

def get_valid_string(prompt="Enter a valid name: ", text_length=5, max_words=10):
    pattern = r'^[a-zA-Z0-9_* ]+$'
    while True:
        input_string = input(prompt)
        if re.match(pattern, input_string):
            words = input_string.split()
            if len(words) <= max_words:
                return input_string  
            else:
                print(f"The string contains more than {max_words} words. Please try again.")
        else:
            print("Invalid input. Enter valid Characters")

def get_valid_name(prompt="Enter a valid name: "):
    pattern = r'^[a-zA-Z_-*][a-zA-Z0-9_*-]*$'
    while True:
        name = input(prompt)
        if re.match(pattern, name):
            return name
        else:
            print("Invalid name Entered. Try again")

def get_valid_choice(prompt, choices):
    while True:
        for i, choice in enumerate(choices, start=1):
            print(f"{i}. {choice}")
        selection = input(f"{prompt} (1-{len(choices)}): ")
        if selection.isdigit() and 1 <= int(selection) <= len(choices):
            return int(selection) - 1  
        else:
            print("Invalid choice, please try again.")


def get_valid_selection(prompt, choices):
    while True:
        for i, choice in enumerate(choices, start=1):
            print(f"{i}. {choice}")
        selection = input(f"{prompt} (1-{len(choices)}): ")
        if selection.isdigit() and 1 <= int(selection) <= len(choices):
            return choices[int(selection) - 1] 
        else:
            print("Invalid choice, please try again.")

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

def get_vlan_names_by_ids(received_vlans):
    input_str = input("Enter VLANs to assign (comma-separated, e.g. 10,20,40): ")
    vlan_ids = [vlan_id.strip() for vlan_id in input_str.split(',')]
    existing_vlan_names = []
    non_existing_vlan_ids = []
    for vlan_id in vlan_ids:
        found = False
        for vlan in received_vlans['vlan']:
            if vlan['vlan-id'] == vlan_id:
                existing_vlan_names.append(vlan['name'])
                found = True
                break
        if not found:
            non_existing_vlan_ids.append(vlan_id)
    if existing_vlan_names:
        print(f"Existing VLAN Names: {existing_vlan_names}")
    else:
        print("No matching VLANs found.")
    if non_existing_vlan_ids:
        print(f"Non-existing VLAN IDs: {non_existing_vlan_ids}")
    else:
        print("All entered VLAN IDs exist.")
    return existing_vlan_names, non_existing_vlan_ids
    

def is_valid_interfaces():
    pattern = r"^(ge|xe|et)-[0-9]/[0-9]/(?:[0-5]?[0-9]|60)$"
    while True:
        interface_name = input("Enter the interface name (or 'exit' to stop): ")
        if interface_name.lower() == 'exit':  
            print("Exiting...")
            return None
        if bool(re.match(pattern, interface_name)):
            print(f"{interface_name} is a valid interface name.")
            return interface_name  
        else:
            print(f"{interface_name} is not a valid interface name. Please try again.")

def get_ike_lifetime():
    ike_lifetime = input("Enter IKE Security Association lifetime (180..86400 seconds or press Enter for default 86400): ")
    if ike_lifetime.isdigit():
        ike_lifetime = int(ike_lifetime)
        ike_lifetime = max(180, min(ike_lifetime, 86400))
    else:
        ike_lifetime = 86400
    return ike_lifetime

def get_valid_passwd(prompt="Enter valid passwd"):
    while True:
        password = input(prompt)
        pattern = r'^[a-zA-Z0-9#$"]+$'
        if re.match(pattern, password):
            print("Password is valid.")
            return password  
        else:
            print("Password is invalid. It contains characters outside a-zA-Z0-9#$\".")




def print_xml_hierarchy(element, indent=""):
    print(f"{indent}{element.tag}: {element.text if element.text.strip() else ''} {element.attrib}")
    for child in element:
        print_xml_hierarchy(child, indent + "    ")