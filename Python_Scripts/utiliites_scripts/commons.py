import re
import ipaddress

import re

def get_valid_string(prompt="Enter a valid name: ", text_length=5, max_words=10):
    pattern = r'^[a-zA-Z0-9_\- ]+$'
    while True:
        input_string = input(prompt)
        words = input_string.split()
        if re.match(pattern, input_string) and len(input_string) >= text_length:
            if len(words) <= max_words:
                return input_string  
            else:
                print(f"The string contains more than {max_words} words. Please try again.")
        else:
            print(f"Invalid input. Enter valid characters and ensure the name is at least {text_length} characters long.")

def validate_yes_no(prompt):
    pattern = r"^(yes|y|no|n)$"
    while True:
        input_str = input(prompt).strip()  
        if re.match(pattern, input_str, re.IGNORECASE):
            return input_str.lower().startswith('y') 
        else:
            print("Invalid input. Please enter 'yes' or 'no' (y/n).")

def get_valid_name(prompt="Enter a valid name: "):
    pattern = r'^[a-zA-Z_*][a-zA-Z0-9_*]*(-[0-9]+)?$'
    while True:
        name = input(prompt)
        if re.match(pattern, name):
            return name
        else:
            print("Invalid name Entered. Try again")

def get_valid_ipv4_name(prompt="Enter a valid IPv4 address or name: "):
    pattern = r'(^([a-zA-Z_*][a-zA-Z0-9_*]*(-[0-9]+)?)$)|(^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?(_[a-zA-Z0-9_*]+)?$)'
    while True:
        name = input(prompt)
        if re.match(pattern, name):
            return name
        else:
            print("Invalid name entered. Try again.")

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

def get_valid_network_address(prompt):
    while True:
        user_input = input(prompt)
        try:
            network = ipaddress.ip_network(user_input, strict=True)
            if network.prefixlen <= 32:
                return str(network)
        except ValueError:
            print("Invalid input. Please enter a valid IPv4 network address.")
            
def multiple_selection(prompt, options):
    print(prompt)
    for idx, option in enumerate(options, start=1):
        print(f"{idx}: {option}")
    selections = input("Enter your choices as comma-separated values (e.g., 1,2,3): ").split(',')
    selected_values = [options[int(choice.strip()) - 1] for choice in selections if choice.strip().isdigit() and 0 < int(choice.strip()) <= len(options)]
    return selected_values

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
    pattern = r"^(?:(ge|xe|et)-[0-9]/[0-9]/(?:[0-5]?[0-9]|60)|st0)$"
    while True:
        interface_name = input("Enter the interface name (ge|xe|et)-[0-9]/[0-9]/(?:[0-5]?[0-9]|60)|st0): ")
        if interface_name.lower() == 'exit':  
            print("Exiting...")
            return None
        if bool(re.match(pattern, interface_name)):
            print(f"{interface_name} is a valid interface name.")
            return interface_name  
        else:
            print(f"{interface_name} is not a valid interface name. Please try again.")


def get_ike_lifetime(prompt="Enter IKE Security Association lifetime (180..86400 seconds or press Enter for default 86400): ",
                    default=86400):
    ike_lifetime = input(prompt)
    if ike_lifetime.isdigit():
        ike_lifetime = int(ike_lifetime)
        ike_lifetime = max(180, min(ike_lifetime, 86400))  
    else:
        ike_lifetime = default  
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