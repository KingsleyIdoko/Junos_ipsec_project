import re


def get_valid_string(prompt="Enter a valid name: "):
    pattern = r'^[a-zA-Z0-9_* ]+$'
    while True:
        input_string = input(prompt)
        if re.match(pattern, input_string):
            words = input_string.split()
            if len(words) <= 5:
                return input_string  # Valid string, return it
            else:
                print("The string contains more than 5 words. Please try again.")
        else:
            print("Invalid input. Please ensure the string contains only alphanumeric characters, underscores, asterisks, and spaces.")


def get_valid_integer(prompt="Enter a number: "):
    while True:
        try:
            user_input = input(prompt)
            user_input_as_int = int(user_input)
            return user_input_as_int
        except ValueError:
            print("Invalid input. Please enter a valid Number.")