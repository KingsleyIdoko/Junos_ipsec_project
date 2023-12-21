from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from functools import cmp_to_key
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.clean_nat_rules import (compare_nat, Rm_dup_rules, filter_list, 
                                               nat_delete, rule_compare)
# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))
class DeviceConfigurator:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        # Initialize the Nornir object with the config file
        self.nr = InitNornir(config_file=config_file)
    def fetch_nat_rules(self):
        nat_rules= []
        try:
            self.response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in self.response:
                result = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']
                for nat_names in result['rule']:
                    nat_rules.append(nat_names)
            unfiltered_rules = compare_nat(nat_rules)
            filtered_rules = Rm_dup_rules(unfiltered_rules)
            payload = filter_list(filtered_rules)
            return payload, nat_rules
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
    def re_order_nat_rules(self):
        _, nat_rules = self.fetch_nat_rules()
        payload = sorted(nat_rules, key=cmp_to_key(rule_compare))
        rule_names = [rule['name'] for rule in payload]
        print(rule_names)
    
    def push_config(self):
        payload, _ = self.fetch_nat_rules()
        for rule in payload:
            xml_data = nat_delete(rule)
            response = self.nr.run(task=pyez_config, payload=xml_data, data_format='xml')
            for res in response:
                diff_result = self.nr.run(task=pyez_diff)
                for res in diff_result:
                    print("Checking for duplicate rules and cleaning it up")
                    if diff_result[res].result is None:
                        print("No Config Change")
                        return
                    print(diff_result[res].result)
                    committed = self.nr.run(task=pyez_commit)
                    for res1 in committed:
                        print(committed[res1].result)
config = DeviceConfigurator()
response = config.re_order_nat_rules()



