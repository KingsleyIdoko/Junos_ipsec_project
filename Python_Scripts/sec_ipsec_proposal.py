
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ipsec_proposal import (gen_ipsec_proposal_config,update_ipsec_proposal,del_ipsec_proposal)
from sec_basemanager import BaseManager


class IPsecProposalManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get IPsec Proposal")
            print("2. Create IPsec Proposal")
            print("3. Update IPsec Proposal")
            print("4. Delete Ipsec Prospoal")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_ipsec_proposal(interactive=True)
            elif operation == "2":
                return self.create_ipsec_proposal()
            elif operation == "3":
                return self.update_ipsec_proposal()
            elif operation == "4":
                return  self.delete_ipsec_proposal()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_ipsec_proposal(self, interactive=False, get_raw_data=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response.failed:  
                    print("Failed to connect to the device, trying again...")
                    attempt += 1
                    continue
                for _, result in response.items():
                    ike_config = result.result['configuration']['security'].get('ipsec', {})
                    ipsec_proposal = ike_config.get('proposal', [])
                    ipsec_proposal = [ipsec_proposal] if isinstance(ipsec_proposal, dict) else ipsec_proposal
                    ipesec_ipsec_proposal = [ipsec_proposal['name'] for ipsec_proposal in ipsec_proposal if 'name' in ipsec_proposal]              
                if not ipsec_proposal:  
                    print("No IPsec Proposal configurations exist on the device.")
                    return None
                if interactive:
                    print(ipsec_proposal)
                    return
                if get_raw_data:
                    return ipsec_proposal
                return ipesec_ipsec_proposal
            except Exception as e:
                print(f"Check connectivity to the device, trying again...")
                attempt += 1
                continue  
        print("Failed to retrieve gateways after several attempts due to connectivity issues.")
        return None

    def create_ipsec_proposal(self):
        try:
            old_ipsec_proposal = self.get_ipsec_proposal()
            if not old_ipsec_proposal:
                print("No existing IPSEC Proposal found on the device")
            payload = gen_ipsec_proposal_config(old_ipsec_proposal=old_ipsec_proposal)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def update_ipsec_proposal(self):
        from sec_ipsec_policy import IpsecPolicyManager
        policy_manager = IpsecPolicyManager()
        used_ipsec_proposals = policy_manager.get_ipsec_policy(get_proposal_name=True)
        try:
            ipsec_proposal = self.get_ipsec_proposal(get_raw_data=True)
            if ipsec_proposal:
                payload, old_ipsec_name = update_ipsec_proposal(ipsec_proposal=ipsec_proposal,used_ipsec_proposals=used_ipsec_proposals)
            if old_ipsec_name:
                self.delete_ipsec_proposal(commit=True, ipsec_proposal_name=old_ipsec_name)
            return payload
        except Exception as e:
            print(f"An error occurred: {e}")
            print("No existing IKE gateways found on the device.")

    def delete_ipsec_proposal(self, commit=False, ipsec_proposal_name=None):
        from sec_ipsec_policy import IpsecPolicyManager
        policy_manager = IpsecPolicyManager()
        used_ipsec_proposals = policy_manager.get_ipsec_policy(get_proposal_name=True)
        if not commit:
            ipsec_proposal_name = self.get_ipsec_proposal()
            payload = del_ipsec_proposal(ipsec_proposal_name=ipsec_proposal_name,used_ipsec_proposals=used_ipsec_proposals)
            return payload
        else:
            ipsec_proposal_name=ipsec_proposal_name
            payload = del_ipsec_proposal(ipsec_proposal_name=ipsec_proposal_name,used_ipsec_proposals=used_ipsec_proposals)
            run_pyez_tasks(self, payload, 'xml')

if __name__ == "__main__":
    config = IPsecProposalManager()
    response = config.push_config()