from utiliites_scripts.commons import (get_valid_selection,
                                       get_valid_network_address, get_valid_ipv4_address)
import re
from sec_interfaces import InterfaceManager
interface_manager = InterfaceManager()

def gen_static_route_config(**kwargs):
    static_routes_input = kwargs.get('static_route', [])
    new_static_routes = []
    if static_routes_input:
        print(f"There are {len(static_routes_input)} existing static routes on the device:")
        for i, route in enumerate(static_routes_input, start=1):
            print(f"{i}. Route: {route['name']} next-hop {route['next-hop']}")
    while True:
        select_prefix = get_valid_network_address("Enter new prefix-length (e.g., 192.168.1.0/24): ")
        if any(route['name'] == select_prefix for route in new_static_routes + static_routes_input):
            print(f"The prefix {select_prefix} already exists on the device. Please enter a different prefix.")
            continue
        next_hop = configure_next_hop()
        new_static_routes.append({'name': select_prefix, 'next-hop': next_hop})
        print(f"Added route: {select_prefix} next-hop {next_hop}")
        if input("Add another route? (yes/no): ").lower() != 'yes':
            break
    insert_attribute = "" if static_routes_input else 'operation="create"'
    routes_payload = "".join(f""" <route>
                                <name>{route['name']}</name>
                                <next-hop>{route['next-hop']}</next-hop>
                            </route>""" for route in new_static_routes)
    payload = f"""
            <configuration>
                    <routing-options {insert_attribute}>
                        <static>
                            {routes_payload}
                        </static>
                    </routing-options>
            </configuration>""".strip()
    print(payload)
    return payload

def prompt_for_ike_policy_mode():
    while True:
        sel_mode = ["main", "aggressive"]
        mode = get_valid_selection("Select IKE Policy mode: ", sel_mode)
        if mode.lower() in ["main", "aggressive"]:
            return mode
        print("Invalid mode selected. Please choose either 'main' or 'aggressive'.")


def extract_proposals(ike_policy):
    ike_policy = [ike_policy] if isinstance(ike_policy, dict) else ike_policy
    return [policy['proposals'] for policy in ike_policy if 'proposals' in policy]

def select_route_to_update(static_route):
    print("Select a static route to update:")
    for i, policy in enumerate(static_route, start=1):
        print(f"{i}. {policy['name']} 'next-hop' {policy['next-hop']} " )
    selection = input("Enter the number of the route: ")
    if selection.isdigit() and 1 <= int(selection) <= len(static_route):
        return static_route[int(selection) - 1]
    else:
        print("Invalid selection.")
        return None

def update_static_route(**kwargs):
    static_routes = kwargs.get('static_route')
    if not static_routes:
        print("No static routes provided.")
        return None
    payloads = []  
    continue_update = True
    while continue_update:
        selected_route = select_route_to_update(static_routes)
        if not selected_route:
            print("No static route selected or invalid selection. Exiting update process.")
            return payloads
        policy_attributes = {
            'name': selected_route.get('name'),
            'next-hop': selected_route.get('next-hop')
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        if not selected_attribute:
            print("Invalid selection or no selection made.")
            continue  
        selected_key = selected_attribute.split(':')[0].strip()
        if selected_key == "next-hop":
            old_next_hop = selected_route[selected_key]
            new_next_hop = configure_next_hop()
            print(f"Current next-hop is {old_next_hop}.")
            while True:
                replace_or_merge = input("Do you want to replace it (replace/merge)? ").lower()
                if re.match(r"^(replace|merge)$", replace_or_merge):
                    break
                else:
                    print("Invalid input. Please enter 'replace' or 'merge'.")
            if replace_or_merge == 'replace':
                selected_route[selected_key] = new_next_hop
                del_route = f"""<route operation="delete">
                                    <name>{selected_route['name']}</name>
                                </route>"""
                payload = f"""
                    <configuration>
                        <routing-options>
                            <static>
                                {del_route}
                                <route>
                                    <name>{selected_route['name']}</name>
                                    <next-hop>{selected_route['next-hop']}</next-hop>
                                </route>
                            </static>
                        </routing-options>
                    </configuration>""".strip()
                payloads.append(payload)
            else:
                print("Merge is not supported yet. Please try replacing the value.")
                continue
        else:
            print("Prefix Name cannot be edited. Please create a new route.")
            continue
        if input("Do you want to update another route? (yes/no): ").lower() != 'yes':
            continue_update = False
    return payloads


def del_static_route(**kwargs):
    try:
        static_names = kwargs.get("route_name")
        if not static_names:
            raise ValueError("No policy names provided for deletion.")
        if not isinstance(static_names, list):
            del_vpn_name = [static_names]
        else:
            del_vpn_name = get_valid_selection("Select Policy to delete: ", static_names)
        if not del_vpn_name:
            raise ValueError("Invalid selection or no selection made.")
        payload = f"""
        <configuration>
                <routing-options>
                    <static>
                        <route operation="delete">
                            <name>{del_vpn_name}</name>
                        </route>
                    </static>
                </routing-options>
        </configuration>""".strip()
        return payload
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None

def configure_next_hop():
    """Allows the user to configure the next hop by choosing between an IP address or an interface."""
    while True:
        choice = input("Specify interface type (Prefix/Interface): ").lower()
        if re.match(r"^(prefix|interface)$", choice):
            break
        else:
            print("Invalid input. Please enter 'prefix' or 'interface'.")
    if choice == "prefix":
        return get_valid_ipv4_address("Enter a valid IPv4 address: ")
    else:
        interfaces = interface_manager.get_interfaces(get_interface_name=True)  
        return get_valid_selection("Select next-hop interface: ", interfaces)