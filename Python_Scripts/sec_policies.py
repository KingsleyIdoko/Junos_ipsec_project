from sec_basemanager import BaseManager
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
from utiliites_scripts.sec_policies import gen_sec_policies_config, gen_update_config

class SecPolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
         super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get security policies")
            print("2. create security policies")
            print("3. update security policies")
            print("4. delete security policies")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_sec_policy(interactive=True)
            elif operation == "2":
                return self.create_sec_policy()
            elif operation == "3":
                return self.update_sec_policy()
            elif operation == "4":
                return self.delete_sec_policy()
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
            if interactive:
                for policy in all_sec_policies:
                    print(policy)
                    return
            return all_sec_policies if all_sec_policies else None
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
        raw_data = self.get_sec_policy()
        payload = gen_update_config(raw_data)

    def delete_sec_policy(self):
        pass

if __name__ == "__main__":
    config = SecPolicyManager()
    response = config.push_config()
