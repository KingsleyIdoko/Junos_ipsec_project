from utiliites_scripts.commons import (get_valid_name, get_valid_string,get_valid_selection)
pfs_groups = ['group1','group14','group19','group2','group20','group24','group5']
def gen_ipsecpolicy_config(**kwargs):
    old_ipsec_policy = kwargs.get('old_ipsec_policy',None)
    ipsec_proposal_names = kwargs.get('ipsec_proposals',None)
    if old_ipsec_policy:
        print(f"There are {len(old_ipsec_policy)} existing IKE Policy on the device")
        for i, choice in enumerate(old_ipsec_policy, start=1):
            print(f"{i}. {choice}")
    ipsec_policy_name = get_valid_name("Enter new IKE policy name: ")
    description = get_valid_string("Enter IKE Policy description: ", max_words=20)
    pfs = get_valid_selection("Enter perfect-forward-secrecy group : ",pfs_groups)
    proposal = get_valid_selection("Select IPsec Proposal to attach : ",ipsec_proposal_names)
    if old_ipsec_policy and len(old_ipsec_policy) > 1:
        last_policy_name = old_ipsec_policy[-1] 
        insert_attribute = f'insert="after" key="[ name=\'{last_policy_name}\' ]" operation="create"'
    else:
        insert_attribute = 'operation="create"'
        print("No existing IKE policies found. Creating the first policy.")
    payload = f"""
    <configuration>
            <security>
                <ipsec>
                    <policy {insert_attribute}>
                        <name>{ipsec_policy_name}</name>
                        <description>{description}</description>
                        <perfect-forward-secrecy>
                            <keys>{pfs}</keys>
                        </perfect-forward-secrecy>
                        <proposals>{proposal}</proposals>
                    </policy>
                </ipsec>
            </security>
    </configuration>""".strip()
    return payload

def extract_proposals(ike_policy):
    ike_policy = [ike_policy] if isinstance(ike_policy, dict) else ike_policy
    return [policy['proposals'] for policy in ike_policy if 'proposals' in policy]

def select_policy_to_update(ipsec_policies):
    print("Select a policy to update:")
    if not isinstance(ipsec_policies, list):
        ipsec_policies = [ipsec_policies]
    for i, policy in enumerate(ipsec_policies, start=1):
        print(f"{i}. {policy['name']}")
    selection = input("Enter the number of the policy: ")
    if selection.isdigit() and 1 <= int(selection) <= len(ipsec_policies):
        return ipsec_policies[int(selection) - 1]
    else:
        print("Invalid selection.")
        return None

def update_ipsec_policy(**kwargs):
    ipsec_policies = kwargs.get('ipsec_configs')
    ipsec_proposal_names = kwargs.get('ipsec_proposals', [])
    if not ipsec_policies:
        print("No IPsec configurations provided. Exiting.")
        return None, None
    selected_policy = select_policy_to_update(ipsec_policies)
    if not selected_policy:
        print("No policy selected or invalid selection. Exiting update process.")
        return None, None
    old_proposal = selected_policy['proposals']
    old_policy_name = selected_policy['name']
    new_proposal = None
    update_proposal = None
    continue_update = True
    while continue_update:
        policy_attributes = {
            'name': selected_policy.get('name'),
            'description': selected_policy.get('description'),
            'pfs': selected_policy.get('perfect-forward-secrecy', {}).get('keys'),
            'proposals': selected_policy.get('proposals'),
        }
        attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
        selected_attribute = get_valid_selection("Select an attribute to update", attribute_keys)
        selected_key = selected_attribute.split(':')[0].strip()
        new_value = handle_policy_update(selected_policy, selected_key, ipsec_proposal_names)
        if selected_key == 'proposals':
            new_proposal = new_value
        continue_update = input("Would you like to make another change? (yes/no): ").strip().lower() == 'yes'
        insert_attribute = 'operation="create"' if old_policy_name != selected_policy['name'] else ""
    payload = create_payload(selected_policy, old_proposal, new_proposal, insert_attribute=insert_attribute)
    return (payload, old_policy_name) if old_policy_name != selected_policy['name'] else (payload, None)

def handle_policy_update(policy, key, proposals_names):
    if key == 'pfs':
        policy[key] = get_valid_selection("Enter perfect-forward-secrecy group : ", pfs_groups)
        return policy[key]
    elif key == 'description':
        policy[key] = get_valid_string("Enter new description: ")
        return policy[key]
    elif key == 'proposals':
        policy[key] = get_valid_selection("Enter new proposal: ", proposals_names)
        return policy[key]
    else:
        policy[key] = get_valid_name(f"Enter the new value for {key}: ")
        return policy[key]

def create_payload(policy, old_proposal, new_proposal, insert_attribute=None):
    update_proposal = f"""
        <proposals>{new_proposal}</proposals>
        <proposals operation="delete">{old_proposal}</proposals>""" if new_proposal else f'<proposals>{old_proposal}</proposals>'
    if not insert_attribute:
        pfs_var = f"""
                <keys operation="delete"/>
                <keys operation="create">{policy['perfect-forward-secrecy'].get('keys')}</keys>"""
    else: 
        pfs_var = f"""<keys>{policy['perfect-forward-secrecy'].get('keys')}</keys>"""
    return f"""
    <configuration>
        <security>
            <ipsec>
                <policy {insert_attribute}>
                    <name>{policy['name']}</name>
                    <description>{policy['description']}</description>
                    <perfect-forward-secrecy>
                        {pfs_var}
                    </perfect-forward-secrecy>
                    {update_proposal}
                </policy>
            </ipsec>
        </security>
    </configuration>""".strip()



def del_ipsec_policy(**kwargs):
    try:
        policy_names = kwargs.get("policy_name")
        if not policy_names:
            raise ValueError("No policy names provided for deletion.")
        used_policy = kwargs.get("used_policy", [])
        if isinstance(used_policy, list):
            used_policy = [used_policy]
        if not isinstance(policy_names, list):
            del_policy_name = policy_names
        else:
            del_policy_name = get_valid_selection("Select Policy to delete: ", policy_names)
        if not del_policy_name:
            raise ValueError("Invalid selection or no selection made.")
        if used_policy != None:
            if del_policy_name in used_policy:
                message = f"{del_policy_name} is referenced in an IKE Gateway and cannot be deleted."
                raise ReferenceError(message)
        payload = f"""
            <configuration>
                    <security>
                        <ipsec>
                            <policy operation="delete">
                                <name>{del_policy_name}</name>
                            </policy>
                        </ipsec>
                    </security>
            </configuration>""".strip()
        return payload
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
