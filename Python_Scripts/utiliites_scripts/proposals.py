from utiliites_scripts.commons import get_valid_string, get_valid_integer, get_valid_choice
encrypt = ['3des-cbc', 'aes-128-cbc', 'aes-128-gcm', 'aes-192-cbc', 'aes-256-cbc', 'aes-256-gcm', 'des-cbc']
dh_group = ['group1', 'group14', 'group19', 'group2', 'group20', 'group24', 'group5']
auth_meth = ['dsa-signatures', 'ecdsa-signatures-256', 'ecdsa-signatures-384', 'pre-shared-keys', 'rsa-signatures']
auth_algo = ['md5', 'sha-256', 'sha-384', 'sha1']


def extract_and_update_proposal(ike_config,used_proposals):
    proposals = ike_config.get('proposal', [])
    proposals = [proposals] if isinstance(proposals, dict) else proposals
    proposal_names = [proposal['name'] for proposal in proposals]
    selected_index = get_valid_choice("Select a proposal to update", proposal_names)
    selected_proposal = proposals[selected_index]
    print("Selected Proposal:", selected_proposal['name'])
    if selected_proposal['name'] in used_proposals:
         print(f"Proposals {selected_proposal['name']} is currently in used by IKE Policy")
         return None
    proposal_keys = list(selected_proposal.keys())
    key_index = get_valid_choice("Select a key to update", proposal_keys)
    selected_key = proposal_keys[key_index]
    new_value = get_valid_string(f"Enter new value for {selected_key}: ")
    selected_proposal[selected_key] = new_value
    print("Updated Proposal:", selected_proposal['name'], "->", selected_key, "=", new_value)
    return selected_proposal


def gen_ikeproposal_xml(updated_proposal, old_proposal):
    if old_proposal:
                last_old_proposal = old_proposal[-1]  
                ike_opening_tag = "<ike>"
                proposal_attributes = f'insert="after" key="[ name=\'{last_old_proposal}\' ]" operation="create"'
    else:
        ike_opening_tag = '<ike operation="create">'
        proposal_attributes = ""
    ike_proposal_xml = f"""
        <configuration>
            <security>
                {ike_opening_tag}
                    <proposal {proposal_attributes}>
                        <name>{updated_proposal['name']}</name>
                        <description>{updated_proposal['description']}</description>
                        <authentication-method>{updated_proposal['authentication-method']}</authentication-method>
                        <dh-group>{updated_proposal['dh-group']}</dh-group>
                        <authentication-algorithm>{updated_proposal['authentication-algorithm']}</authentication-algorithm>
                        <encryption-algorithm>{updated_proposal['encryption-algorithm']}</encryption-algorithm>
                        <lifetime-seconds>{updated_proposal['lifetime-seconds']}</lifetime-seconds>
                    </proposal>
                </ike>
            </security>
        </configuration>""".strip()
    print("Generated IKE Proposal Configuration:")
    return ike_proposal_xml


def delete_ike_proposal(ike_proposal_names):
    if not ike_proposal_names:
        print("No proposals to delete.")
        return None
    choice_index = get_valid_choice("Enter proposal number to delete", ike_proposal_names)
    proposal_name_to_delete = ike_proposal_names[choice_index]
    payload = f"""
    <configuration>
        <security>
            <ike>
                <proposal operation="delete">
                    <name>{proposal_name_to_delete}</name>
                </proposal>
            </ike>
        </security>
    </configuration>""".strip()
    
    print(f"Proposal to delete: {proposal_name_to_delete}")
    return payload


def gen_ikeprop_config(old_proposal_names, encrypt=encrypt,dh_group=dh_group, auth_meth=auth_meth,auth_algo=auth_algo):
    if old_proposal_names:
        print(f"{len(old_proposal_names)} proposals already exist on the device.")
    
    while True:
        ikeproposal_name = get_valid_string("Enter Ike Proposal Name: ")
        if ikeproposal_name in old_proposal_names:
            print("Ike Proposal already exists, please enter a different name.")
            continue
        break
    ikeproposal_desc = get_valid_string("Enter Ike Proposal Description: ")
    encrypt_algorithm = get_valid_choice("Select Encryption Algorithm: ", encrypt)
    dhgroup = get_valid_choice("Select DH Group: ", dh_group)
    auth_method = get_valid_choice("Select Authentication Method: ", auth_meth)
    auth_algorithm = get_valid_choice("Select Authentication Algorithms: ", auth_algo)
    ike_lifetime = get_valid_integer("Enter Ike Security Association lifetime (180..86400 seconds): ")
    ike_lifetime = max(180, min(ike_lifetime, 86400))
    if old_proposal_names:
            last_old_proposal = old_proposal_names[-1]  
            ike_opening_tag = "<ike>"
            proposal_attributes = f'insert="after" key="[ name=\'{last_old_proposal}\' ]" operation="create"'
    else:
        ike_opening_tag = '<ike operation="create">'
        proposal_attributes = ""
    ike_proposal_xml = f"""
        <configuration>
            <security>
                {ike_opening_tag}
                    <proposal {proposal_attributes}>
                        <name>{ikeproposal_name}</name>
                        <description>{ikeproposal_desc}</description>
                        <authentication-method>{auth_method}</authentication-method>
                        <dh-group>{dhgroup}</dh-group>
                        <authentication-algorithm>{auth_algorithm}</authentication-algorithm>
                        <encryption-algorithm>{encrypt_algorithm}</encryption-algorithm>
                        <lifetime-seconds>{ike_lifetime}</lifetime-seconds>
                    </proposal>
                </ike>
            </security>
        </configuration>""".strip()
    print("Generated IKE Proposal Configuration:")
    print(ike_proposal_xml)
    return ike_proposal_xml