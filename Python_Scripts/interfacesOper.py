
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

    def interface_operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Intefaces")
            print("2. Update Interfaces")
            print("3. Delete Interfaces")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_interfaces(interactive=True)
            elif operation == "2":
                return self.update_interfaces()
            elif operation == "4":
                return self.delete_interfaces()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_interfaces(self, interactive=False, retries=3):
        attempt = 0
        lacp_chasis = None  
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    all_results = []
                    for interface in response:
                        result = response[interface].result['configuration']['interfaces']['interface']
                        try:
                            lacp_chasis = response[interface].result['configuration']['chassis']['aggregated-devices']['ethernet']
                        except KeyError:
                            lacp_chasis = None
                        all_results.append(result)
                    if interactive:
                        for result in all_results:
                            print(result)
                            return None
                    return (all_results, lacp_chasis) if lacp_chasis else all_results
                else:
                    print("No response received, trying again...")
            except Exception as e:
                print(f"An error has occurred: {e}")
                print("Checking connectivity to the device, trying again...")
            attempt += 1
        print("Failed to retrieve interfaces after several attempts.")
        return None


    def update_interfaces(self):
        payload = []
        get_interfaces_output = self.get_interfaces()
        if isinstance(get_interfaces_output, tuple) and len(get_interfaces_output) == 2:
            interfaces, lacp_chasis = get_interfaces_output
        else:
            interfaces = get_interfaces_output
            lacp_chasis = None
        if interfaces:
            filtered_interface = select_interface(interfaces)
            if not filtered_interface: 
                return None
            int_params = ['Description', 'Disable | Enable', 'L2/3 Addressing', 'LACP', 'MAC', 'MTU', 'Speed']
            config_output = config_interface(int_params, filtered_interface, lacp_chasis)
            if isinstance(config_output, list):  
                payload.extend(config_output)
            else:  
                if config_output:  
                    payload.append(config_output)
            return payload
        else:
            print("Failed to retrieve interfaces.")
            return None



    def delete_interfaces(self):
        pass

    def push_config(self):
        xml_data = self.interface_operations()
        if not xml_data:
            return None
        elif isinstance(xml_data, list):
            for xml in xml_data:
                run_pyez_tasks(self, xml, 'xml') 
                return None
        else:
             run_pyez_tasks(self, xml_data, 'xml') 


config = InterfaceManager()
response = config.push_config()