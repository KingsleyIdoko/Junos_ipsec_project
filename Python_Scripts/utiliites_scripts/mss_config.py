
def input_integer(prompt):
    # Use a while loop to keep asking for input until a valid integer is entered
    while True:
        # Use the input() function to get the user input as a string
        user_input = input(prompt)
        # Use a try-except block to attempt to convert the user input to an integer
        try:
            # Use the int() function to convert the user input to an integer
            user_input = int(user_input)
            # If the conversion is successful, return the user input as an integer
            return user_input
        # If the conversion fails, catch the ValueError exception
        except ValueError:
            # Print an error message and ask the user to reenter the input
            print("Invalid input. Please enter an integer.")


