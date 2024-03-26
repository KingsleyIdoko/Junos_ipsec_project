import re
import ipaddress
def is_valid_mac_address(mac):
    pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(pattern.match(mac))

def is_valid_string(input_string):
    pattern = r'^[a-zA-Z0-9_ ]+$'
    if re.match(pattern, input_string):
        words = input_string.split()
        return len(words) <= 5
    else:
        return False
def is_valid_ipv4_address(address):
    try:
        ipaddress.ip_network(address, strict=False)
        return True
    except ValueError:
        return False

def get_interfaces(device_interfaces):
    interface_names = []
    for interface in device_interfaces['interface']:
        if interface['name'].startswith('fab') or interface['name'].startswith('fxp'):
            continue
        gigether_options = interface.get('gigether-options')
        if gigether_options:
            parent = gigether_options.get('redundant-parent', {}).get('parent')
            if parent:
                interface_names.append(parent)
                continue  
        interface_names.append(interface['name'])
    return list(set(interface_names))

def is_valid_string(input_string):
    pattern = r'^[a-zA-Z0-9_ ]+$'
    if re.match(pattern, input_string):
        words = input_string.split()
        return len(words) <= 10
    else:
        return False
        
def select_interface(nested_interfaces):
    if not nested_interfaces or not isinstance(nested_interfaces[0], list):
        print("Invalid interface data provided.")
        return
    interfaces = nested_interfaces[0]  
    while True:  
        print("Please choose an interface for configuration by entering its number:\n")
        for index, interface in enumerate(interfaces, start=1):
            print(f"{index}. {interface['name']}")
        
        try:
            choice = int(input("\nEnter choice: ")) - 1 
            if choice < 0 or choice >= len(interfaces):
                print("Invalid choice. Please enter a number listed above.\n")
                continue  
            selected_interface = interfaces[choice]
            print(f"\nYou selected: {selected_interface['name']}")
            return selected_interface 
        except ValueError:
            print("Invalid input. Please enter a number.\n")



def config_interface(int_params, filtered_interface):
    print(f"Configuring interface {filtered_interface['name']}:\n")
    for index, name in enumerate(int_params, start=1):
        print(f"{index}. {name}")
    while True:
        try:
            choice = int(input("\nEnter your choice: ")) - 1
            if choice < 0 or choice >= len(int_params):
                print("Invalid choice. Please enter a number listed above.\n")
                continue
            selected_param = int_params[choice]
            print(f"\nYou selected: {selected_param}")
            if choice == 0: 
                while True:
                    desc = input(f"Enter description for {filtered_interface['name']}: ")
                    if is_valid_string(desc):
                        payload = config_description(desc) 
                        break 
                    else:
                        print("Invalid description. Please try again.")
                return
            elif choice == 2:
                return config_int_status()
            payload = f"""
            <configuration>
                <interfaces>
                    <interface operation="create">
                        <name>{filtered_interface['name']}</name>
                        {payload}
                    </interface>
                </interfaces>
            </configuration>"""
            return payload
        except ValueError:
            print("Invalid input. Please enter a number.\n")

   
def config_description(desc):
        xml_data = f"""<description>{desc}</description>"""
        return xml_data

def config_int_status():
    while True:
        try:
            choice = int(input("Enter 1 to enable or 0 to disable the interface: "))
            if choice == 1:
                print("Interface will be enabled (removing <disable/> if present).")
                payload = """<disable operation="delete"/>"""
                break  
            elif choice == 0:
                print("Interface will be disabled (adding <disable/>).")
                payload = "<disable/>"
                break  
            else:
                print("Invalid choice. Please enter 1 to enable or 0 to disable.")
        except ValueError:
            print("Invalid input. Please enter a valid number (1 or 0).")
    return payload

def set_int_params(interface_name):
    while True:
        try:
            unit = input("Enter unit number: ")
            print("Configure interface as Layer 2, Layer 2.5 (ISO), or Layer 3\n")
            choice = float(input("Enter choice (2 for Layer2, 2.5 for ISO, 3 for Layer3): "))
            data = ""

            if choice == 2:
                while True:
                    port_type = input("Specify 0 as access, 1 as trunk: ")
                    if port_type in ["0", "1"]:
                        port_mode = "access" if port_type == "0" else "trunk"
                        data = f"""
                                <ethernet-switching>
                                    <interface-mode>{port_mode}</interface-mode>
                                </ethernet-switching>"""
                        break
                    else:
                        print("Invalid choice selected, try again.")
            elif choice == 3:
                while True:
                    subnet = input("Enter the IP address (e.g., 192.168.1.1/24): ")
                    if is_valid_ipv4_address(subnet):
                        data = f"""
                                <inet>
                                    <address>
                                        <name>{subnet}</name>
                                    </address>
                                </inet>"""  
                        break
                    else:
                        print("IP address specified is not valid.")
            elif choice == 2.5:
                data  = """
                        <iso operation="create">
                        </iso>"""
            else:
                print("Invalid layer choice specified.")
                continue

            payload = f"""<unit>
                            <name>{unit}</name>
                            <family>
                                {data}
                            </family>       
                          </unit>"""
            return payload
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def config_mac(interface_name):
    while True:
        mac_address = input("Please enter Mac Address (e.g., 50:00:00:0f:00:03): ")
        if is_valid_mac_address(mac_address):
            payload = f"""
            <configuration>
                <interfaces>
                    <interface operation="create">
                        <name>{interface_name}</name>
                        <mac>{mac_address}</mac>
                    </interface>
                </interfaces>
            </configuration>"""
            print("MAC address configured successfully.")
            return payload
        else:
            print("You entered an invalid MAC address. Please try again.")

def config_speed(interface_name, speed):
    payload = f"""
    <configuration>
        <interfaces>
            <interface operation="create">
                <name>{interface_name}</name>
                <speed>{speed}<speed/>
            </interface>
        </interfaces>
    </configuration>"""
    return payload

def config_unit(interface_name):
    payload = f"""
    <configuration>
        <interfaces>
            <interface operation="create">
                    <unit>
                         <name>0</name>    
                    </unit>  
            </interface>
        </interfaces>
    </configuration>"""
    return payload



# payload = f"""
#     <configuration>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                 </interface>
#             </interfaces>
#     </configuration>"""



#     <configuration>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>
#                             <ethernet-switching>
#                                 <interface-mode>access</interface-mode>
#                             </ethernet-switching>
#                         </family>
#                     </unit>
#                 </interface>
#             </interfaces>
#     </configuration>


#     <configuration>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>
#                         </family>
#                     </unit>
#                 </interface>
#             </interfaces>
#     </configuration>
#     <cli>
#         <banner>[edit]</banner>
#     </cli>



#     <configuration>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>
#                             <ethernet-switching>
#                                 <interface-mode>trunk</interface-mode>
#                             </ethernet-switching>
#                         </family>
#                     </unit>
#                 </interface>
#             </interfaces>
#     </configuration>


#     <configuration>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <gigether-options>
#                         <ieee-802.3ad>
#                             <bundle>ae0</bundle>
#                         </ieee-802.3ad>
#                     </gigether-options>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>
#                             <ethernet-switching>
#                                 <interface-mode>trunk</interface-mode>
#                             </ethernet-switching>
#                         </family>
#                     </unit>             
#                 </interface>            
#             </interfaces>               
#     </configuration>  



# <configuration>
#             <chassis operation="create">
#                 <aggregated-devices>
#                     <ethernet>
#                         <device-count>5</device-count>
#                     </ethernet>
#                 </aggregated-devices>
#             </chassis>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <gigether-options>
#                         <ieee-802.3ad>
#                             <bundle>ae0</bundle>
#                         </ieee-802.3ad>
#                     </gigether-options>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>     
#                             <ethernet-switching>
#                                 <interface-mode>trunk</interface-mode>
#                             </ethernet-switching>
#                         </family>       
#                     </unit>             
#                 </interface>            
#             </interfaces>               
#     </configuration>        



#     <configuration>
#             <chassis operation="create">
#                 <aggregated-devices>
#                     <ethernet>
#                         <device-count>5</device-count>
#                     </ethernet>
#                 </aggregated-devices>
#             </chassis>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <gigether-options>
#                         <ieee-802.3ad>
#                             <bundle>ae0</bundle>
#                         </ieee-802.3ad>
#                     </gigether-options>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>     
#                             <ethernet-switching>
#                                 <interface-mode>trunk</interface-mode>
#                             </ethernet-switching>
#                         </family>       
#                     </unit>             
#                 </interface>            
#                 <interface operation="create">
#                     <name>ae0</name>    
#                     <aggregated-ether-options>
#                         <lacp>          
#                             <active/>   
#                             <periodic>fast</periodic>
#                         </lacp>         
#                     </aggregated-ether-options>
#                 </interface>            
#             </interfaces>               
#     </configuration>  



#     <configuration>
#             <chassis operation="create">
#                 <aggregated-devices>
#                     <ethernet>
#                         <device-count>5</device-count>
#                     </ethernet>
#                 </aggregated-devices>
#             </chassis>
#             <interfaces>
#                 <interface operation="create">
#                     <name>ge-0/0/5</name>
#                     <description>This is the VPN ZONE Traffic</description>
#                     <mtu>9192</mtu>
#                     <mac>50:00:00:0f:00:03</mac>
#                     <gigether-options>
#                         <ieee-802.3ad>
#                             <bundle>ae0</bundle>
#                         </ieee-802.3ad>
#                     </gigether-options>
#                     <unit>
#                         <name>0</name>
#                         <family>
#                             <inet>      
#                                 <address>
#                                     <name>10.0.0.1/24</name>
#                                 </address>
#                             </inet>     
#                             <ethernet-switching>
#                                 <interface-mode>trunk</interface-mode>
#                             </ethernet-switching>
#                         </family>       
#                     </unit>             
#                 </interface>            
#                 <interface operation="create">
#                     <name>ae0</name>    
#                     <aggregated-ether-options>
#                         <lacp>          
#                             <active/>   
#                             <periodic>fast</periodic>
#                         </lacp>         
#                     </aggregated-ether-options>
#                 </interface>            
#             </interfaces>               
#     </configuration> 