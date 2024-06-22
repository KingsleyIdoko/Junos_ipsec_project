from utiliites_scripts.commit import run_pyez_tasks
import sys

def main(target, config_class):
    """
    Main function to handle different operations like get, create, update, and delete.

    Args:
        target: Target device or group to run the task on.
        config_class: The configuration manager class.

    Returns:
        None
    """
    config = config_class()
    operation = config.operations()  # Get the operation interactively

    if operation == "get":
        response = config.get(interactive=True, target=target)
    else:
        payload = None
        if operation == "create":
            payload = config.create(target=target)
        elif operation == "update":
            payload = config.update(target=target)
        elif operation == "delete":
            payload = config.delete(target=target)
        else:
            print("Invalid operation specified. Please use 'get', 'create', 'update', or 'delete'.")
            sys.exit(1)

        if payload:
            run_pyez_tasks(config, payload)
