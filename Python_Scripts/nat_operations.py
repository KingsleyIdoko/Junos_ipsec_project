from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.fetch_data import append_nat_data
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.selectprefix import select_prefix, select_nat_type
from utiliites_scripts.pool_data import (nat_pool_creation, check_nat_pull_duplicates,
                                         is_valid_nat_pool_name, is_valid_ipv4_address,
                                         delete_nat_pool, extract_pool_names)
script_dir = os.path.dirname(os.path.realpath(__file__))

class NatPolicyManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def fetch_nat_data(self):
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
                # source_subnets = select_prefix(source_subnets)
                # nat_data = append_nat_data(result, hostname, remote_subnets, source_subnets)
            return nat_pool, pool_names
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
    
    def nat_operations(self):
        print("Specify Operation.....\n")
        print("1. create nat pool")
        print("2. delete nat pool")
        print("3. create nat rule")
        print("4. delete nat rule")
        
        operation = input("Enter your choice (1-4): ")
        
        if operation == "1":
            result =  self.create_nat_pool()
            return result
        elif operation == "2":
            result = self.delete_nat_pool()
            return result
        elif operation == "3":
            self.create_nat_rule()
        elif operation == "4":
            self.delete_nat_rule()
        else:
            print("Invalid choice. Please specify a valid operation.")
    
    def create_nat_pool(self):
        print("Creating NAT Pool.......\n")
        pool_name = input("Specify name of pull: ")
        if not is_valid_nat_pool_name(pool_name):
            print("Name is not valid")
            self.create_nat_pool()
        else:
            address_name = input("Specify nat pool address: ")
            if not is_valid_ipv4_address(address_name):
                print("Prefix Length is not valid")
                self.create_nat_pool()
            else:
                nat_pool, _ = self.fetch_nat_data()
                print("Checking for duplicate nat pool name and nat prefixes......\n")
                result = check_nat_pull_duplicates(nat_pool, pool_name, address_name)
                if result:
                    print(result)
                    self.create_nat_pool()
                else:
                    payload = nat_pool_creation(pool_name, address_name)
                    return payload

    def delete_nat_pool(self):
        list_nat_pool = {}
        print("Select Nat Pool to delete: ")
        nat_pool, _ = self.fetch_nat_data()
        for index, pool in enumerate(nat_pool, start=1):
            print(f"{index}. '{pool['name']}'")
            list_nat_pool[index] = pool['name']
        user_choice = int(input("Enter the number of the nat_pool to delete: "))
        while user_choice < 1 or user_choice > len(nat_pool):
            print("Invalid number specified")
            user_choice = int(input("Enter the number of the nat_pool to delete: "))
        selected_nat_pool_name = list_nat_pool.get(user_choice)
        for pool in nat_pool:
            if  pool['name'] == selected_nat_pool_name:
                _, pool_names = self.fetch_nat_data()
                if selected_nat_pool_name in pool_names:
                    print("Pool name is in use, cannot be deleted")
                    break
                payload = delete_nat_pool(selected_nat_pool_name)
                return payload
        else:
            print("Nat details not found on the device")
        

    def create_nat_rule(self):
        nat_type = self.get_nat_rule_type()
        print(f"Creating NAT Rule of type: {nat_type}")
        print("Select Remote Prefixes............\n")
        remote_subnets = select_prefix(remote_subnets)
        print("Select Source Prefixes............\n")

    def delete_nat_rule(self):
        nat_type = self.get_nat_rule_type()
        print(f"Deleting NAT Rule of type: {nat_type}")
        


    def get_nat_rule_type(self):
        print("\nSpecify NAT rule type:")
        print("1. nat_exempt rule")
        print("2. interface rule")
        print("3. nat_pool")
        nat_type = input("Enter your choice (1-3): ")
        
        if nat_type == "1":
            return "nat_exempt rule"
        elif nat_type == "2":
            return "interface rule"
        elif nat_type == "3":
            return "nat_pool"
        else:
            print("Invalid choice. Please specify a valid NAT rule type.")
            return self.get_nat_rule_type()  # Recursively ask again for valid input


        
    # def create_nat_pool(self):

        
    # def overlapping_subnet(self):
    #     xml_data = []
    #     dictionaries = [{'off': None}, {'pool': None}, {'interface': None}]
    #     nat_type = select_nat_type(dictionaries)
    #     nat_data, pool_name = self.fetch_nat_data()
    #     global_nat_rule, source_zone, destination_zone, rule_name, remote_prefixes, source_prefixes = nat_data
    #     payload = minidom.parseString(nat_policy( global_nat_rule, source_zone, destination_zone, rule_name, nat_type, remote_prefixes, source_prefixes, pool_name))
    #     formatted_xml = payload.toprettyxml()
    #     formatted_xml = '\n'.join([line for line in formatted_xml.split('\n') if line.strip()])
    #     return formatted_xml

    def push_config(self):
        xml_data = self.nat_operations()
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml') 
        
        
config = NatPolicyManager()
result = config.push_config()