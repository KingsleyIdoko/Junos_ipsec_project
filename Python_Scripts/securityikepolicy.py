
from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ikepolicy import (gen_ikepolicy_config, update_ike_policy,
                                         delete_ike_policy)
from securityikeproOper import IkeProposalManager


script_dir = os.path.dirname(os.path.realpath(__file__))

class IkePolicyManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)
        self.ike_proposal =  IkeProposalManager()

    def ike_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get ike policy")
            print("2. create ike policy")
            print("3. update ike policy")
            print("4. delete ike policy")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_ike_policy(interactive=True)
            elif operation == "2":
                response = self.create_ike_policy()
                return response
            elif operation == "3":
                response = self.update_ike_policy()
                print(response)
            elif operation == "4":
                response =  self.delete_ike_policy()
                return response
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ike_policy(self, interactive=False, get_raw_data=False, retries=3, get_policy_name=False):
        attempt = 0
        ike_policy_names = []
        get_used_proposals = None  
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    for _, result in response.items():
                        ike_config = result.result['configuration']['security'].get('ike', {})
                        proposals = ike_config.get('proposal', [])
                        ike_proposal_names = [proposal['name'] for proposal in proposals if 'name' in proposal]
                        if ike_config:
                            raw_ike_policy = ike_config.get('policy', [])
                            ike_policy = [raw_ike_policy] if isinstance(raw_ike_policy, dict) else raw_ike_policy
                            ike_policy_names = [policy['name'] for policy in ike_policy if 'name' in policy]
                        else:
                            print("No IKE configuration found on the device.")
                            break
                    if interactive:
                        print("No existing IKE Policy on the device" if raw_ike_policy in ([], None) else raw_ike_policy)
                        return None
                    if get_policy_name:
                        return ike_policy_names
                    if get_raw_data and raw_ike_policy:
                        return raw_ike_policy, ike_proposal_names or None
            except Exception as e:
                print(f"An error has occurred: {e}. Trying again...")
            attempt += 1
        print("Failed to retrieve IKE policies after several attempts.")
        return None

    
    def create_ike_policy(self):
        old_ike_policy = self.get_ike_policy()
        ike_proposal = self.ike_proposal.get_ike_proposals()
        if not ike_proposal:
            print("No existing IKE Proposal found on the device")
            return None
        payload = gen_ikepolicy_config(old_ike_policy=old_ike_policy, ike_proposal=ike_proposal)
        print(payload)
        return payload

    def update_ike_policy(self):
        try:
            ike_configs, proposal_names = self.get_ike_policy(get_raw_data=True)
            payload, del_policy = update_ike_policy(ike_configs=ike_configs, proposal_names=proposal_names)
            print(payload)
            print(del_policy)
        except ValueError as e:
            print(f"An error has occured, {e}")
        
    def delete_ike_policy(self):
        policy_name = self.get_ike_policy(get_policy_name=True)
        used_policy = None
        payload = delete_ike_policy(policy_name=policy_name,used_policy=used_policy)
        return payload

    def push_config(self):
        try:
            xml_data = self.ike_operations()
            if not xml_data:
                logging.info("No XML data to push.")
                return
            if isinstance(xml_data, list):
                for xml in xml_data:
                    try:
                        run_pyez_tasks(self, xml, 'xml')
                    except Exception as e:
                        logging.error(f"Failed to push configuration for {xml}: {e}")
            else:
                try:
                    run_pyez_tasks(self, xml_data, 'xml')
                except Exception as e:
                    logging.error(f"Failed to push configuration: {e}")
        except Exception as e:
            logging.error(f"Error in push_config: {e}")

if __name__ == "__main__":
    config = IkePolicyManager()
    response = config.push_config()