#!/usr/bin/python3

import sys
import subprocess
import gzip

def solv_line_pkg_to_nevra(line):
    # remove ending new line
    pkg = line[:-1]
    # remove "=Pkg: " and make it a nevra
    pkg = pkg[6:].replace(' ', '-')
    s_spl = pkg.split("-")
    return "-".join(s_spl[:-1]) + '.' + s_spl[-1]

def nevra_to_namearch(nevra):
    arch =  nevra.rpartition(".")[2]

    nevr = nevra.rpartition(".")[0] # remove .arch
    nev = nevr.rpartition("-")[0] # remove -release
    name =  nev.rpartition("-")[0] # remove -epoch:version

    return name + "." + arch

def print_help_and_exit():
    print("""Goes through all packages in specified repo (reponame.repo.gz) and keeps
only the latest version for given name.arch

Usage: keep_only_latest.py <repo_path>

After it is finished it runs testsolv to verify results.
""")
    sys.exit(0)

if len(sys.argv) != 2:
    print_help_and_exit()

repo_path = sys.argv[1]

if not repo_path:
    print_help_and_exit()

repo_contents = []
with gzip.open(repo_path, "rt") as fin:
    repo_contents = fin.readlines()

name_arch = {}

for line in repo_contents:
    if line.startswith("=Pkg: "):
        nevra = solv_line_pkg_to_nevra(line)
        na = nevra_to_namearch(nevra)
        if not na in name_arch:
            name_arch[na] = []
        name_arch[na].append(nevra)

pruned_repo = []
keep = True
for line in repo_contents:
    if line.startswith("=Pkg: "):
        nevra = solv_line_pkg_to_nevra(line)
        na = nevra_to_namearch(nevra)
        name_arch[na].sort()
        name_arch[na].reverse()
        latest_nevras = name_arch[na][:2]
        keep = nevra in latest_nevras
    if keep:
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
