
from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ikepolicy import gen_ikepolicy_config, extract_proposals
from securityikeproOper import IkeProposalManager
ike_proposal =  IkeProposalManager()

script_dir = os.path.dirname(os.path.realpath(__file__))

class IkePolicyManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def ike_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Ike Policy")
            print("2. Create Ike Policy")
            print("3. Update Ike Policy")
            print("4. Delete Ike Policy")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                response = self.get_ike_policy(interactive=True)
            elif operation == "2":
                response = self.create_ike_policy()
                return response
            elif operation == "3":
                response = self.update_ike_policy()
                return response
            elif operation == "4":
                response =  self.delete_ike_policy()
                return response
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ike_policy(self, interactive=False, get_raw_data=False, retries=3, get_proposals=False):
        attempt = 0
        ike_policy_names = []
        get_used_proposals = None  
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    for _, result in response.items():
                        ike_config = result.result['configuration']['security'].get('ike', {})
                        if ike_config:
                            ike_policy = ike_config.get('policy', [])
                            ike_policy = [ike_policy] if isinstance(ike_policy, dict) else ike_policy
                            ike_policy_names = [policy['name'] for policy in ike_policy if 'name' in policy]
                            if get_proposals:
                                get_used_proposals = extract_proposals(ike_policy)
                        else:
                            print("No IKE configuration found on the device.")
                            break
                    if interactive and ike_policy_names:
                        print(ike_policy_names)
                    if get_proposals and get_used_proposals:
                        return get_used_proposals
                    if get_raw_data and ike_config:
                        return ike_config, ike_policy_names
                    return ike_policy_names or None
            except Exception as e:
                print(f"An error has occurred: {e}. Trying again...")
            attempt += 1
        print("Failed to retrieve IKE policies after several attempts.")
        return None

    
    def create_ike_policy(self):
        old_ike_policy = self.get_ike_policy()
        ike_proposal_names = ike_proposal.get_ike_proposals()
        if not old_ike_policy:
            print("No existing IKE Proposal found on the device")
        payload = gen_ikepolicy_config(old_ike_policy, ike_proposal_names)
        return payload

    # def update_ike_policy(self):
    #     try:
    #         ike_configs, ike_proposal_names = self.get_proposals(get_raw_data=True)
    #         if ike_configs:
    #             updated_proposal = extract_and_update_proposal(ike_configs)
    #             payload = gen_ikeproposal_xml(updated_proposal, ike_proposal_names)
    #             return payload
    #         else:
    #             print("No existing IKE Proposal exist on the device")
    #     except ValueError as e:
    #         print(f"An error has occured, {e}")

    
    # def delete_ike_policy(self):
    #     *_, ike_proposal_names = self.get_proposals(get_raw_data=True)
    #     payload = delete_ike_proposal(ike_proposal_names)
    #     return payload

    def push_config(self):
        xml_data = self.ike_operations()
        print(xml_data)
        if not xml_data:
            return 
        elif isinstance(xml_data, list):
            for xml in xml_data:
                run_pyez_tasks(self, xml, 'xml') 
            return None
        else:
             run_pyez_tasks(self, xml_data, 'xml') 

if __name__ == "__main__":
    config = IkePolicyManager()
    response = config.push_config()