from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os, sys
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.ikepolicy import gen_ikepolicy_config, update_ike_policy, del_ike_policy
from sec_ike_proposal import IkeProposalManager
from sec_basemanager import BaseManager
from utiliites_scripts.main_func import main

script_dir = os.path.dirname(os.path.realpath(__file__))

class IkePolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)
        self.ike_proposal = IkeProposalManager()

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get IKE policy")
            print("2. Create IKE policy")
            print("3. Update IKE policy")
            print("4. Delete IKE policy")
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

    def get(self, interactive=False, get_raw_data=False, get_proposal_names=False, get_policy_name=False, target=None):
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            if response:
                for _, result in response.items():
                    ike_config = result.result['configuration']['security'].get('ike', {})
                    proposals = ike_config.get('proposal', [])
                    if not isinstance(proposals, list):
                        proposals = [proposals]
                    ike_proposal_names = [proposal['name'] for proposal in proposals if 'name' in proposal]
                    if ike_config:
                        raw_ike_policy = ike_config.get('policy', [])
                        if not raw_ike_policy:
                            print("No existing IKE Policy on the device.")
                            return None
                        ike_policy = [raw_ike_policy] if isinstance(raw_ike_policy, dict) else raw_ike_policy
                        ike_policy_names = [policy['name'] for policy in ike_policy if 'name' in policy]
                        used_ike_proposals = [policy['proposals'] for policy in ike_policy if 'proposals' in policy]
                    else:
                        print("No IKE configuration found on the device.")
                        return None
                if interactive:
                    print("No existing IKE Policy on the device" if raw_ike_policy in ([], None) else raw_ike_policy)
                    return None
                if get_proposal_names:
                    return used_ike_proposals
                if get_policy_name:
                    return ike_policy_names
                if get_raw_data and raw_ike_policy:
                    return raw_ike_policy, ike_proposal_names or None
        except Exception as e:
            print(f"An error has occurred: {e}.")
        print("Failed to retrieve IKE policies.")
        return None

    def create(self, target):
        old_ike_policy = self.get(get_policy_name=True, target=target)
        ike_proposal = self.ike_proposal.get()
        if not ike_proposal:
            print("No existing IKE Proposal found on the device")
            return None
        payload = gen_ikepolicy_config(old_ike_policy=old_ike_policy, ike_proposal=ike_proposal)
        return payload

    def update(self, target):
        try:
            from sec_ike_gateway import IkeGatewayManager
            gateway_manager = IkeGatewayManager()
            ike_configs, proposal_names = self.get(get_raw_data=True, target=target)
            used_policy = gateway_manager.get(used_policy=True, target=target)
            payload, del_policy = update_ike_policy(ike_configs=ike_configs, proposal_names=proposal_names, used_policy=used_policy)
            if del_policy:
                self.delete(commit=True, policy_name=del_policy, used_policy=used_policy, target=target)
            return payload
        except ValueError as e:
            print(f"An error has occurred, {e}")

    def delete(self, target, commit=False, policy_name=None):
        from sec_ike_gateway import IkeGatewayManager
        gateway_manager = IkeGatewayManager()
        used_policy = gateway_manager.get(used_policy=True, target=target)
        if not commit:
            policy_name = self.get(get_policy_name=True, target=target)
            payload = del_ike_policy(policy_name=policy_name, used_policy=used_policy)
            return payload
        else:
            payload = del_ike_policy(policy_name=policy_name, used_policy=used_policy)
            run_pyez_tasks(self, payload, 'xml')

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python ike_policy_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, IkePolicyManager)
