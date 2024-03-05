def select_prefix(prefixes):
    # Create a message that displays the options and prompts the user to enter a number
    message = ""
    for i, prefix in enumerate(prefixes):
        message += f"{i + 1}. {prefix['name']} ({prefix['ip-prefix']})\n"
    message += "Enter a number: "

    # Use a while loop to keep asking the user for input
    while True:
        # Use the input() function to get the user's input as a string
        user_input = input(message)

        # Convert the input to an integer and check if it is a valid index for the prefixes list
        try:
            index = int(user_input) - 1
            if 0 <= index < len(prefixes):
                # Return the corresponding element from the prefixes list
                return prefixes[index]
            else:
                # Print an error message if the input is out of range
                print("Invalid input. Please enter a number between 1 and", len(prefixes))
                # Ask the user to select a correct number again
                print("Please select a correct number from the list.")
        except ValueError:
            # Print an error message if the input is not a number
            print("Invalid input. Please enter a number.")
            # Ask the user to select a correct number again
            print("Please select a correct number from the list.")



# Define the list of dictionaries


# Define the function that takes the list of dictionaries as an argument
def select_nat_type(dictionaries):
    # Create a message that displays the options and prompts the user to enter a number
    message = "Select Nat Type:\n"
    for i, dictionary in enumerate(dictionaries):
        message += f"{i + 1}. {list(dictionary.keys())[0]}\n"
    message += "Enter a number: "

    # Use a while loop to keep asking the user for input
    while True:
        # Use the input() function to get the user's input as a string
        user_input = input(message)

        # Convert the input to an integer and check if it is a valid option for the nat type
        try:
            index = int(user_input) - 1
            if 0 <= index < len(dictionaries):
                # Return the corresponding dictionary from the list of dictionaries
                return dictionaries[index]
            else:
                # Print an error message if the input is out of range
                print("Invalid input. Please enter a number between 1 and", len(dictionaries))
        except ValueError:
            # Print an error message if the input is not a number
            print("Invalid input. Please enter a number.")


