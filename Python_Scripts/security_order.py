# Import the necessary modules
from nornir_pyez.plugins.tasks import pyez_get_config, pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from utiliites_scripts.sec_reordering import re_order_policy

# Define the script directory
script_dir = os.path.dirname(os.path.realpath(__file__))

# Define the class Config
class SecurityPolicyManager:
    # Define the class attributes
    database = 'committed'

    # Define the class constructor
    def __init__(self, config_file):
        # Initialize the Nornir object with the config file
        self.nr = InitNornir(config_file=config_file)
        # Run the pyez_get_config task and store the response
        self.response = self.nr.run(task=pyez_get_config, database=self.database)

    # Define the method to get the policy names
    def get_policy_names(self):
        trust_to_untrust = []
        untrust_to_trust = []

        # Extract policy names from the response
        for dev in self.response:
            policy_names = self.response[dev].result['configuration']['security']['policies']['policy']
            for policy in policy_names:
                from_zone = policy['from-zone-name']
                to_zone = policy['to-zone-name']
                for p in policy['policy']:
                    policy_name = p['name']
                    # Categorize policies based on zone direction
                    if from_zone == 'trust' and to_zone == 'untrust':
                        trust_to_untrust.append(policy_name)
                    elif from_zone == 'untrust' and to_zone == 'trust':
                        untrust_to_trust.append(policy_name)
        return trust_to_untrust, untrust_to_trust

    def build_config(self):
        # Get policy names and build configuration payload
        trust_to_untrust, untrust_to_trust = self.get_policy_names()
        zone_direction = ['trust_to_untrust', 'untrust_to_trust']
        payload = []
        for zone in zone_direction:
            closest_policy = []
            if zone == 'trust_to_untrust':
                zone_a, zone_b = 'trust', 'untrust'
                for trust_policy in trust_to_untrust:
                    if trust_policy != 'default_trust_untrust':
                        closest_policy.append(trust_policy)
                        if len(closest_policy) <= 1:
                            closest_policy.append('default_trust_untrust')
                trust_zone_payload = re_order_policy(zone_a, zone_b, closest_policy)
                payload.append(trust_zone_payload)
            elif zone == 'untrust_to_trust':
                zone_a, zone_b = 'untrust', 'trust'
                for untrust_policy in untrust_to_trust:
                    if untrust_policy != 'default_untrust_trust':
                        closest_policy.append(untrust_policy)
                        if len(closest_policy) <= 1:
                            closest_policy.append('default_untrust_trust')
                untrust_zone_payload = re_order_policy(zone_a, zone_b, closest_policy)
                payload.append(untrust_zone_payload)
        return payload
    
    def push_config(self):
        # Build configuration payload and push it to devices
        payload = self.build_config()
        for commd in payload:
            response = self.nr.run(task=pyez_config, payload=commd, data_format='xml')
            for res in response:
                diff_result = self.nr.run(task=pyez_diff)
                for res in diff_result:
                    if diff_result[res].result is None:
                        print("No Config Change")
                        return
                    print(diff_result[res].result)
                    committed = self.nr.run(task=pyez_commit)
                    for res1 in committed:
                        print(committed[res1].result)

# Create an instance of the Config class with the provided config file
config = Config(config_file=f"{script_dir}/config.yml")

# Push the configuration changes to devices
response = config.push_config()







