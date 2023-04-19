#!/usr/bin/python3

import sys
from os import listdir
from os.path import isfile, join
import gzip
import os
import shutil
from shutil import copyfile

def add_pkg_to_dict(pkgs_to_keep_per_repo, pkg_repo_line):
    pkg_name = pkg_repo_line.split('@', 1)[0]
    repo_name = pkg_repo_line.split('@', 1)[1]
    list_of_pkgs = pkgs_to_keep_per_repo.get(repo_name)
    if list_of_pkgs is None:
        list_of_pkgs = [pkg_name]
    else:
        list_of_pkgs.append(pkg_name)
    pkgs_to_keep_per_repo[repo_name] = list_of_pkgs


if len(sys.argv) != 3:
    print("""Goes through all repos (expect for @System) in debugdata and removes all packages
that are not present in solver.result.

Usage: minimize_debugdata.py <debugdata_path_rpms> <output_debugdata_rpms_path>
""")
    sys.exit(0)

onlyfiles = [f for f in listdir(sys.argv[1]) if isfile(join(sys.argv[1], f))]

if os.path.exists(sys.argv[2]):
    shutil.rmtree(sys.argv[2])
os.makedirs(sys.argv[2])

repos = []
pkgs_to_keep_per_repo = {}
for f in onlyfiles:
    path_in = join(sys.argv[1], f)
    path_out = join(sys.argv[2], f)
    if f.endswith(".repo.gz") and not f.endswith("@System.repo.gz"):
        repos.append(f)
        continue
    if f.endswith("solver.result"):
        with open(path_in, "rt") as fin:
            result = fin.readlines()
            for line in result:
                # remove ending new line
                line = line[:-1]
                # TODO(amatej): This just handles install for now
                if line.startswith("install "):
                    # remove install
                    pkg_repo_line = (line[8:])
                    add_pkg_to_dict(pkgs_to_keep_per_repo, pkg_repo_line)

                if line.startswith("reinstall "):
                    # remove reinstall
                    pkgs_repo = (line[10:])
                    installed_pkg_line = pkgs_repo.split(' ')[0]
                    reinstall_pkg_line = pkgs_repo.split(' ')[1]
                    add_pkg_to_dict(pkgs_to_keep_per_repo, installed_pkg_line)
                    add_pkg_to_dict(pkgs_to_keep_per_repo, reinstall_pkg_line)
    if f.endswith("testcase.t"):
        with open(path_in, "rt") as fin:
            result = fin.readlines()
            for line in result:
                if line.startswith("job "):
                    elems = line.split(" ")
                    for elem in elems:
                        if '@' in elem:
                            add_pkg_to_dict(pkgs_to_keep_per_repo, elem)

    copyfile(path_in, path_out)

print("Keeping pkgs:")
print(pkgs_to_keep_per_repo)

print("Processing repo:")
for repo in repos:
    pruned_repo = []
    repo_name = repo.split('.')[0]
    if pkgs_to_keep_per_repo.get(repo_name) is None:
        continue
    print(repo_name)
    repo_contents = []
    with gzip.open(join(sys.argv[1], repo), "rt") as fin:
        repo_contents = fin.readlines()
    # remove first line: "=Ver: 3.0"
    #del repo_contents[0]
    keep = True
    for line in repo_contents:
        if line.startswith("=Pkg: "):
            # remove ending new line
            pkg = line[:-1]
            # remove "=Pkg: " and make it a nevra
            pkg = pkg[6:].replace(' ', '-')
            s_spl = pkg.split("-")
            pkg = "-".join(s_spl[:-1]) + '.' + s_spl[-1]
            if pkg in pkgs_to_keep_per_repo[repo_name]:
                keep = True
            else:
                keep = False
        if keep:
            pruned_repo.append(line)

    with gzip.open(join(sys.argv[2], repo), "wt") as fout:
        for line in pruned_repo:
            fout.write(line)
