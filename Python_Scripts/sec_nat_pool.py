from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os
from xml.dom import minidom
from utiliites_scripts.fetch_data import append_nat_data
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.selectprefix import select_prefix
from sec_basemanager import BaseManager
from utiliites_scripts.pool_data import (gen_delete_pool_config, extract_pool_names,gen_nat_pool_config,
                                         gen_updated_pool_config,gen_updated_pool_config,extract_pool_names)
script_dir = os.path.dirname(os.path.realpath(__file__))

class NatPoolManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get nat configs")
            print("2. Create nat pool")
            print("3. Update nat pool")
            print("4. Delete nat pool")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_nat(interactive=True)
            elif operation == "2":
                return self.create_nat_pool()
            elif operation == "3":
                return self.update_nat_pool()
            elif operation == "4":
                return self.delete_nat_pool()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_nat(self, interactive=False, get_pool_names=False):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)    
            all_nat_data = []
            all_nat_pools = []
            all_pool_names = []
            for _, result in response.items():
                nat_config = result.result.get('configuration', {}).get('security', {}).get('nat', {}).get('source', {})
                rule_sets = nat_config.get('rule-set', []) 
                used_pool_names = extract_pool_names(rule_sets) if rule_sets else []
                nat_pool = nat_config.get('pool', [])
                address_books = result.result.get('configuration', {}).get('security', {}).get('address-book', [])
                remote_subnets = address_books[1].get('address', []) if len(address_books) > 1 else []
                source_subnets = address_books[0].get('address', []) if len(address_books) > 1 else []
                pool_names = extract_pool_names(rule_sets) if rule_sets else []
                try:
                    hostname = result.result['configuration']['system']['host-name']
                except KeyError:
                    hostname = result.result.get('configuration', {}).get('groups', [{}])[0].get('system', {}).get('host-name', 'Unknown Hostname')
                nat_data = append_nat_data(rule_sets, hostname, remote_subnets, source_subnets) if rule_sets else []
                all_nat_data.extend(nat_data)
                all_nat_pools.extend(nat_pool)
                all_pool_names.extend(pool_names)
            if interactive and rule_sets:
                print(rule_sets)
                if nat_pool:
                    print(nat_pool)
                return None
            if get_pool_names:
                return nat_pool, used_pool_names
            return all_nat_pools, all_pool_names, all_nat_data
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
        
    def create_nat_pool(self):
        try:
            nat_data, used_pool_names = self.get_nat(get_pool_names=True)
            return gen_nat_pool_config(nat_data, used_pool_names)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
    def update_nat_pool(self):
        try:
            nat_data, used_pool_names = self.get_nat(get_pool_names=True)
            return gen_updated_pool_config(nat_data, used_pool_names)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
    
    def delete_nat_pool(self):
        print("Select NAT Pool to delete: ")
        try:
            nat_data, used_pool_names = self.get_nat(get_pool_names=True)
            return gen_delete_pool_config(nat_data, used_pool_names)
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None

if __name__ == "__main__":
    config = NatPoolManager()
    result = config.push_config()
