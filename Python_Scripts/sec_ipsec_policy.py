from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os, sys, logging
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ipsec_policy import gen_ipsecpolicy_config, update_ipsec_policy, del_ipsec_policy
from sec_ipsec_proposal import IPsecProposalManager
from sec_basemanager import BaseManager
from utiliites_scripts.main_func import main

proposal_manager = IPsecProposalManager()
script_dir = os.path.dirname(os.path.realpath(__file__))

class IpsecPolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)
  
    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get IPsec Policy")
            print("2. Create IPsec Policy")
            print("3. Update IPsec Policy")
            print("4. Delete IPsec Policy")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return "get"
            elif operation == "2":
                return "create"
            elif operation == "3":
                return "update"
            elif operation == "4":
                return "delete"
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get(self, interactive=False, get_proposal_name=False, get_raw_data=False, get_policy_name=False, target=None):
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            if response:
                for _, result in response.items():
                    ipsec_config = result.result['configuration']['security'].get('ipsec', {})
                    if ipsec_config:
                        raw_ipsec_policy = ipsec_config.get('policy', [])
                        ipsec_policy = [raw_ipsec_policy] if isinstance(raw_ipsec_policy, dict) else raw_ipsec_policy
                        ipsec_policy_names = [policy['name'] for policy in ipsec_policy if 'name' in policy]
                        used_proposals = [prop['proposals'] for prop in ipsec_policy]
                    else:
                        print("No IPsec configuration found on the device.")
                        break
                if interactive:
                    print("No existing IPsec Policy on the device" if raw_ipsec_policy in ([], None) else raw_ipsec_policy)
                    return None
                if get_policy_name:
                    return ipsec_policy_names
                if get_proposal_name:
                    return used_proposals
                if get_raw_data and raw_ipsec_policy:
                    return raw_ipsec_policy, ipsec_policy_names or None
        except Exception as e:
            print(f"An error has occurred: {e}.")
        print("Failed to retrieve IPsec policies.")
        return None

    def create(self, target):
        old_ipsec_policy = self.get(get_policy_name=True, target=target)
        ipsec_proposals = proposal_manager.get_ipsec_proposal()
        if not old_ipsec_policy:
            print("No existing IPsec Policy found on the device")
        payload = gen_ipsecpolicy_config(old_ipsec_policy=old_ipsec_policy, ipsec_proposals=ipsec_proposals)
        return payload

    def update(self, target):
        try:
            ipsec_configs, proposal_names = self.get(get_raw_data=True, target=target)
            payload, del_policy = update_ipsec_policy(ipsec_configs=ipsec_configs, proposal_names=proposal_names)
            if del_policy:
                self.delete(commit=True, policy_name=del_policy, target=target)
            return payload
        except ValueError as e:
            print(f"An error has occurred, {e}")

    def delete(self, target, commit=False, policy_name=None):
        if not commit:
            policy_name = self.get(get_policy_name=True, target=target)
            used_policy = None
            payload = del_ipsec_policy(policy_name=policy_name, used_policy=used_policy)
            return payload
        else:
            payload = del_ipsec_policy(policy_name=policy_name, used_policy=None)
            run_pyez_tasks(self, payload, 'xml')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ipsec_policy_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, IpsecPolicyManager)
