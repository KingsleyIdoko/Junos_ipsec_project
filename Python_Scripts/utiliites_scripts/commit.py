def commit_func(response):
    for res in response:
    print(response[res].result)
    diff_result = self.nr.run(task=pyez_diff)
    for res in diff_result:
        if diff_result[res].result is None:
            print("No Config Change")
            return
        print(diff_result[res].result)
        committed = self.nr.run(task=pyez_commit)
        for res1 in committed:
            print(committed[res1].result)
