#!/usr/bin/python3

import sys
import fnmatch
import subprocess
import gzip

def print_help_and_exit():
    print("""Goes through all packages in specified repo (reponame.repo.gz) and in place
removes all packages whose name fnmatches expr..

Usage: remove_matching_pkgs.py <repo_path> <fnmatch expr>

After it is finished it runs testsolv to verify results.
""")
    sys.exit(0)

if len(sys.argv) != 3:
    print_help_and_exit()

repo_path = sys.argv[1]
fnmatch_expr = sys.argv[2]

if not repo_path or not fnmatch_expr:
    print_help_and_exit()


repo_contents = []
with gzip.open(repo_path, "rt") as fin:
    repo_contents = fin.readlines()

pruned_repo = []
drop = False
for line in repo_contents:
    if line.startswith("=Pkg: "):
        # remove "=Pkg: "
        pkg_line = (line[6:])
        drop = False
        drop |= fnmatch.fnmatch(pkg_line, fnmatch_expr)
        if drop:
            print("Dropping: " + str(line[:-1]))
    if not drop:
        pruned_repo.append(line)


with gzip.open(repo_path, "wt") as fout:
    for line in pruned_repo:
        fout.write(line)

subprocess.run(["testsolv", "testcase.t"])

response = input("Keep? (y/N): ").strip().lower()

if response in ['y']:
    print("Done!")
else:
    with gzip.open(repo_path, "wt") as fout:
        for line in repo_contents:
            fout.write(line)
    print("Reverted.")
