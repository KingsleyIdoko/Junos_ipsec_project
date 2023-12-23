from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.clean_nat_rules import (rule_compare, first_duplicate_rule, nat_delete,
                                            re_order_nat_policy, compare_nat, filter_list,
                                            sort_rules)
from xml.dom import minidom
from lxml import etree
from functools import cmp_to_key
from utiliites_scripts.fetch_data import append_nat_data
from utiliites_scripts.commit import run_pyez_tasks

script_dir = os.path.dirname(os.path.realpath(__file__))

class DeviceConfigurator:
    database = 'committed'

    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def fetch_nat_data(self):
        nat_data = []
        try:
            self.response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in self.response:
                result = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']
                remote_subnets =  self.response[nat].result['configuration']['security']['address-book'][1]['address']
                nat_data = append_nat_data(result, nat_data, remote_subnets)
            return nat_data
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
        
    def build_config(self):
        global_nat_rule, source_zone, destination_zone, rule_set, nat_exempt_vpn_prefixes = self.fetch_nat_data()
        payload = minidom.parseString(nat_policy(global_nat_rule, source_zone, destination_zone, rule_set, nat_exempt_vpn_prefixes))
        formatted_xml = payload.toprettyxml()
        formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
        return formatted_xml
    
    def nat_rule_re_order(self):
        list_of_policies = []
        self.response = self.nr.run(task=pyez_get_config, database=self.database)
        for nat in self.response:
            nat_rules = self.response[nat].result['configuration']['security']['nat']['source']['rule-set']['rule']
        sorted_nat_rules = sorted(nat_rules, key=cmp_to_key(rule_compare))
        grap_duplicate_rules = compare_nat(sorted_nat_rules)
        unique_rules = filter_list(grap_duplicate_rules)
        dup_rules = first_duplicate_rule(unique_rules)
        del_duplicates = [item for item in set (dup_rules)]
        try: 
            for item in sorted_nat_rules:
                list_of_policies.append(item['name'])
            payload = re_order_nat_policy(list_of_policies)
        except Exception as e:
            print(f"An error has occured {e}")
        return payload, del_duplicates

    def push_config(self):
        new_nat_policy = self.build_config()
        response, committed = run_pyez_tasks(self, new_nat_policy, 'xml')
        # updated_nat_order, del_duplicates = self.nat_rule_re_order()
        # print(updated_nat_order)
        # response, committed = run_pyez_tasks(self, updated_nat_order, 'xml')
        # for rule in del_duplicates:
        #     payload = nat_delete(rule)
        #     response, committed = run_pyez_tasks(self, payload, 'xml')

config = DeviceConfigurator()
response = config.push_config()