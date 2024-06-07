from sec_basemanager import BaseManager
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
from utiliites_scripts.sec_policies import (gen_sec_policies_config, gen_update_config, 
                                    gen_delete_config, re_order_policy)
import logging

class SecPolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
         super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get sec policies")
            print("2. create sec policies")
            print("3. update sec policies")
            print("4. delete sec policies")
            print("5. re_order security policies")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_sec_policy(interactive=True)
            elif operation == "2":
                return self.create_sec_policy()
            elif operation == "3":
                return self.update_sec_policy()
            elif operation == "4":
                return self.delete_sec_policy()
            elif operation == "5":
                return self.re_order_sec_policy()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_sec_policy(self, interactive=False):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
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
                return all_sec_policies if all_sec_policies else None
            print("No security policies configuration on the device")
        except Exception as e:
            print(f"An error has occurred while retrieving security policies: {e}")
            return None

    def create_sec_policy(self):
        try:
            raw_data = self.get_sec_policy() 
            if not raw_data:
                print("No Existing Security found.")
            payload = gen_sec_policies_config(raw_data=raw_data) 
            return payload
        except ValueError as e:
            print(f"ValueError occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

    def update_sec_policy(self):
        updated_payload = []
        try:
            raw_data = self.get_sec_policy()  
            payload1, old_policy_name = gen_update_config(raw_data)
            if old_policy_name:
                updated_payload.append(self.delete_sec_policy(old_policy_data=old_policy_name))
            updated_payload.append(payload1)
            return updated_payload
        except Exception as e:  
            logging.error(f"An error has occurred: {e}") 
            return None  

    def delete_sec_policy(self, old_policy_data=None):
        try:
            policy_name = self.get_sec_policy()
            payload = gen_delete_config(policy_name, old_policy_data)
            return payload
        except Exception as e:  
            logging.error(f"An error has occurred: {e}") 
            return None  
        
    def re_order_sec_policy(self):
        raw_data = self.get_sec_policy()
        return re_order_policy(raw_data)
        
if __name__ == "__main__":
    config = SecPolicyManager()
    response = config.push_config()
