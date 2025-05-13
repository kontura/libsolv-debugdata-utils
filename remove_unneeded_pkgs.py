#!/usr/bin/python3

import sys
import subprocess
import gzip

def print_help_and_exit():
    print("""Goes through all packages in specified repo (reponame.repo.gz) tries to
remove it and runs testsolv testcase.t if the exit code is 0 (the result matches solver.result)
the package is not needed and is removed. If the result is different the package is kept.

Pass -m at the end to enable manual mode, where after each package the user is presented
with testsolv output and can either confirm or deny the removal.

Usage: remove_unneeded_pkgs.py <repo_path> [-m]

""")
    sys.exit(0)

if len(sys.argv) > 3:
    print_help_and_exit()

repo_path = sys.argv[1]

manual = ""
if len(sys.argv) == 3:
    manual = sys.argv[2]

print(manual)

def testsolv_passes():
    result = subprocess.run(["testsolv", "testcase.t"], capture_output=True, text=True)
    if result.returncode != 0:
        return False
    if result.stdout != "":
        return False
    if result.stderr != "":
        return False
    return True


def remove_pkgs():
    repo_contents = []
    with gzip.open(repo_path, "rt") as fin:
        repo_contents = fin.readlines()

    removed_pkgs = 0
    pruned_repo = []
    keep = True
    for line_i in range(len(repo_contents)):
        line = repo_contents[line_i]
        if line.startswith("=Pkg: "):
            print(line[:-1])
            repo_without_this_pkg = pruned_repo
            # find start of next package
            next_package_start_line = -1
            for i in range(line_i+1, len(repo_contents)):
                l = repo_contents[i]
                if l.startswith("=Pkg: "):
                    next_package_start_line = i
                    break
            repo_without_this_pkg = repo_without_this_pkg + repo_contents[next_package_start_line:]
            with gzip.open(repo_path, "wt") as fout:
                for l in repo_without_this_pkg:
                    fout.write(l)
            result = subprocess.run(["testsolv", "testcase.t"], capture_output=True, text=True)
            if manual:
                print(result.stdout)
                print(result.stderr)
                response = input("Remove this pkg? (y/N): ").strip().lower()
                if response == 'y':
                    keep = False
                    removed_pkgs += 1
                else:
                    keep = True
            else:
                if result.returncode:
                    keep = True
                else:
                    removed_pkgs += 1
                    keep = False

        if keep:
            pruned_repo.append(line)


    with gzip.open(repo_path, "wt") as fout:
        for line in pruned_repo:
            fout.write(line)

    print("removed pkgs: " + str(removed_pkgs))

testsolv_passes()
# remove unneeded packages
remove_pkgs()
