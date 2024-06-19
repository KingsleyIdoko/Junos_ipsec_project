from nornir_pyez.plugins.tasks import pyez_config
from nornir_utils.plugins.functions import print_result

def run_task(task_name, target, config_class):
    manager = config_class()
    if target == "all":
        result = manager.nr.run(task=task_name)
    else:
        result = manager.nr.filter(name=target).run(task=task_name)
    print_result(result)

def main(target, config_class):
    config = config_class()
    operation = config.operations()  # Get the operation interactively

    if operation == "get":
        response = config.get(interactive=True, target=target)
    elif operation == "create":
        payload = config.create(target=target)
        if payload:
            run_task(lambda task: task.run(task=pyez_config, template_path=payload), target, config_class)
    elif operation == "update":
        payload = config.update(target=target)
        if payload:
            run_task(lambda task: task.run(task=pyez_config, template_path=payload), target, config_class)
    elif operation == "delete":
        payload = config.delete(target=target)
        if payload:
            run_task(lambda task: task.run(task=pyez_config, template_path=payload), target, config_class)
    else:
        print("Invalid operation specified. Please use 'get', 'create', 'update', or 'delete'.")
        sys.exit(1)