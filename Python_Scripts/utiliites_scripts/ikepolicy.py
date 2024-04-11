from utiliites_scripts.commons import (get_valid_name, get_valid_string, get_valid_integer,
                                    get_valid_selection, get_valid_passwd)


def gen_ikepolicy_config(**kwargs):
    old_ike_policy = kwargs.get('old_ike_policy',None)
    ike_proposal_names = kwargs.get('ike_proposal',None)
    ike_policy_name = get_valid_name("Enter new IKE policy name: ")
    description = get_valid_string("Enter IKE Policy description: ", max_words=10)
    mode = prompt_for_ike_policy_mode()
    passwd = get_valid_passwd("Enter Valid Password: ")
    if old_ike_policy:
        last_policy_name = old_ike_policy[-1] 
        insert_attribute = f'insert="after" key="[ name=\'{last_policy_name}\' ]"'
    else:
        insert_attribute = ""
        print("No existing IKE policies found. Creating the first policy.")
    ike_proposal_name = get_valid_selection("Select an IKE Proposal: ", ike_proposal_names)
    payload = f"""
    <configuration>
        <security>
            <ike>
                <policy {insert_attribute} operation="create">
                    <name>{ike_policy_name}</name>
                    <description>{description}</description>
                    <mode>{mode}</mode>
                    <proposals>{ike_proposal_name}</proposals>
                    <pre-shared-key>
                        <ascii-text>{passwd}</ascii-text>
                    </pre-shared-key>
                </policy>
            </ike>
        </security>
    </configuration>""".strip()
    print(payload)
    return payload


def prompt_for_ike_policy_mode():
    while True:
        mode = get_valid_name("Select IKE Policy mode: ")
        if mode.lower() in ["main", "aggressive"]:
            return mode
        print("Invalid mode selected. Please choose either 'main' or 'aggressive'.")


def extract_proposals(ike_policy):
    ike_policy = [ike_policy] if isinstance(ike_policy, dict) else ike_policy
    return [policy['proposals'] for policy in ike_policy if 'proposals' in policy]

def select_policy_to_update(ike_policies):
    print("Select a policy to update:")
    for i, policy in enumerate(ike_policies, start=1):
        print(f"{i}. {policy['name']}")
    selection = input("Enter the number of the policy: ")
    if selection.isdigit() and 1 <= int(selection) <= len(ike_policies):
        return ike_policies[int(selection) - 1]
    else:
        print("Invalid selection.")
        return None

def update_ike_policy(**kwargs):
    ike_policies = kwargs.get('ike_configs')
    proposals = kwargs.get('proposal_names')
    selected_policy = select_policy_to_update(ike_policies)
    if not selected_policy:
        print("No policy selected or invalid selection. Exiting update process.")
        return
    policy_attributes = {
        'name': selected_policy.get('name'),
        'mode': selected_policy.get('mode'),
        'description': selected_policy.get('description'),
        'proposals': selected_policy.get('proposals'),
        'pre-shared-key': selected_policy.get('pre-shared-key', {}).get('ascii-text')
    }
    attribute_keys = [f"{key}: {value}" for key, value in policy_attributes.items() if value is not None]
    selected_attribute_description = get_valid_selection("Select an attribute to update", attribute_keys)
    selected_key = selected_attribute_description.split(':')[0]
    if selected_key == 'pre-shared-key':
        selected_policy[selected_key] = {'ascii-text': new_value}
    elif selected_key == 'proposals':
        selected_policy[selected_key] = get_valid_selection("Select proposal to update: ", proposals)
    elif selected_key == 'mode':
        mode_choice = ["main","aggressive"] 
        selected_policy[selected_key] = get_valid_selection("Select proposal to update: ", mode_choice)
    elif selected_key == "name":
        old_policy_name = selected_key['name']
        new_value = get_valid_name(f"Enter the new value for {selected_key}: ")   
        selected_policy[selected_key] = new_value
    elif selected_key == "description":
        new_value = get_valid_string(f"Enter the new value for {selected_key}: ")   
        selected_policy[selected_key] = new_value       
    if selected_key != 'name':
        payload = f"""
        <configuration junos:commit-seconds="1712734023" junos:commit-localtime="2024-04-10 07:27:03 UTC" junos:commit-user="root">
                <security>
                    <ike>
                        <policy>
                            <name>{new_value}</name>
                            <mode>{policy_attributes['mode']}</mode>
                            <proposals>{policy_attributes['proposals']}</proposals>
                            <pre-shared-key>
                                <ascii-text>{policy_attributes['pre-shared-key']['ascii-text']}</ascii-text>
                            </pre-shared-key>
                        </policy>
                    </ike>
                </security>
        </configuration>""".strip()
    else:
        payload = f"""
        <configuration>
                <security>
                    <ike>
                      <policy>
                        <name>{selected_policy['name']}</name>
                        <mode>{selected_policy['mode']}</mode>
                        <proposals>{selected_policy['proposals']}</proposals>
                        <pre-shared-key>
                            <ascii-text>{selected_policy['pre-shared-key']['ascii-text']}</ascii-text>
                        </pre-shared-key>
                    </policy>
                    </ike>
                </security>
        </configuration>""".strip()
    return payload, old_policy_name if old_policy_name else payload, None


def delete_ike_policy(**kwargs):
    try:
        policy_names = kwargs.get("policy_name")
        if not policy_names:
            raise ValueError("No policy names provided for deletion.")
        used_policy = kwargs.get("used_policy", [])
        if isinstance(used_policy, list):
            used_policy = [used_policy]
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
                        <ike>
                            <policy operation="delete">
                                <name>{del_policy_name}</name>
                            </policy>
                        </ike>
                    </security>
            </configuration>""".strip()
        return payload
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return None
