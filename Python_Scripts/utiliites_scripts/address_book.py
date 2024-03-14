    
def create_address_book(addressbook_name, address_name, ipv4_address, zone):
    payload = f"""
        <configuration>
                <security>
                    <address-book>
                        <name>{addressbook_name}</name>
                        <address>
                            <name>{address_name}</name>
                            <ip-prefix>{ipv4_address}</ip-prefix>
                        </address>
                        <attach>
                            <zone>
                                <name>{zone}</name>
                            </zone>
                        </attach>
                    </address-book>        
                </security>                 
        </configuration>"""
    return payload


def map_subnets_to_zones(subnets):
    return [{subnet['name']: subnet['attach']['zone']['name']} for subnet in subnets]

def select_address_book(address_books):
    print("Select existing address_book.......\n")
    
    # Create a list of address book names from the dictionaries
    address_book_names = [list(book.keys())[0] for book in address_books]
    
    # Display the options to the user
    for i, name in enumerate(address_book_names, start=1):
        print(f"{i}. {name}")
    
    # Get user input
    while True:
        try:
            message = int(input("Specify option: "))
            if 1 <= message <= len(address_book_names):
                return address_book_names[message - 1]
            else:
                print(f"Please specify a number between 1 and {len(address_book_names)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")
