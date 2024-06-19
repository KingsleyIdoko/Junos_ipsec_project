from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff
from rich import print
import os, sys
from utiliites_scripts.commit import run_pyez_tasks
from utiliites_scripts.mss_config import input_integer, create_mss_config
from sec_basemanager import BaseManager
from utiliites_scripts.main_func import main

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

class SecurityMssManager(BaseManager):

    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)

    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. Get MSS configuration")
            print("2. Create MSS configuration")
            print("3. Update MSS configuration")
            print("4. Delete MSS configuration")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return "get"
            elif operation == "2":
                return "create"
            elif operation == "3":
                return "update"
            elif operation == "4":
                return "delete"
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get(self, target=None):
        # Placeholder for the actual get MSS configuration code
        pass

    def create(self, target):
        # Placeholder for the actual create MSS configuration code
        pass

    def update(self, target):
        # Placeholder for the actual update MSS configuration code
        pass

    def delete(self, target):
        # Placeholder for the actual delete MSS configuration code
        pass

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python security_mss_manager.py <target>")
        sys.exit(1)
    target = sys.argv[1]
    main(target, SecurityMssManager)
