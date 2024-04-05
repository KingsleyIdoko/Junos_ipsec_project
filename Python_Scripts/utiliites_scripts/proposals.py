from utiliites_scripts.commons import get_valid_string, get_valid_integer
encrypt = ['3des-cbc', 'aes-128-cbc', 'aes-128-gcm', 'aes-192-cbc', 'aes-256-cbc', 'aes-256-gcm', 'des-cbc']
dh_group = ['group1', 'group14', 'group19', 'group2', 'group20', 'group24', 'group5']
auth_meth = ['dsa-signatures', 'ecdsa-signatures-256', 'ecdsa-signatures-384', 'pre-shared-keys', 'rsa-signatures']
auth_algo = ['md5', 'sha-256', 'sha-384', 'sha1']

def gen_ikeprop_config(old_proposal, encrypt=encrypt,dh_group=dh_group, auth_meth=auth_meth,auth_algo=auth_algo):
    while True:
        if old_proposal:
            print(f"{len(old_proposal)} proposals already exist on the device.")
            ikeproposal_name = get_valid_string("Enter Ike Proposal Name: ")
            if old_proposal == ikeproposal_name:
                print("Ike Proposal already exist:")
                continue
        ikeproposal_desc = get_valid_string("Enter Ike Proposal Description: ")
        print("Select Encryption Algorithm: ")
        for i, alg in enumerate(encrypt, 1):
            print(f"{i}. {alg}")
        encrypt_algorithm = encrypt[get_valid_integer("Enter choice: ") - 1]
        print("Select DH Group:")
        for i, group in enumerate(dh_group, 1):
            print(f"{i}. {group}")
        dhgroup = dh_group[get_valid_integer("Enter choice: ") - 1]
        print("Select Authentication Method")
        for i, method in enumerate(auth_meth, 1):
            print(f"{i}. {method}")
        auth_method = auth_meth[get_valid_integer("Enter choice: ") - 1]
        print("Select Authentication Algorithms")
        for i, alg in enumerate(auth_algo, 1):
            print(f"{i}. {alg}")
        auth_algorithm = auth_algo[get_valid_integer("Enter choice: ") - 1]
        ike_lifetime = get_valid_integer("Enter Ike Security Association lifetime (180..86400 seconds): ")
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



def extract_and_update_proposal(ike_config):
    # Normalize proposals to always be a list
    proposals = ike_config['proposal']
    if isinstance(proposals, dict):
        proposals = [proposals]
    
    # Extract proposal names and display them for user selection
    proposal_names = [proposal['name'] for proposal in proposals]
    for i, name in enumerate(proposal_names, start=1):
        print(f"{i}. {name}")
    
    selected_index = get_valid_integer("Select a proposal to update (by number): ") - 1
    selected_proposal = proposals[selected_index]
    
    print("Selected Proposal:", selected_proposal['name'])
    # Display keys for the selected proposal
    proposal_keys = list(selected_proposal.keys())
    for i, key in enumerate(proposal_keys, start=1):
        print(f"{i}. {key}")
    
    key_index = get_valid_integer("Select a key to update (by number): ") - 1
    selected_key = proposal_keys[key_index]
    
    # Get the new value for the selected key
    new_value = get_valid_string(f"Enter new value for {selected_key}: ")
    
    # Update the selected key with the new value
    selected_proposal[selected_key] = new_value
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