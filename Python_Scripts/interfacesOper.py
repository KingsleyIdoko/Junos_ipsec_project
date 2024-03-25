
from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.interfaces import select_interface,config_interface
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
            print("2. Create Interfaces")
            print("3. Update Interfaces")
            print("4. Delete Interfaces")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                response = self.get_interfaces(interactive=True)
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

    def get_interfaces(self, interactive=False, retries=3):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    all_results = []  
                    for interface in response:
                        result = response[interface].result['configuration']['interfaces']['interface']
                        all_results.append(result)  
                    if interactive:
                        for result in all_results:
                            print(result)  
                    return all_results  
                else:
                    print("No response received, trying again...")
            except Exception as e:
                print(f"An error has occurred: {e}")
                print("Checking connectivity to the device, trying again...")
            attempt += 1
        print("Failed to retrieve interfaces after several attempts.")
        return None


    def create_interfaces(self):
        interfaces = self.get_interfaces()
        filtered_interface = select_interface(interfaces)
        int_params = ['description', 'disable', 'gigether-options', 
        'mac', 'mtu', 'speed', 'unit']  
        config_interface(int_params, filtered_interface)

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