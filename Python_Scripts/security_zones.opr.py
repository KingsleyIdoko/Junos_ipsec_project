from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.security_zones import select_zone, get_system_services

script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityZoneManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. GET Security Zones")
            print("2. Create Security Zone")
            print("3. Update Security Zone")
            print("4. Delete Security Zone")
            
            operation = input("Enter your choice (1-4): ")
            
            if operation == "1":
                result = self.get_security_zone()
                return result
            elif operation == "2":
                result = self.create_security_zone()
                return result
            elif operation == "3":
                return self.update_security_zone()
            elif operation == "4":
                return self.delete_security_zone()
            else:
                print("Invalid choice. Please specify a valid operation.")
                # Instead of recursively calling nat_operations, just continue the loop
                continue

    def get_security_zone(self):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for zones in response:
                result = response[zones].result['configuration']['security']['zones']['security-zone']
                try:
                    hostname = response[zones].result['configuration']['system']['host-name']
                except: 
                    hostname = response[zones].result['configuration']['groups'][0]['system']['host-name']
            return result, hostname
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
        
    def create_security_zone(self):
        zones, hostname = self.get_security_zone()
        print("See existing zones below.......\n")
        zone_names = [zone['name'] for zone in zones]
        select_zone(zone_names)
    def update_security_zone(self):
        pass
    def delete_security_zone(self):
        pass
    def push_config(self):
        pass
config = SecurityZoneManager()
response = config.create_security_zone()