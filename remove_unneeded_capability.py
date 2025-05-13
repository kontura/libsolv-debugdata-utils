#!/usr/bin/python3

import sys
import subprocess
import gzip

def testsolv_passes():
    result = subprocess.run(["testsolv", "testcase.t"], capture_output=True, text=True)
    return not result.returncode

def print_help_and_exit():
    print("""Goes through all packages in specified repo (reponame.repo.gz) tries to
remove each of their specified capability (Req, Prv, Obs, Con...), runs testsolv testcase.t if the exit code is 0 (the result matches solver.result)
the require is not needed and is removed. If the result is different the capability is kept.

Usage: remove_unneeded_capability.py <repo_path> <capability>

""")
    sys.exit(0)

if len(sys.argv) != 3:
    print_help_and_exit()

repo_path = sys.argv[1]
capability = sys.argv[2]

if not testsolv_passes():
    print("testsolv doesn't pass in this directory")
    sys.exit(0)

repo_contents = []
with gzip.open(repo_path, "rt") as fin:
    repo_contents = fin.readlines()

removed_capabilities = 0
pruned_repo = []
in_reqs = False
for line_i in range(len(repo_contents)):
    keep = True
    line = repo_contents[line_i]

    if line.startswith("-"+capability+":"):
        # Don't keep empty capabilities
        prev_line = pruned_repo[-1]
        if prev_line.startswith("+"+capability+":"):
            pruned_repo.pop()
            keep = False

        in_reqs = False

    if in_reqs:
        # create repo without this line
        repo_without_this_req = pruned_repo
        repo_without_this_req = repo_without_this_req + repo_contents[line_i+1:]

        with gzip.open(repo_path, "wt") as fout:
            for l in repo_without_this_req:
                fout.write(l)

        if testsolv_passes():
            removed_capabilities += 1
            keep = False
        else:
            keep = True

    if line.startswith("+"+capability+":"):
        print("Entering on line: " + str(line_i))
        in_reqs = True

    if keep:
        pruned_repo.append(line)


with gzip.open(repo_path, "wt") as fout:
    for line in pruned_repo:
        fout.write(line)

print("removed reqs: " + str(removed_capabilities))
