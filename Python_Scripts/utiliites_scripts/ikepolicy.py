from utiliites_scripts.commons import get_valid_choice, get_valid_integer, get_valid_string

def gen_ikepolicy_config(old_ike_policy, ike_proposal_names):
    ike_policy_name = get_valid_string("Enter new IKE policy name: ")
    description = get_valid_string("Enter IKE Policy description: ")
    passwd = get_valid_string("Enter pre-shared-key (passwd): ")
    if old_ike_policy:
        last_policy_name = old_ike_policy[-1] 
        insert_attribute = f'insert="after" key="[ name=\'{last_policy_name}\' ]"'
    else:
        insert_attribute = ""
        print("No existing IKE policies found. Creating the first policy.")
    ike_proposal_name = get_valid_choice("Select an IKE Proposal: ", ike_proposal_names)
    payload = f"""
    <configuration>
        <security>
            <ike>
                <policy {insert_attribute} operation="create">
                    <name>{ike_policy_name}</name>
                    <description>{description}</description>
                    <proposals>{ike_proposal_name}</proposals>
                    <pre-shared-key>
                        <ascii-text>{passwd}</ascii-text>
                    </pre-shared-key>
                </policy>
            </ike>
        </security>
    </configuration>""".strip()
    return payload


def extract_proposals(ike_policy):
    ike_policy = [ike_policy] if isinstance(ike_policy, dict) else ike_policy
    return [policy['proposals'] for policy in ike_policy if 'proposals' in policy]
