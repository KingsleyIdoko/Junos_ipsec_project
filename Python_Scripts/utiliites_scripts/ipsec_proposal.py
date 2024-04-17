from utiliites_scripts.commons import (get_valid_name, get_valid_string, get_ike_lifetime,
                                        get_valid_selection)
import xml.etree.ElementTree as ET

select_enc_algo = ['3des-cbc', 'aes-128-cbc', 'aes-128-gcm', 'aes-192-cbc', 'aes-192-gcm','aes-256-cbc', 'aes-256-gcm', 'des-cbc']
select_auth_algo = ['hmac-md5-96', 'hmac-sha-256-128', 'hmac-sha1-96']
protocol  = ["esp", "ah"]

def gen_ipsec_proposal_config(**kwargs):
    old_ipsec_proposal = kwargs.get('old_ipsec_proposal', None)
    if old_ipsec_proposal:
        print(f"There are {len(old_ipsec_proposal)} existing IPsec Policy on the device")
        for i, choice in enumerate(old_ipsec_proposal, start=1):
            print(f"{i}. {choice}")
    ipsec_policy_name = get_valid_name("Enter new IPsec Proposal name: ")
    description = get_valid_string("Enter IPsec proposal description: ", max_words=10)
    protocol = ipsec_selection(prompt="Select IPsec Encapsulation Protocol: ", sel=protocol)
    encryption_algorithm = ipsec_selection(prompt="Select IPsec Encryption Algorithm: ", sel=select_enc_algo)
    auth_algorithm = ''
    if "gcm" not in encryption_algorithm:
        auth_algorithm = ipsec_selection(prompt="Select IPsec Auth Algorithm: ", sel=select_auth_algo)
    ipsec_lifetime = get_ike_lifetime()
    if old_ipsec_proposal:
        last_ipsec_name = old_ipsec_proposal[-1]
        insert_attribute = f'insert="after" key="[ name=\'{last_ipsec_name}\' ]"'
    else:
        insert_attribute = ""
        print("No existing IPSEC policies found. Creating the first policy.")
    payload = f"""
        <configuration>
        <security>
            <ipsec>
                <proposal {insert_attribute} operation="create" >
                    <name>{ipsec_policy_name}</name>
                    <description>{description}</description>
                    <protocol>{protocol}</protocol>
                    <encryption-algorithm>{encryption_algorithm}</encryption-algorithm>
                    {'<authentication-algorithm>' + auth_algorithm + '</authentication-algorithm>' if auth_algorithm else ''}
                    <lifetime-kilobytes>{ipsec_lifetime}</lifetime-kilobytes>
                </proposal>
            </ipsec>
        </security>
    </configuration>""".strip()
    return payload

def ipsec_selection(prompt, sel):
    while True:
        selection = get_valid_selection(prompt, sel)
        if selection.lower() in [s.lower() for s in sel]:
            return selection
        print("Invalid selection. Please try again.")

def extract_proposals(ike_policy):
    ike_policy = [ike_policy] if isinstance(ike_policy, dict) else ike_policy
    return [policy['proposals'] for policy in ike_policy if 'proposals' in policy]

def select_policy_to_update(ike_policies):
    print("Select a proposal to update:")
    for i, policy in enumerate(ike_policies, start=1):
        print(f"{i}. {policy['name']}")
    selection = input("Enter the number of the proposal: ")
    if selection.isdigit() and 1 <= int(selection) <= len(ike_policies):
        return ike_policies[int(selection) - 1]
    else:
        print("Invalid selection.")
        return None

def update_ipsec_proposal(**kwargs):
    ipsec_proposal = kwargs.get('ipsec_proposal')
    if not ipsec_proposal:
        print("No IPsec proposal provided.")
        return None, None
    selected_proposal = select_policy_to_update(ipsec_proposal)
    if not selected_proposal:
        print("No policy selected or invalid selection. Exiting update process.")
        return None, None
    old_ipsec_name = selected_proposal['name']
    initial_encryption_algo = selected_proposal['encryption-algorithm']
    continue_update = True
    while continue_update:
        policy_attributes = {
            'name': selected_proposal.get('name'),
            'description': selected_proposal.get('description'),
            'protocol': selected_proposal.get('protocol'),
            'encryption-algorithm': selected_proposal.get('encryption-algorithm'),
            'authentication-algorithm': selected_proposal.get('authentication-algorithm'),
            'lifetime-kilobytes': selected_proposal.get('lifetime-kilobytes'),
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        selected_key, new_value = selected_attribute.split(':')
        selected_key = selected_key.strip()
        if selected_key == 'encryption-algorithm':
            new_value = get_valid_selection("Select encryption algorithm: ", select_enc_algo)
            if 'gcm' in new_value and selected_proposal['authentication-algorithm']:
                print("Deleting 'authentication-algorithm' due to GCM selection.")
                selected_proposal['authentication-algorithm'] = None
            elif 'gcm' not in new_value and 'gcm' in initial_encryption_algo:
                print("GCM no longer used. Please select a new authentication algorithm.")
                selected_proposal['authentication-algorithm'] = get_valid_selection("Select authentication algorithm: ", select_auth_algo)
            selected_proposal[selected_key] = new_value
        elif selected_key == 'authentication-algorithm':
            if 'gcm' in selected_proposal['encryption-algorithm']:
                print("Authentication Algorithm cannot be updated, GCM is selected in the Encryption Algorithm")
                continue
            new_value = get_valid_selection("Select authentication algorithm: ", select_auth_algo)
            selected_proposal[selected_key] = new_value
        elif selected_key == "description":
            selected_proposal[selected_key] = get_valid_string("Enter new description: ")
        else:
            new_value = get_valid_name(f"Enter the new value for {selected_key}: ") if selected_key != 'lifetime-kilobytes' else get_ike_lifetime()
            selected_proposal[selected_key] = new_value
        another_change = input("Would you like to make another change? (yes/no): ").strip().lower()
        if another_change != 'yes':
            continue_update = False
    insert_attribute = ""  
    if old_ipsec_name != selected_proposal['name']:
        insert_attribute = f'insert="after" key="[ name=\'{old_ipsec_name}\' ]" operation="create"'
    payload = f"""
    <configuration>
        <security>
            <ipsec>
                <proposal {insert_attribute}>
                    <name>{selected_proposal['name']}</name>
                    <description>{selected_proposal['description']}</description>
                    <protocol>{selected_proposal['protocol']}</protocol>
                    <encryption-algorithm>{selected_proposal['encryption-algorithm']}</encryption-algorithm>
                    {'<authentication-algorithm operation="delete"/>' if selected_proposal['authentication-algorithm'] is None else '<authentication-algorithm>' + selected_proposal['authentication-algorithm'] + '</authentication-algorithm>'}
                    <lifetime-kilobytes>{selected_proposal['lifetime-kilobytes']}</lifetime-kilobytes>
                </proposal>
            </ipsec>
        </security>
    </configuration>""".strip()
    return (payload, old_ipsec_name) if old_ipsec_name != selected_proposal['name'] else (payload, None)

def del_ipsec_proposal(**kwargs):
    try:
        ipsec_proposal_name = kwargs.get("ipsec_proposal_name")
        if not ipsec_proposal_name:
            raise ValueError("No IPsec proposal provided for deletion.")
        used_ipsec_proposal = kwargs.get("used_ipsec_proposal", [])
        if isinstance(used_ipsec_proposal, list):
            used_ipsec_proposal = [used_ipsec_proposal]
        if not isinstance(ipsec_proposal_name, list):
            del_proposal_name = ipsec_proposal_name
        else:
            del_proposal_name = get_valid_selection("Select proposal to delete: ", ipsec_proposal_name)
        if not del_proposal_name:
            raise ValueError("Invalid selection or no selection made.")
        if used_ipsec_proposal != None:
            if del_proposal_name in used_ipsec_proposal:
                message = f"{del_proposal_name} is referenced in an IKE Gateway and cannot be deleted."
                raise ReferenceError(message)
        payload = f"""
        <configuration>
                <security>
                    <ipsec>
                        <proposal operation="delete">
                            <name>{del_proposal_name}</name>
                        </proposal>
                    </ipsec>
                </security>
        </configuration>""".strip()
        return payload
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
