from utiliites_scripts.commons import (get_valid_name, get_ike_lifetime,get_valid_selection)

def gen_ipsec_vpn_config(**kwargs):
    old_ipsec_vpn = kwargs.get('old_ipsec_vpn', [])
    ipsec_policies = kwargs.get('ipsec_policy', [])
    ike_gateways = kwargs.get('ike_gateway', [])
    if old_ipsec_vpn:
        print(f"There are {len(old_ipsec_vpn)} existing IPsec VPN configurations on the device")
        for i, choice in enumerate(old_ipsec_vpn, start=1):
            print(f"{i}. {choice}")
    ipsec_vpn_name = get_valid_name("Enter new IPsec VPN name: ")
    while ipsec_vpn_name in old_ipsec_vpn:
        print("This IPsec VPN name is already in use. Please choose another name.")
        ipsec_vpn_name = get_valid_name("Enter new IPsec VPN name: ")
    establish_tunnels = get_valid_selection("Establish tunnels: ", ['immediately', 'on-traffic'])
    selected_ipsec_policy = get_valid_selection("Select IPsec Policy: ", ipsec_policies)
    selected_ike_gateway = get_valid_selection("Select IKE Gateway: ", ike_gateways)
    idle_time = get_ike_lifetime(prompt="Enter idle time (60 to 999999 seconds): ")
    insert_attribute = 'operation="create"'
    if old_ipsec_vpn:
        last_vpn_name = old_ipsec_vpn[-1]
        insert_attribute = f'insert="after" key="[ name=\'{last_vpn_name}\' ]" operation="create"'
    else:
        print("No existing IPsec VPN found. Creating the first VPN.")
    payload = f"""
        <configuration>
                <security>
                    <ipsec>
                        <vpn {insert_attribute}>
                            <name>{ipsec_vpn_name}</name>
                            <ike>
                                <gateway>{selected_ike_gateway}</gateway>
                                <idle-time>{idle_time}</idle-time>
                                <ipsec-policy>{selected_ipsec_policy}</ipsec-policy>
                            </ike>
                            <establish-tunnels>{establish_tunnels}</establish-tunnels>
                        </vpn>
                    </ipsec>
                </security>
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

def select_policy_to_update(ipsec_vpns):
    print("Select a policy to update:")
    for i, policy in enumerate(ipsec_vpns, start=1):
        print(f"{i}. {policy['name']}")
    selection = input("Enter the number of the policy: ")
    if selection.isdigit() and 1 <= int(selection) <= len(ipsec_vpns):
        return ipsec_vpns[int(selection) - 1]
    else:
        print("Invalid selection.")
        return None
                                      
def update_ipsec_vpn(**kwargs):
    ipsec_vpns = kwargs.get('ipsec_vpns')
    old_vpn_names = kwargs.get('old_vpn_names', [])
    ipsec_policies = kwargs.get('ipsec_policy', [])
    ike_gateways = kwargs.get('ike_gateway', [])
    selected_vpn = select_policy_to_update(ipsec_vpns)
    if not selected_vpn:
        print("No policy selected or invalid selection. Exiting update process.")
        return None, None
    old_vpn_name = selected_vpn['name']
    continue_update = True
    while continue_update:
        policy_attributes = {
            'name': selected_vpn.get('name'),
            'ike_gateway': selected_vpn.get('ike', {}).get('gateway'),
            'ike_idle_time': selected_vpn.get('ike', {}).get('idle-time'),
            'ipsec_policy': selected_vpn.get('ike', {}).get('ipsec-policy'),
            'establish_tunnels': selected_vpn.get('establish-tunnels')
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        selected_key = selected_attribute.split(':')[0].strip()
        if selected_key == 'ike_gateway':
            selected_vpn['ike']['gateway'] = get_valid_selection("Select a new Ike Gateway: ", ike_gateways)
        elif selected_key == 'ipsec_policy':
            selected_vpn['ike']['ipsec-policy'] = get_valid_selection("Select a new IPsec Policy: ", ipsec_policies)
        elif selected_key == 'establish_tunnels':
            selected_vpn['establish-tunnels'] = get_valid_selection("Select a new mode: ", ['immediately', 'on-traffic'])
        elif selected_key == 'ike_idle_time':
            selected_vpn['ike']['idle-time'] = get_ike_lifetime(prompt="Enter idle time (60 to 999999 seconds): ", default=300)
        else:
            selected_vpn[selected_key] = get_valid_name(f"Enter the new value for {selected_key}: ")
        another_change = input("Would you like to make another change? (yes/no): ").strip().lower()
        continue_update = another_change == 'yes'
    if old_vpn_name != selected_vpn['name']:
        insert_attribute = 'operation="create"'
        if old_vpn_names and len(old_vpn_names) > 1 and old_vpn_name in old_vpn_names:
            last_vpn_name = old_vpn_names[-1] if old_vpn_names[-1] != old_vpn_name else old_vpn_names[-2]
            insert_attribute = f'insert="after" key="[ name=\'{last_vpn_name}\' ]" operation="create"'
    else:
        insert_attribute = ""
    payload = f"""
    <configuration>
        <security>
            <ipsec>
                <vpn {insert_attribute}>
                    <name>{selected_vpn['name']}</name>
                    <ike>
                        <gateway>{selected_vpn['ike']['gateway']}</gateway>
                        <idle-time>{selected_vpn['ike']['idle-time']}</idle-time>
                        <ipsec-policy>{selected_vpn['ike']['ipsec-policy']}</ipsec-policy>
                    </ike>
                    <establish-tunnels>{selected_vpn['establish-tunnels']}</establish-tunnels>
                </vpn>
            </ipsec>
        </security>
    </configuration>""".strip()
    print(old_vpn_name)
    return (payload, old_vpn_name) if old_vpn_name != selected_vpn['name'] else (payload, None)


def del_ipsec_vpn(**kwargs):
    try:
        vpn_names = kwargs.get("vpn_name")
        if not vpn_names:
            raise ValueError("No policy names provided for deletion.")
        used_policy = kwargs.get("used_policy", [])
        if isinstance(used_policy, list):
            used_policy = [used_policy]
        if not isinstance(vpn_names, list):
            del_vpn_name = vpn_names
        else:
            del_vpn_name = get_valid_selection("Select Policy to delete: ", vpn_names)
        if not del_vpn_name:
            raise ValueError("Invalid selection or no selection made.")
        if used_policy != None:
            if del_vpn_name in used_policy:
                message = f"{del_vpn_name} is referenced in an IKE Gateway and cannot be deleted."
                raise ReferenceError(message)
        payload = f"""
        <configuration>
                <security>
                    <ipsec>
                        <vpn operation="delete">
                            <name>{del_vpn_name}</name>
                        </vpn>
                    </ipsec>
                </security>
        </configuration>""".strip()
        return payload
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
