
from nornir_pyez.plugins.tasks import pyez_get_config
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.interfaces import select_interface,config_interface, enable_interface_config
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.commons import is_valid_interfaces, get_valid_integer
script_dir = os.path.dirname(os.path.realpath(__file__))

class InterfaceManager:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)
        self.int_params = ['Description', 'Disable | Enable', 'L2/3 Addressing', 'LACP', 'Add|Remove Vlan','MAC', 'MTU', 'Speed']

    def interface_operations(self):
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

    def get_interfaces(self, interactive=False, get_interface_name=None, retries=3):
        attempt = 0
        lacp_chassis = None
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    all_results = []
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
                    return (all_results, lacp_chassis) if lacp_chassis else all_results
                else:
                    print("No response received, trying again...")
            except Exception as e:
                print(f"An error has occurred: {e}")
                print("Checking connectivity to the device, trying again...")
            attempt += 1
        print("Failed to retrieve interfaces after several attempts.")
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

    def push_config(self):
        xml_data = None  
        try:
            xml_data = self.interface_operations()
            if not xml_data:
                return
            if isinstance(xml_data, list):
                for xml in xml_data:
                    run_pyez_tasks(self, xml, 'xml')
            else:
                run_pyez_tasks(self, xml_data, 'xml')

        except ValueError as e:
            print(e)
            print("An error occurred, review your config changes.")
            if xml_data:
                print("Failed configuration data:", xml_data)
            else:
                print("Configuration data was not generated due to an error.")


if __name__ == "__main__":
    config = InterfaceManager()
    response = config.push_config()