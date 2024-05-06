from nornir_pyez.plugins.tasks import pyez_get_config
from rich import print
import os
from utiliites_scripts.static_route import gen_static_route_config,update_static_route, del_static_route
from sec_basemanager import BaseManager

class StaticRouteManager(BaseManager):
    def __init__(self, config_file="config.yml"):
        super().__init__(config_file=config_file)
  
    def operations(self):
        while True:
            print("\nSpecify Operation.....")
            print("1. get static routes")
            print("2. create static route")
            print("3. update static route")
            print("4. delete static route")
            operation = input("Enter your choice (1-4): ")
            if operation == "1":
                return self.get_static_routes(interactive=True)
            elif operation == "2":
                return self.create_static_route()
            elif operation == "3":
                return self.update_static_route()
            elif operation == "4":
                return self.delete_static_route()
            else:
                print("Invalid choice. Please specify a valid operation.")
                continue

    def get_static_routes(self, interactive=False, get_raw_data=False, retries=3, get_route_name=False):
        attempt = 0
        while attempt < retries:
            try:
                response = self.nr.run(task=pyez_get_config, database=self.database)
                if response:
                    for _, result in response.items():
                        route_config = result.result['configuration']['routing-options']['static']
                        if route_config:
                            raw_static_route = route_config.get('route', [])
                            static_route = [raw_static_route] if isinstance(raw_static_route, dict) else raw_static_route
                            static_route_names = [static['name'] for static in static_route if 'name' in static]
                        else:
                            print("No IKE configuration found on the device.")
                            break
                    if interactive:
                        print("No existing IKE Policy on the device" if raw_static_route in ([], None) else raw_static_route)
                        return None
                    if get_route_name:
                        return static_route_names
                    if get_raw_data and raw_static_route:
                        return raw_static_route, static_route_names or None
            except Exception as e:
                print(f"An error has occurred: {e}. Trying again...")
            attempt += 1
        print("Failed to retrieve IKE policies after several attempts.")
        return None

    def create_static_route(self):
        static_route, *_ = self.get_static_routes(get_raw_data=True)
        if not static_route:
            print("No existing IPsec VPN found on the device")
            return None
        payload = gen_static_route_config(static_route=static_route)
        return payload

    def update_static_route(self):
        try:
            static_route, *_ = self.get_static_routes(get_raw_data=True)
            if static_route:
                payload = update_static_route(static_route=static_route)
            return payload
        except ValueError as e:
            print(f"An error has occured, {e}")
        
    def delete_static_route(self, commit=False, route_name=None):
        try:
            route_name = self.get_static_routes(get_route_name=True)
            payload = del_static_route(route_name=route_name)
            print(payload)
            return payload
        except Exception as e:
            print(f"An unexpected error occurred: {str(e)}")
            return None
        
if __name__ == "__main__":
    config = StaticRouteManager()
    response = config.push_config()