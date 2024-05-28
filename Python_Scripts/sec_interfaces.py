
from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os
from utiliites_scripts.interfaces import select_interface,config_interface, enable_interface_config
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.commons import is_valid_interfaces, get_valid_integer
from sec_basemanager import BaseManager

class InterfaceManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)
        self.int_params = ['Description', 'Disable | Enable', 'L2/3 Addressing', 
                           'LACP', 'Add|Remove Vlan','MAC', 'MTU', 'Speed']

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get Intefaces")
            print("2. Create Interfaces")
            print("3. Update Interfaces")
            print("4. Delete Interfaces")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_interfaces(interactive=True)
            elif operation == "2":
                return self.create_interfaces()
            elif operation == "3":
                return self.update_interfaces()
            elif operation == "4":
                return self.delete_interfaces()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_interfaces(self, interactive=False, get_interface_name=None, get_only_interfaces=False):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            if response:
                all_results = []
                lacp_chassis = None
                for _, interface_value in response.items():
                    result = interface_value.result['configuration']['interfaces']['interface']
                    try:
                        lacp_chassis = interface_value.result['configuration']['chassis']['aggregated-devices']['ethernet']
                    except KeyError:
                        lacp_chassis = None
                    all_results.append(result)
                    
                if interactive:
                    for result in all_results:
                        print(result)
                    return
                
                if get_interface_name:
                    interface_names = [interface['name'] for sublist in all_results for interface in sublist if not interface['name'].startswith('fxp')]
                    return interface_names
                if get_only_interfaces:
                    return all_results
                return (all_results, lacp_chassis) if lacp_chassis else all_results
            else:
                print("No response received.")
        except Exception as e:
            print(f"An error has occurred: {e}")
            print("Failed to retrieve interfaces due to connectivity issues.")
        
        return None


    def create_interfaces(self, commit_directly=False):
        existing_interfaces = self.get_interfaces(get_interface_name=True)
        interface_name = is_valid_interfaces()
        if interface_name is None:
            print("No valid interface name provided. Exiting...")
            return None
        if interface_name in existing_interfaces:
            print(f"{interface_name} already exists on the device.")
            return None
        sub_interface = get_valid_integer("Enter unit number (unit x): ")
        payload = enable_interface_config(interface_name, sub_interface)
        if commit_directly:
            run_pyez_tasks(self, payload, 'xml')
            print("Configuration committed directly.")
        else:
            print("Configuration prepared but not committed.")
        return payload
        
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
            config_output = config_interface(self.int_params, filtered_interface, lacp_chasis)
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

if __name__ == "__main__":
    config = InterfaceManager()
    response = config.push_config()