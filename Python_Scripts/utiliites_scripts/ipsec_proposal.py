from utiliites_scripts.commons import (get_valid_name, get_valid_string, get_ike_lifetime,
                                        get_valid_selection)
import xml.etree.ElementTree as ET

select_enc_algo = ['3des-cbc', 'aes-128-cbc', 'aes-128-gcm', 'aes-192-cbc', 'aes-192-gcm','aes-256-cbc', 'aes-256-gcm', 'des-cbc']
select_auth_algo = ['hmac-md5-96', 'hmac-sha-256-128', 'hmac-sha1-96']
protocol  = ["esp", "ah"]

def ipsec_selection(prompt, options):
    """Allow user to select a valid option for IPsec configurations."""
    print(prompt)
    for idx, option in enumerate(options, 1):
        print(f"{idx}. {option}")
    while True:
        choice = input("Select an option by number: ")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Invalid selection. Please try again with a valid option number.")

def gen_ipsec_proposal_config(**kwargs):
    old_ipsec_proposal = kwargs.get('old_ipsec_proposal', [])
    if old_ipsec_proposal:
        print(f"There are {len(old_ipsec_proposal)} existing IPsec policies on the device:")
        for i, proposal in enumerate(old_ipsec_proposal, start=1):
            print(f"{i}. {proposal}")
        last_ipsec_name = old_ipsec_proposal[-1]  
        insert_attribute = f'insert="after" key="[ name=\'{last_ipsec_name}\' ]"'
    else:
        print("No existing IPSEC policies found. Creating first proposal.")
        insert_attribute = ""
    ipsec_policy_name = get_valid_name("Enter new IPsec Proposal name: ")
    description = get_valid_string("Enter IPsec proposal description: ")
    selected_protocol = ipsec_selection("Select IPsec Encapsulation Protocol: ", ["esp", "ah"])
    encryption_algorithm = ipsec_selection("Select IPsec Encryption Algorithm: ", select_enc_algo)
    auth_algorithm = ''
    if "gcm" not in encryption_algorithm.lower():
        auth_algorithm = ipsec_selection("Select IPsec Auth Algorithm: ", select_auth_algo)
    ipsec_lifetime = get_ike_lifetime()
    payload = f"""
        <configuration>
            <security>
                <ipsec>
                    <proposal {insert_attribute} operation="create">
                        <name>{ipsec_policy_name}</name>
                        <description>{description}</description>
                        <protocol>{selected_protocol}</protocol>
                        <encryption-algorithm>{encryption_algorithm}</encryption-algorithm>
                        {'<authentication-algorithm>' + auth_algorithm + '</authentication-algorithm>' if auth_algorithm else ''}
                        <lifetime-kilobytes>{ipsec_lifetime}</lifetime-kilobytes>
                    </proposal>
                </ipsec>
            </security>
        </configuration>""".strip()
    return payload

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
    used_proposals = kwargs.get("used_ipsec_proposals", [])
    if not ipsec_proposal:
        print("No IPsec proposal provided.")
        return None, None
    selected_proposal = select_policy_to_update(ipsec_proposal)
    if not selected_proposal:
        print("No policy selected or invalid selection. Exiting update process.")
        return None, None
    old_proposals = [prop['name'] for prop in ipsec_proposal]
    old_ipsec_name = selected_proposal['name']
    initial_encryption_algo = selected_proposal.get('encryption-algorithm', '')
    continue_update = True
    while continue_update:
        policy_attributes = {key: val for key, val in selected_proposal.items() if key in ['name', 'description', 'protocol', 'encryption-algorithm', 'authentication-algorithm', 'lifetime-kilobytes'] and val is not None}
        if 'description' not in policy_attributes or policy_attributes['description'] is None:
            print("Proposal is missing the description parameter")
            selected_proposal['description'] = get_valid_string("Enter description: ")
        if 'lifetime-kilobytes' not in policy_attributes or policy_attributes['lifetime-kilobytes'] is None:
            selected_proposal['lifetime-kilobytes'] = 86400  
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items()]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        selected_key, new_value = selected_attribute.split(': ', 1)
        selected_key = selected_key.strip()
        if selected_key == 'encryption-algorithm':
            new_value = get_valid_selection("Select encryption algorithm: ", select_enc_algo)
            handle_encryption_update(selected_proposal, initial_encryption_algo, new_value)
        elif selected_key == 'authentication-algorithm' and 'gcm' in selected_proposal.get('encryption-algorithm', '').lower():
            print("Authentication Algorithm cannot be updated, GCM is selected in the Encryption Algorithm")
        elif selected_key == 'name' and selected_proposal[selected_key] in used_proposals:
            print(f"{selected_proposal[selected_key]} is in use by IPsec Policy and cannot be updated.")
        else:
            selected_proposal[selected_key] = get_value_for_key(selected_key)
        if input("Would you like to make another change? (yes/no): ").strip().lower() != 'yes':
            continue_update = False
    insert_attribute = determine_insert_attribute(old_proposals, old_ipsec_name)
    payload = build_ipsec_payload(selected_proposal, insert_attribute)
    return (payload, old_ipsec_name) if old_ipsec_name != selected_proposal['name'] else (payload, None)

def get_value_for_key(key):
    if key == 'lifetime-kilobytes':
        value = input("Enter lifetime in kilobytes or press Enter for default (86400): ").strip()
        return value if value.isdigit() else "86400"
    if key == 'description':
        return get_valid_string("Enter new description: ")
    if key == 'protocol':
        return ipsec_selection("Select IPsec Encapsulation Protocol: ", ["esp", "ah"])
    return get_valid_name(f"Enter the new value for {key}: ")


def determine_insert_attribute(old_proposals, old_ipsec_name):
    last_index = old_proposals.index(old_ipsec_name)
    if last_index == len(old_proposals) - 1 and len(old_proposals) > 1:
        return f'insert="after" key="[ name=\'{old_proposals[-2]}\' ]"'
    elif last_index != len(old_proposals) - 1:
        return f'insert="after" key="[ name=\'{old_proposals[last_index + 1]}\' ]"'
    return ""

def handle_encryption_update(proposal, initial_algo, new_value):
    proposal['encryption-algorithm'] = new_value
    if 'gcm' in new_value and proposal.get('authentication-algorithm'):
        print("Deleting 'authentication-algorithm' due to GCM selection.")
        proposal['authentication-algorithm'] = None
    elif 'gcm' not in new_value and 'gcm' in initial_algo:
        print("GCM no longer used. Please select a new authentication algorithm.")
        proposal['authentication-algorithm'] = get_valid_selection("Select authentication algorithm: ", select_auth_algo)

def build_ipsec_payload(proposal, insert_attribute):
    """Builds the XML configuration payload."""
    authentication_xml = ('<authentication-algorithm operation="delete"/>' if proposal.get('authentication-algorithm') is None
                          else f'<authentication-algorithm>{proposal["authentication-algorithm"]}</authentication-algorithm>')
    return f"""
    <configuration>
        <security>
            <ipsec>
                <proposal {insert_attribute}>
                    <name>{proposal['name']}</name>
                    <description>{proposal.get('description', '')}</description>
                    <protocol>{proposal.get('protocol', '')}</protocol>
                    <encryption-algorithm>{proposal['encryption-algorithm']}</encryption-algorithm>
                    {authentication_xml}
                    <lifetime-kilobytes>{proposal.get('lifetime-kilobytes', '')}</lifetime-kilobytes>
                </proposal>
            </ipsec>
        </security>
    </configuration>""".strip()

def del_ipsec_proposal(**kwargs):
    try:
        ipsec_proposal_name = kwargs.get("ipsec_proposal_name")
        if not ipsec_proposal_name:
            raise ValueError("No IPsec proposal provided for deletion.")
        used_ipsec_proposal = kwargs.get("used_ipsec_proposals", [])
        if not isinstance(used_ipsec_proposal, list):
            used_ipsec_proposal = [used_ipsec_proposal]
        if not isinstance(ipsec_proposal_name, list):
            del_proposal_name = [ipsec_proposal_name]
        else:
            del_proposal_name = get_valid_selection("Select proposal to delete: ", ipsec_proposal_name)
        if not del_proposal_name:
            raise ValueError("Invalid selection or no selection made.")
        if used_ipsec_proposal and del_proposal_name in used_ipsec_proposal:
            raise ReferenceError(f"{del_proposal_name} is referenced in an IPsec Policy and cannot be deleted.")
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

