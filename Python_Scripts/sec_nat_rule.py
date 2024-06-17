from sec_basemanager import BaseManager
from utiliites_scripts.nat_rule import (generate_nat_rule_config,extract_nat_config,order_nat_rule,
                                        gen_nat_update_config,gen_delete_nat_rule,generate_static_nat_config)
from nornir_pyez.plugins.tasks import pyez_get_config
from utiliites_scripts.commons import get_valid_selection
from rich import print
import os
script_dir = os.path.dirname(os.path.realpath(__file__))

        
class NatPolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get nat rules")
            print("2. Create nat rule")
            print("3. Update nat rule")
            print("4. Delete nat rule")
            print("5. Order nat rule")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_nat(interactive=True)
            elif operation == "2":
                return self.create_nat_rule()
            elif operation == "3":
                return self.update_nat_rule()
            elif operation == "4":
                return self.delete_nat_rule()
            elif operation == "5":
                return self.order_nat_rule()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_nat(self, interactive=False, get_all_configs=False):
        """
        This function allows you to grab all the NAT configuration from the device.

        Parameters:
        - interactive (bool): If True, enables interactive mode, printing additional information.
        - get_all_configs (bool): If True, returns all NAT configurations.

        Returns:
        - If get_all_configs is True, returns a tuple containing all NAT configurations and rule sets.
        - If get_all_configs is False, returns NAT data.

        Note: If interactive mode is enabled and no NAT configuration exists on the device, it prints a message and returns None.
        """
        try:
            # Retrieve NAT configuration from the device
            response = self.nr.run(task=pyez_get_config, database=self.database)  
            nat_data = []

            # Process the response
            for _, values in response.items():
                nat_config = values.result.get('configuration', {}).get('security', {}).get('nat', {})
                src_rule_sets = nat_config.get('source',{}).get('rule-set', []) 
                static_rule_sets  = nat_config.get('static',{}).get('rule-set', []) 

                nat_type  = ["static_nat","source_nat","destination_nat"]
                choice = get_valid_selection("Select nat type configs to retrieve: ", nat_type)
                if src_rule_sets:
                    nat_data =  extract_nat_config(src_rule_sets)
                    if interactive:
                        if src_rule_sets:
                            print(src_rule_sets)
                    if get_all_configs:
                        return src_rule_sets, nat_data
                else:
                    if interactive:
                        print("No NAT configuration exists on the device.")

            # Return the NAT data or None if interactive mode is enabled
            if interactive:
                return None
            return nat_data
        except Exception as e:
            # Handle device unreachable exception
            print(f"The device is not reachable. Please ensure the device is up and running.")
            return None


    def create_nat_rule(self):
        """
        This function guides the user through the process of creating a NAT rule.

        Returns:
        - If successful, returns the generated NAT rule configuration.
        - If an error occurs, prints an error message and returns None.
        """
        try:
            # Retrieve NAT data from the device
            nat_data = self.get_nat()
            while True:
                type_nat = ["static nat", "source nat", "destination nat"]
                choice = get_valid_selection("Specify the type of nat: ", type_nat)
                if choice == "static nat":
                    return generate_static_nat_config(nat_data)
                elif choice == "source nat":
                    rule_type = ["interface nat", "pool nat", "nat exempt"]
                    rule_choice = get_valid_selection("Specify the nat rule: ", rule_type)
                    if rule_choice == "interface nat":
                        choice = {'interface': None}
                        return generate_nat_rule_config(choice, nat_data)
                    elif rule_choice == "pool nat":
                        choice = {'pool': None}
                        return generate_nat_rule_config(choice, nat_data)
                    elif rule_choice == "nat exempt":
                        choice = {'off': None}
                        return generate_nat_rule_config(choice, nat_data)
                elif choice == "destination nat":
                    # Implement destination NAT configuration logic here
                    pass
        except Exception as e:
            # Handle any exceptions and print an error message
            print(f"An error has occurred: {e}")
            return None

    def update_nat_rule(self):
        try:
            rule_set,nat_data = self.get_nat(get_all_configs=True)
            return gen_nat_update_config(rule_set, nat_data)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None   
        
    def delete_nat_rule(self):
        try:
            *_,nat_data = self.get_nat(get_all_configs=True)
            return gen_delete_nat_rule(nat_data=nat_data)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None   
        
    def order_nat_rule(self):
        try:
            *_,nat_data = self.get_nat(get_all_configs=True)
            return order_nat_rule(nat_data)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None   

if __name__ == "__main__":
    config = NatPolicyManager()
    result = config.push_config()