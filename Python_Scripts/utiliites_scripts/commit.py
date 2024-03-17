from nornir_pyez.plugins.tasks import pyez_config, pyez_commit, pyez_diff, pyez_rollback

def run_pyez_tasks(self, payload, data_format):
    response = self.nr.run(task=pyez_config, payload=payload, data_format=data_format)
    for res in response.values():  
        print(res.result)
    diff_result = self.nr.run(task=pyez_diff)
    need_commit = False

    for res in diff_result.values():
        if res.result:  
            print(res.result)
            need_commit = True
        else:
            print("No Config Change: No Commit to Apply")
    if need_commit:
        try:
            message = int(input("Enter 1 to commit, 0 to rollback: "))
        except ValueError:
            print("Invalid input. Assuming rollback.")
            message = 0
        if message == 1:
            committed = self.nr.run(task=pyez_commit)
            for res in committed.values():
                print(res.result)
            return response, committed
        else:
            rolled_back = self.nr.run(task=pyez_rollback)
            print("Configuration rollback initiated.")
            return None
    else:
        return response, None
