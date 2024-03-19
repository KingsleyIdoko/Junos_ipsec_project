from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.commit import run_pyez_tasks
from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
import re, ipaddress
script_dir = os.path.dirname(os.path.realpath(__file__))
class NatPool:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def fetch_nat_data(self):
        response = self.nr.run(task=pyez_get_config, database=self.database)
        for nat in response:
            pool_name = response[nat].result['configuration']['security']['nat']['source']['pool'].get('name')
            try:
                hostname = response[nat].result['configuration']['system']['host-name']
            except: 
                hostname = response[nat].result['configuration']['groups'][0]['system']['host-name']
        return pool_name, hostname

    def validate_pool_name(self, pool_name):
        import re
        pattern = r"^[A-Z][A-Z0-9_]{0,62}$"
        if re.match(pattern, pool_name):
            return True
        else:
            return False

    def validate_ip_prefix(self, ip_prefix):
        import ipaddress
        try:
            network = ipaddress.IPv4Network(ip_prefix, strict=False)
            if network.network_address == network[0]:
                return True
            else:
                return False
        except ValueError:
            return False

    def create_nat_pool(self):
        pool_name, hostname = self.fetch_nat_data()
        pattern = r"^[A-Z][A-Z0-9_]{0,62}$"
        if pool_name:
            print("The following pool_name already exist: \n", pool_name)
        pool_name = input(f"Enter pool names for device {hostname}: ").upper()
        pool_prefix = input(f"Specify prefix {hostname}: ").upper()

        while not self.validate_pool_name(pool_name):
            print("Invalid pool name. Please try again.")
            pool_name = input("Enter pool names: ").upper()

        while not self.validate_ip_prefix(pool_prefix):
            print("Invalid ip prefix. Please try again.")
            pool_prefix = input("Specify prefix: ").upper()

        if re.match(pattern, pool_name):
            network = ipaddress.IPv4Network(pool_prefix, strict=False)
            if network.network_address == network[0]:
                    payload = f""" <configuration>
                                <security>
                                    <nat>
                                        <source>
                                            <pool>
                                                <name>{pool_name}</name>
                                                <address>
                                                    <name>{pool_prefix}</name>
                                                </address>
                                            </pool>
                                        </source>
                                    </nat>
                                </security>
                        </configuration>"""
                    print(payload)
            return payload
        
    def push_config(self):
        new_nat_pool = self.create_nat_pool()
        run_pyez_tasks(self, new_nat_pool, 'xml') 

object = NatPool()
response = object.push_config()