from nornir import InitNornir
import logging
from utiliites_scripts.commit import run_pyez_tasks
class BaseManager:
    database = 'committed'
    
    def __init__(self, config_file="config.yml"):
        self.nr = InitNornir(config_file=config_file)
        
    def push_config(self):
        try:
            xml_data = self.operations()
            if not xml_data:
                logging.info("No XML data to push.")
                return
            if isinstance(xml_data, list):
                for xml in xml_data:
                    try:
                        run_pyez_tasks(self, xml, 'xml')
                    except Exception as e:
                        logging.error(f"Failed to push configuration for {xml}: {e}")
            else:
                try:
                    run_pyez_tasks(self, xml_data, 'xml')
                except Exception as e:
                    logging.error(f"Failed to push configuration: {e}")
        except Exception as e:
            logging.error(f"Error in push_config: {e}")
