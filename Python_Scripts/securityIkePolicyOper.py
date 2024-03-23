
from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.security_zones import select_zone, update_zone, zone_interface_names,find_available_interfaces
from utiliites_scripts.interfaces import get_interfaces
from utiliites_scripts.commit import run_pyez_tasks

script_dir = os.path.dirname(os.path.realpath(__file__))

class InterfaceManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def nat_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Intefaces")
            print("2. Delete Interfaces")
            print("3. Update Interfaces")
            print("4. Delete Interfaces")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                response = self.get_interfaces()
                return response
            elif operation == "2":
                response = self.create_interfaces()
                return response
            elif operation == "3":
                response = self.update_interfaces()
                return response
            elif operation == "4":
                response =  self.delete_interfaces()
                return response
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_interfaces(self):
        pass
    
    def create_interfaces(self):
        pass

    def update_interfaces(self):
        pass
    
    def delete_interfaces(self):
        pass

    def push_config(self):
        xml_data = self.nat_operations()
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml') 

config = InterfaceManager()
response = config.push_config()