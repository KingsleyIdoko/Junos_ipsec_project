from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.mss_config import input_integer, create_mss_config
from sec_basemanager import BaseManager

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityMssManager(BaseManager):

    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def get_mss(self):
        pass

    def create_mss(self):
        pass

    def update_mss(self):
        pass

    def delete_mss(self):
        pass

if __name__ == "__main__":
    config =  SecurityMssManager()   
    response = config.push_config()