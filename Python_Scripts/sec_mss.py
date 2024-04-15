from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.mss_config import input_integer, create_mss_config

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityMssManager:
    database = 'committed'

    def __init__(self, config_file="config.yml"):
        # Initialize the Nornir object with the config file
        self.nr = InitNornir(config_file=config_file)
        self.mss_value = input_integer("Enter the ipsec vpn mss: ")

    def get_mss(self):
        pass

    def create_mss(self):
        pass

    def update_mss(self):
        pass

    def delete_mss(self):
        pass

    def push_config(self):
        xml_data = self.nat_operations()
        if not xml_data:
            return None
        run_pyez_tasks(self, xml_data, 'xml')   

config =  SecurityMssManager()   
response = config.push_config()