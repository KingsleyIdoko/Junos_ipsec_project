def select_zone(zones):
    print("Select a zone:\n")
    for i, zone in enumerate(zones, start=1):
        print(f"{i}. {zone}")
    print(f"{len(zones) + 1}. Create new zone")

    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if 1 <= choice <= len(zones):
                print(f"You selected: {zones[choice - 1]}")
                return zones[choice - 1]
            elif choice == len(zones) + 1:
                print("Option to create a new zone selected.")
                # e.g., create_new_zone()
                return "create_new_zone"
            else:
                print(f"Please select a number between 1 and {len(zones) + 1}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def create_new_zone(zone_name, zone_description, services, protocols, select_interface):
    print("Creating a new zone...")
    payload = f"""
        <configuration>
            <security>
                <zones>
                    <security-zone>
                        <name>{zone_name}</name>
                        <description>{zone_description}</description>
                        <host-inbound-traffic>
                            <system-services>
                                <name>{services}</name>
                                <except/>
                            </system-services>
                            <protocols>
                                <name>{protocols}</name>
                                <except/>
                            </protocols>
                        </host-inbound-traffic>
                        <interfaces>
                            <name>{select_interface}</name>
                        </interfaces>
                    </security-zone>
                </zones>                
            </security>                 
    </configuration>"""

def get_system_services():
    services = [
        "all", "any-service", "appqoe", "bootp", "dhcp", "dhcpv6", "dns", "finger", "ftp", "high-availability",
        "http", "https", "ident-reset", "ike", "lsping", "netconf", "ntp", "ping", "r2cp", "reverse-ssh",
        "reverse-telnet", "rlogin", "rpm", "rsh", "snmp", "snmp-trap", "ssh", "tcp-encap", "telnet", "tftp",
        "traceroute", "webapi-clear-text", "webapi-ssl", "xnm-clear-text"
    ]

    print("Select a system service:\n")
    for i, service in enumerate(services, start=1):
        print(f"{i}. {service}")
    
    while True:
        try:
            choice = int(input("\nEnter your choice: "))
            if 1 <= choice <= len(services):
                selected_service = services[choice - 1]
                print(f"You selected: {selected_service}")
                return selected_service
            else:
                print(f"Please select a number between 1 and {len(services)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")