from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.mss_config import input_integer, create_mss_config

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

class DeviceConfigurator:
    database = 'committed'

    def __init__(self, config_file="config.yml"):
        # Initialize the Nornir object with the config file
        self.nr = InitNornir(config_file=config_file)
        self.mss_value = input_integer("Enter the ipsec vpn mss: ")


    def build_config(self):
        payload = create_mss_config(self.mss_value)
        return payload
    

    def push_config(self):
        mss_config = self.build_config()
        print(mss_config)
        run_pyez_tasks(self, mss_config, 'xml')  

config =  DeviceConfigurator()   
response = config.push_config()