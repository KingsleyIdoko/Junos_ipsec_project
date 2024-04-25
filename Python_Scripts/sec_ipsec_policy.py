
from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ipsec_policy import (gen_ipsecpolicy_config, update_ipsec_policy,
                                         del_ipsec_policy)
from sec_ipsec_proposal import IPsecProposalManager
proposal_manager = IPsecProposalManager()

script_dir = os.path.dirname(os.path.realpath(__file__))

class IpsecPolicyManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)
  
    def ipsec_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get Ipsec policy")
            print("2. create Ipsec policy")
            print("3. update Ipsec policy")
            print("4. delete Ipsec policy")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_ipsec_policy(interactive=True)
            elif operation == "2":
                return self.create_ipsec_policy()
            elif operation == "3":
                return self.update_ipsec_policy()
            elif operation == "4":
                return self.delete_ipsec_policy()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ipsec_policy(self, interactive=False, get_proposal_name=False, get_raw_data=False, retries=3, get_policy_name=False):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    for _, result in response.items():
                        ipsec_config = result.result['configuration']['security'].get('ipsec', {})
                        if ipsec_config:
                            raw_ipsec_policy = ipsec_config.get('policy', [])
                            ipsec_policy = [raw_ipsec_policy] if isinstance(raw_ipsec_policy, dict) else raw_ipsec_policy
                            ipsec_policy_names = [policy['name'] for policy in ipsec_policy if 'name' in policy]
                            used_proposals = [prop['proposals'] for prop in ipsec_policy]
                        else:
                            print("No IKE configuration found on the device.")
                            break
                    if interactive:
                        print("No existing IKE Policy on the device" if raw_ipsec_policy in ([], None) else raw_ipsec_policy)
                        return None
                    if get_policy_name:
                        return ipsec_policy_names
                    if get_proposal_name:
                        return used_proposals
                    if get_raw_data and raw_ipsec_policy:
                        return raw_ipsec_policy, ipsec_policy_names or None
            except Exception as e:
                print(f"An error has occurred: {e}. Trying again...")
            attempt += 1
        print("Failed to retrieve IKE policies after several attempts.")
        return None

    def create_ipsec_policy(self):
        old_ipsec_policy = self.get_ipsec_policy(get_policy_name=True)
        ipsec_proposals  = proposal_manager.get_ipsec_proposal()
        if not old_ipsec_policy:
            print("No existing IKE Policy found on the device")
        payload = gen_ipsecpolicy_config(old_ipsec_policy=old_ipsec_policy, ipsec_proposals=ipsec_proposals)
        return payload

    def update_ipsec_policy(self):
        try:
            ipsec_configs, proposal_names = self.get_ipsec_policy(get_raw_data=True)
            payload, del_policy = update_ipsec_policy(ipsec_configs=ipsec_configs, proposal_names=proposal_names)
            if del_policy:
                self.delete_ipsec_policy(commit=True, policy_name=del_policy)
            return payload
        except ValueError as e:
            print(f"An error has occured, {e}")
        
    def delete_ipsec_policy(self, commit=False, policy_name=None):
        if not commit:
            policy_name = self.get_ipsec_policy(get_policy_name=True)
            used_policy = None
            payload = del_ipsec_policy(policy_name=policy_name,used_policy=used_policy)
            return payload
        else:
            policy_name=policy_name
            used_policy = None
            payload = del_ipsec_policy(policy_name=policy_name,used_policy=used_policy)
            run_pyez_tasks(self, payload, 'xml')

    def push_config(self):
        try:
            xml_data = self.ipsec_operations()
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
    config = IpsecPolicyManager()
    response = config.push_config()