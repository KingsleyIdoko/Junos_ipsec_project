from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff, pyez_rollback
from jnpr.junos.exception import RpcError, CommitError

def run_pyez_tasks(self, payload, data_format='xml'):
    response = self.nr.run(task=pyez_config, payload=payload, data_format=data_format)
    print_diff_result = False

    for res in response.values():
        if res.result:
            print_diff_result = True

    if print_diff_result:
        diff_result = self.nr.run(task=pyez_diff)
        for res in diff_result.values():
            if res.result:
                print(res.result)
        need_commit = True
    else:
        print("No Config Change: No Commit to Apply")
        need_commit = False
    
    if need_commit:
        while True:
            message = input("Enter 'yes' to commit, 'no' to abort: ").lower()
            if message in ['yes', 'y']:
                committed = self.nr.run(task=pyez_commit)
                commit_successful = True
                for res in committed.values():
                    if res.failed:
                        commit_successful = False
                        print(format_error(res.exception))
                    else:
                        print("Successfully deployed config")
                if commit_successful:
                    return response, committed
            elif message in ['no', 'n']:
                rolled_back = self.nr.run(task=pyez_rollback)
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
        # Handle dictionary-based exceptions if any
        return f"Error: {exception.get('message', str(exception))}"
    else:
        return str(exception)
