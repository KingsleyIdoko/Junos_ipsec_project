
from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.proposals import (gen_ikeprop_config, extract_and_update_proposal, 
                                         update_ikeproposal_xml, delete_ike_proposal)
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
                return self.get_ike_proposals(interactive=True)
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
                if response.failed:  # Check if the task failed
                    print("Failed to connect to the device, trying again...")
                    attempt += 1
                    continue
                for _, result in response.items():
                    ike_config = result.result['configuration']['security'].get('ike', {})
                    proposals = ike_config.get('proposal', [])
                    proposals = [proposals] if isinstance(proposals, dict) else proposals
                    ike_proposal_names = [proposal['name'] for proposal in proposals if 'name' in proposal]
                if not proposals:  
                    print("No IKE configurations exist on the device.")
                    return None
                if interactive:
                    print(proposals)
                    return
                if get_raw_data:
                    return ike_config, ike_proposal_names
                return ike_proposal_names
            except Exception as e:
                print(f"An error has occurred: {e}. Checking connectivity to the device, trying again...")
                attempt += 1
                continue  
        print("Failed to retrieve proposals after several attempts due to connectivity issues.")
        return None

    def create_proposal(self):
        try:
            old_proposals = self.get_ike_proposals()
            if not old_proposals:
                print("No existing IKE Proposal found on the device")
                old_proposals = []  
            payload = gen_ikeprop_config(old_proposals)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    
    def update_proposal(self):
        from securityikepolicy import IkePolicyManager
        policy_manager = IkePolicyManager()
        try:
            ike_configs, _ = self.get_ike_proposals(get_raw_data=True)
            if ike_configs:
                try:
                    used_proposals = list(set(policy_manager.get_ike_policy(get_proposals=True)))
                except:
                    used_proposals = None
                updated_proposal, insert_after, old_name, desc, changed_key  = extract_and_update_proposal(ike_configs, 
                                                                                                           used_proposals)
                if updated_proposal is None:
                    print("Update aborted: Proposal is currently in use or another issue occurred.")
                    return None
                payload = []
                if old_name and old_name != updated_proposal['name']:
                    print(f"Name change detected: Deleting '{old_name}' and creating '{updated_proposal['name']}' with updated attributes.")
                    del_payload = self.delete_proposal(direct_del=True, ike_prop_name=old_name, commit=False)
                    payload.append(del_payload)
                new_payload = update_ikeproposal_xml(updated_proposal=updated_proposal,old_name=old_name, 
                                                  insert_after=insert_after, changed_key=changed_key)
                print(new_payload)
                payload.append(new_payload)
                print(f"Update successful: {desc}")
                return payload
            else:
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            print("No existing IKE Proposals found on the device.")


    def delete_proposal(self, **kwargs):
        from securityikepolicy import IkePolicyManager
        policy_manager = IkePolicyManager()
        direct_del = kwargs.get('direct_del', False)
        ike_prop_name = kwargs.get('ike_prop_name', None)
        commit = kwargs.get('commit', False)
        key_values = kwargs.get('key_values', None)
        try:
            used_proposals = list(set(policy_manager.get_ike_policy(get_proposals=True)))
        except:
            used_proposals = None
        if not direct_del:
            if used_proposals:
                used_proposals = list(set(policy_manager.get_ike_policy(get_proposals=True)))
            if not ike_prop_name:
                ike_prop_name = self.get_ike_proposals(get_raw_data=True)[-1]
        print(direct_del, ike_prop_name, commit, key_values)
        payload = delete_ike_proposal(ike_proposal_names=ike_prop_name,used_proposals=used_proposals, 
                                    direct_delete=direct_del,key_values=key_values)
        if commit and payload is not None:
            return run_pyez_tasks(self, payload, 'xml', **kwargs) 
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
    config = IkeProposalManager()
    response = config.push_config()