from nornir_pyez.plugins.tasks import pyez_get_config,pyez_config, pyez_commit, pyez_diff
from nornir import InitNornir
from rich import print
import os
from xml.dom import minidom
from lxml import etree
from utiliites_scripts.fetch_data import append_nat_data
from utiliites_scripts.nat_exempt import nat_policy
from utiliites_scripts.pool_data import get_pool_data
script_dir = os.path.dirname(os.path.realpath(__file__))
class DeviceConfigurator:
    database = 'committed'
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)

    def fetch_nat_data(self):
        try:
            response = self.nr.run(task=pyez_get_config, database=self.database)
            for nat in response:
                result = response[nat].result['configuration']['security']['nat']['source']['rule-set']
                remote_subnets =  response[nat].result['configuration']['security']['address-book'][1]['address']
                source_subnets =  response[nat].result['configuration']['security']['address-book'][0]['address']
                nat_pool = response[nat].result['configuration']['security']['nat']['source']['pool']
                pool_name = response[nat].result['configuration']['security']['nat']['source']['pool'].get('name')
                try:
                    hostname = response[nat].result['configuration']['system']['host-name']
                except: 
                    hostname = response[nat].result['configuration']['groups'][0]['system']['host-name']
                nat_data = append_nat_data(result, hostname, remote_subnets, source_subnets)
            return nat_data, pool_name
        except Exception as e:
            print(f"An error has occurred: {e}")
            return None
    def overlapping_subnet(self):
        nat_type = 'pool'
        nat_data, pool_name = self.fetch_nat_data()
        global_nat_rule, source_zone, destination_zone, rule_name, remote_prefixes, source_prefixes = nat_data
        payload = nat_policy( global_nat_rule, source_zone, destination_zone, rule_name, nat_type, remote_prefixes, source_prefixes, pool_name)



config = DeviceConfigurator()
result = config.overlapping_subnet()