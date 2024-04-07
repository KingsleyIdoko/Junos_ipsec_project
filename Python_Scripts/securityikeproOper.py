
from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.proposals import (gen_ikeprop_config, extract_and_update_proposal, 
                                         gen_ikeproposal_xml, delete_ike_proposal)
script_dir = os.path.dirname(os.path.realpath(__file__))

class IkeProposalManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def ike_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Ike Proposals")
            print("2. Create Ike Proposal")
            print("3. Update Ike Proposal")
            print("4. Delete Ike Proposal")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                response = self.get_ike_proposals(interactive=True)
            elif operation == "2":
                return self.create_proposal()
            elif operation == "3":
                return self.update_proposal()
            elif operation == "4":
                return  self.delete_proposal()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ike_proposals(self, interactive=False, get_raw_data=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    for _, result in response.items():
                        ike_config = result.result['configuration']['security'].get('ike')
                        if ike_config:
                            proposals = ike_config.get('proposal',[])
                            proposals = [proposals] if isinstance(proposals, dict) else proposals
                            ike_proposal_names = [proposal['name'] for proposal in proposals if 'name' in proposal]
                            if not isinstance(ike_proposal_names, list):  
                                ike_proposal_names = [ike_proposal_names]
                        else:
                            print("No Security ike implementation exist on the device")
                            break
                    if interactive:
                        print(proposals)
                        return
                    if get_raw_data:
                        return ike_config, ike_proposal_names if ike_config else None
                    return ike_proposal_names if ike_proposal_names else None
            except Exception as e:
                print(f"An error has occurred: {e}. Checking connectivity to the device, trying again...")
            attempt += 1
        print("Failed to retrieve proposals after several attempts.")
        return None

    
    def create_proposal(self):
        old_proposals = self.get_ike_proposals()
        if not old_proposals:
            print("No existing IKE Proposal found on the device")
        payload = gen_ikeprop_config(old_proposals)
        print(payload)
        return payload

    def update_proposal(self):
        payload = []
        from securityikepolicy import IkePolicyManager
        policy_manager = IkePolicyManager()
        
        try:
            ike_configs, ike_proposal_names = self.get_ike_proposals(get_raw_data=True)
            if ike_configs:
                used_proposals = list(set(policy_manager.get_ike_policy(get_proposals=True)))
                try:
                    new_updated_proposal, del_old_proposal = extract_and_update_proposal(ike_configs, used_proposals)
                    
                    if del_old_proposal in used_proposals:
                        print(f"Proposal {del_old_proposal} is in use by IKE Policy and cannot be updated.")
                        return None
                    new_payload = gen_ikeproposal_xml(new_updated_proposal, ike_proposal_names)
                    payload.append(new_payload)
                    del_payload = self.delete_proposal(ike_prop_name=del_old_proposal, direct_del=True)
                    payload.append(del_payload)
                    
                    return payload
                except Exception as e:  
                    print(f"An error occurred while updating the proposal: {e}")
                    return None
            else:
                print("No existing IKE Proposals exist on the device.")
        except ValueError as e:
            print(f"An error has occurred: {e}")

    def delete_proposal(self, direct_del=False, ike_prop_name=None, commit=False):
        from securityikepolicy import IkePolicyManager
        policy_manager = IkePolicyManager()
        used_proposals = list(set(policy_manager.get_ike_policy(get_proposals=True)))
        if not direct_del:
            used_proposals = list(set(policy_manager.get_ike_policy(get_proposals=True)))
            if not ike_prop_name:
                ike_prop_name = self.get_ike_proposals(get_raw_data=True)[-1]
        payload = delete_ike_proposal(ike_prop_name, used_proposals, direct_del)
        if commit and payload != None:
            return run_pyez_tasks(self, payload, 'xml')
        return payload

    def push_config(self):
        xml_data = self.ike_operations()
        if not xml_data:
            return 
        elif isinstance(xml_data, list):
            for xml in xml_data:
                run_pyez_tasks(self, xml, 'xml') 
            return
        else:
             run_pyez_tasks(self, xml_data, 'xml') 
if __name__ == "__main__":
    config = IkeProposalManager()
    response = config.push_config()