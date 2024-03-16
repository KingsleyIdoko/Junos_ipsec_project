    
def address_book(addressbook_name, address_name, ipv4_address, zone):
    print(addressbook_name)
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
    if isinstance(address_books, dict):
        address_books = [address_books]
    address_book_items = []
    for book in address_books:
        for key, value in book.items():
            address_book_items.append((value, key))
    address_book_items.append(("create new zone", "subnet"))
    for i, (value, key) in enumerate(address_book_items, start=1):
        print(f"{i}. {value}: {key}")
    while True:
        try:
            message = int(input("Specify option: "))
            if message == len(address_book_items):
                create_zone()  
                create_address_book() 
                return "New zone and address book created", None  
            elif 1 <= message < len(address_book_items):
                selected_zone, address_book_name = address_book_items[message - 1]
                return address_book_name, selected_zone
            else:
                print(f"Please specify a number between 1 and {len(address_book_items)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")


def create_zone():
    print("Creating new zone...")
    # Implement zone creation logic here

def create_address_book():
    print("Creating new address book...")
    # Implement address book creation logic here
