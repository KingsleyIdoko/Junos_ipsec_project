from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff, pyez_rollback
from jnpr.junos.exception import RpcError, CommitError
from rich import print

def run_pyez_tasks(config, payload, data_format='xml'):
    response = config.nr.run(task=pyez_config, payload=payload, data_format=data_format)
    diff_result = config.nr.run(task=pyez_diff)
    need_commit = False
    for res in diff_result.values():
        if res.result:
            print(res.result)
            need_commit = True
        else:
            print("No Config Change: No Commit to Apply")
    
    if need_commit:
        while True:
            message = input("Enter 'yes' to commit, 'no' to abort: ").lower()
            if message in ['yes', 'y']:
                committed = config.nr.run(task=pyez_commit)
                print(committed)
                for res in committed.values():
                    if res.failed:
                        print(format_error(res.exception))
                    else:
                        print("Successfully deployed config")
                return response, committed
            elif message in ['no', 'n']:
                print("Running pyez_rollback task...")
                rolled_back = config.nr.run(task=pyez_rollback)
                print(rolled_back)
                print("Configuration abort initiated.")
                return response, rolled_back
            else:
                print("Invalid command. Please enter 'yes', 'y', 'no', or 'n'.")
    else:
        return response, None

def format_error(exception):
    if isinstance(exception, CommitError):
        return f"CommitError(message: {exception.message})"
    elif isinstance(exception, RpcError):
        return f"RpcError(message: {exception.message})"
    elif isinstance(exception, dict):
        return f"Error: {exception.get('message', str(exception))}"
    else:
        return str(exception)
