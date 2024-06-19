from sec_basemanager import BaseManager
from utiliites_scripts.nat_rule import (generate_nat_rule_config, extract_nat_config, order_nat_rule,
                                        gen_nat_update_config, gen_delete_nat_rule, generate_static_nat_config)
from nornir_pyez.plugins.tasks import pyez_get_config
from utiliites_scripts.commons import get_valid_selection
from rich import print
import os
import sys
from utiliites_scripts.main_func import main

script_dir = os.path.dirname(os.path.realpath(__file__))

class NatPolicyManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get NAT rules")
            print("2. Create NAT rule")
            print("3. Update NAT rule")
            print("4. Delete NAT rule")
            print("5. Order NAT rule")
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
                return "order"
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get(self, interactive=False, get_all_configs=False, target=None):
        nat_type = ["static_nat", "source_nat", "destination_nat", "All"]
        try:
            response = self.nr.filter(name=target).run(task=pyez_get_config, database=self.database)
            nat_data = []
            for _, values in response.items():
                nat_config = values.result.get('configuration', {}).get('security', {}).get('nat', {})
                src_rule_sets = nat_config.get('source', {}).get('rule-set', [])
                static_rule_sets = nat_config.get('static', {}).get('rule-set', [])
                dest_rule_sets = nat_config.get('destination', {}).get('rule-set', [])
                choice = get_valid_selection("Select NAT type configs to retrieve: ", nat_type)
                if choice == "static_nat":
                    nat_data = extract_nat_config(static_rule_sets)
                elif choice == "source_nat":
                    nat_data = extract_nat_config(src_rule_sets)
                elif choice == "destination_nat":
                    nat_data = extract_nat_config(dest_rule_sets)
                elif choice == "All":
                    nat_data = extract_nat_config(src_rule_sets + static_rule_sets + dest_rule_sets)
                    if interactive:
                        if src_rule_sets:
                            print(src_rule_sets)
                    if get_all_configs:
                        return src_rule_sets, nat_data
                else:
                    if interactive:
                        print("No NAT configuration exists on the device.")

            if interactive:
                return None
            return nat_data
        except Exception as e:
            print(f"The device is not reachable. Please ensure the device is up and running.")
            return None

    def create(self, target):
        try:
            nat_data = self.get(target=target)
            while True:
                type_nat = ["static nat", "source nat", "destination nat"]
                choice = get_valid_selection("Specify the type of NAT: ", type_nat)
                if choice == "static nat":
                    return generate_static_nat_config(nat_data)
                elif choice == "source nat":
                    rule_type = ["interface nat", "pool nat", "nat exempt"]
                    rule_choice = get_valid_selection("Specify the NAT rule: ", rule_type)
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
                    pass
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

    def update(self, target):
        try:
            rule_set, nat_data = self.get(get_all_configs=True, target=target)
            return gen_nat_update_config(rule_set, nat_data)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

    def delete(self, target):
        try:
            *_, nat_data = self.get(get_all_configs=True, target=target)
            return gen_delete_nat_rule(nat_data=nat_data)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

    def order(self, target):
        try:
            *_, nat_data = self.get(get_all_configs=True, target=target)
            return order_nat_rule(nat_data)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python nat_policy_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, NatPolicyManager)
