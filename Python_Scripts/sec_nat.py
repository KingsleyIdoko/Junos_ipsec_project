from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.fetch_data import append_nat_data
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.selectprefix import select_prefix
from utiliites_scripts.pool_data import (nat_pool_creation, check_nat_pull_duplicates,
                                         is_valid_name, is_valid_ipv4_address,
                                         delete_nat_pool, extract_pool_names)
script_dir = os.path.dirname(os.path.realpath(__file__))

class NatPolicyManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Create NAT pool")
            print("2. Delete NAT pool")
            print("3. Create NAT rule")
            print("4. Delete NAT rule")
            
            operation = input("Enter your choice (1-4): ")
            
            if operation == "1":
                result = self.create_nat_pool()
                return result
            elif operation == "2":
                result = self.delete_nat_pool()
                return result
            elif operation == "3":
                return self.create_nat_rule()
            elif operation == "4":
                return self.delete_nat_rule()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_nat_data(self):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in response:
                result = response[nat].result['configuration']['security']['nat']['source']['rule-set']
                remote_subnets =  response[nat].result['configuration']['security']['address-book'][1]['address']
                source_subnets =  response[nat].result['configuration']['security']['address-book'][0]['address']
                nat_pool = response[nat].result['configuration']['security']['nat']['source']['pool']
                pool_names = extract_pool_names(result)
                try:
                    hostname = response[nat].result['configuration']['system']['host-name']
                except: 
                    hostname = response[nat].result['configuration']['groups'][0]['system']['host-name']
                nat_data = append_nat_data(result, hostname, remote_subnets, source_subnets)
            return nat_pool, pool_names, nat_data
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None


    def create_nat_pool(self):
        print("Creating NAT Pool.......\n")
        while True:
            pool_name = input("Specify name of pool: ")
            if not is_valid_name(pool_name):
                print("Name is not valid.")
                continue
            address_name = input("Specify NAT pool address: ")
            if not is_valid_ipv4_address(address_name):
                print("Prefix Length is not valid.")
                continue
            nat_pool, *_ = self.get_nat_data()
            print("Checking for duplicate NAT pool name and NAT prefixes......\n")
            if check_nat_pull_duplicates(nat_pool, pool_name, address_name):
                print("Duplicate NAT pool name or prefix detected. Try again.")
                continue
            return nat_pool_creation(pool_name, address_name)

    def delete_nat_pool(self):
        print("Select NAT Pool to delete: ")
        try:
            raw_nat_pool, pool_names = self.get_nat_data()
            nat_pool = raw_nat_pool if isinstance(raw_nat_pool, list) else [raw_nat_pool]
            list_nat_pool = {index + 1: pool['name'] for index, pool in enumerate(nat_pool)}
            for index, name in list_nat_pool.items():
                print(f"{index}. '{name}'")
            try:
                user_choice = int(input("Enter the number of the NAT pool to delete: "))
                while user_choice not in list_nat_pool:
                    print("Invalid number specified. Try again.")
                    user_choice = int(input("Enter the number of the NAT pool to delete: "))
            except ValueError:
                print("Please enter a valid integer.")
                return
            selected_nat_pool_name = list_nat_pool.get(user_choice)
            if selected_nat_pool_name in pool_names:
                print("Pool name is in use, cannot be deleted.")
                return
            return delete_nat_pool(selected_nat_pool_name)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
        
    def create_nat_rule(self):
        print("\nSpecify NAT rule type:")
        print("1. nat exempt")
        print("2. interface nat")
        print("3. nat_pool")
        nat_type = input("Enter your choice (1-3): ")
        if nat_type == "1":
            nat_type = {'off': None},
            result = self.generate_nat_rule(nat_type)
            return result
        elif nat_type == "2":
            nat_type = {'interface': None},
            result = self.generate_nat_rule(nat_type)
            return result
        elif nat_type == "3":
            nat_type = {'pool': None},
            result = self.generate_nat_rule(nat_type,)
            return result
        else:
            print("Invalid choice. Please specify a valid NAT rule type.")
            return self.get_nat_rule_type() 

    def delete_nat_rule(self):
        nat_type = self.get_nat_rule_type()
        print(f"Deleting NAT Rule of type: {nat_type}")

    def generate_nat_rule(self, nat_type, pool_name=None):
        *_, nat_data = self.get_nat_data()
        global_nat_rule, source_zone, destination_zone, rule_name, remote_prefixes, source_prefixes = nat_data
        # print("Select Global Nat name: ")
        # 1. use existing rule-set Name:
        # 2. create new Name:

        print(f"Creating source nat Rules............")
        print(f"Select Source prefixes by entering the numbers separated by commas (e.g., 1,2). Enter '0' for None.............\n")
        source_subnets = select_prefix(source_prefixes)
        print(f"Select Remote prefixes by entering the numbers separated by commas (e.g., 1,2). Enter '0' for None.............\n")
        while True:
                    print("Select Remote prefixes by entering the numbers separated by commas (e.g., 1,2). Enter '0' for None.............\n")
                    remote_subnets = select_prefix(remote_prefixes)
                    if remote_subnets:  # Check if the selection is not empty
                        break
                    else:
                        print("Error: At least one destination subnet must be selected. Selection cannot be 'None'. Please try again.")
        payload = minidom.parseString(nat_policy( global_nat_rule, source_zone, destination_zone, rule_name, 
                                                 nat_type, remote_subnets, source_subnets, pool_name))
        formatted_xml = payload.toprettyxml()
        print(formatted_xml)
        return formatted_xml
        
    def push_config(self):
        xml_data = self.nat_operations()
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml') 
        
        
config = NatPolicyManager()
result = config.create_nat_rule()