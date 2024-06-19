from sec_basemanager import BaseManager
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
from utiliites_scripts.commons import get_valid_selection
from utiliites_scripts.sec_policies import (gen_sec_policies_config, gen_update_config, 
                                            gen_delete_config, re_order_policy)
import logging
import sys
from utiliites_scripts.main_func import main

class SecPolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get security policies")
            print("2. Create security policy")
            print("3. Update security policy")
            print("4. Delete security policy")
            print("5. Re-order security policies")
            operation = input("Enter your choice (1-5): ")
            if operation == "1":
                return "get"
            elif operation == "2":
                return "create"
            elif operation == "3":
                return "update"
            elif operation == "4":
                return "delete"
            elif operation == "5":
                return "re_order"
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get(self, interactive=False, target=None):
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            all_sec_policies = []
            for _, value in response.items():
                sec_policies = value.result.get('configuration', {}).get('security', {}).get('policies', {}).get('policy')
                if sec_policies:
                    all_sec_policies += sec_policies if isinstance(sec_policies, list) else [sec_policies]
            if all_sec_policies:
                if interactive:
                    for policy in all_sec_policies:
                        print(policy)
                    return None
                return all_sec_policies
            print("No security policies configuration on the device")
        except Exception as e:
            print(f"The device is not reachable. Please check connectivity")
            return None

    def create(self, target):
        try:
            raw_data = self.get(target=target)
            if not raw_data:
                print("No Existing Security found.")
                return None
            payload = gen_sec_policies_config(raw_data=raw_data)
            return payload
        except ValueError as e:
            print(f"ValueError occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def update(self, target):
        try:
            raw_data = self.get(target=target)
            if raw_data:
                return gen_update_config(raw_data)
        except Exception as e:
            logging.error(f"An error has occurred: {e}")
            return None

    def delete(self, target, old_policy_data=None):
        try:
            policy_name = self.get(target=target)
            payload = gen_delete_config(policy_name, old_policy_data)
            return payload
        except Exception as e:
            logging.error(f"An error has occurred: {e}")
            return None

    def re_order(self, target):
        raw_data = self.get(target=target)
        return re_order_policy(raw_data)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python sec_policy_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, SecPolicyManager)
