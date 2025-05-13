#!/usr/bin/python3

from os import listdir
from os.path import isfile, join
import gzip
import os
import shutil
from shutil import copyfile
import pprint
import argparse

def add_pkg_to_dict(pkgs_to_keep_per_repo, pkg_repo_line):
    pkg_name = pkg_repo_line.split('@', 1)[0]
    repo_name = pkg_repo_line.split('@', 1)[1]
    list_of_pkgs = pkgs_to_keep_per_repo.get(repo_name)
    if list_of_pkgs is None:
        list_of_pkgs = [pkg_name]
    else:
        list_of_pkgs.append(pkg_name)
    pkgs_to_keep_per_repo[repo_name] = list_of_pkgs

def nevra_to_name(nevra):
    nevr = nevra.rpartition(".")[0] # remove .arch
    nev = nevr.rpartition("-")[0] # remove -release
    return nev.rpartition("-")[0] # remove -epoch:version

def should_keep(pkg_full_nevra, pkg_nevra_list, keep_all_versions):
    if (not keep_all_versions):
        return pkg_full_nevra in pkg_nevra_list
    name = nevra_to_name(pkg_full_nevra)
    name_list = []
    for p in pkg_nevra_list:
        name_list.append(nevra_to_name(p))
    if name in name_list:
        return True
    else:
        return False

def solv_line_pkg_to_nevra(line):
    # remove ending new line
    pkg = line[:-1]
    # remove "=Pkg: " and make it a nevra
    pkg = pkg[6:].replace(' ', '-')
    s_spl = pkg.split("-")
    return "-".join(s_spl[:-1]) + '.' + s_spl[-1]

parser = argparse.ArgumentParser(description="Goes through all repos (expect for @System) in debugdata and removes all packages that are not present in solver.result or in testcase.t jobs.",
                                 epilog="Hint: If we have 2 different results (like picking older dependency in one run vs not in another) it is useful to combine both results in solver.result and minimize the debugdata.")

parser.add_argument("input_dir", help="Path to the rpms directory in debugdata to minimize")
parser.add_argument("output_dir", help="Directory name where the minimized debugdata will be written")
parser.add_argument("--keep-all-versions", action="store_true", help="Keep packages from solver.result and testcase.t jobs in all versions")
parser.add_argument("--keep-installed", action="store_true", help="In addition to packages from solver.result and testcase.t also keep packages from @System (installed)")

args = parser.parse_args()

onlyfiles = [f for f in listdir(args.input_dir) if isfile(join(args.input_dir, f))]

if os.path.exists(args.output_dir):
    shutil.rmtree(args.output_dir)
os.makedirs(args.output_dir)

repos = []
system_repo_pkgs = []
pkgs_to_keep_per_repo = {}
for f in onlyfiles:
    path_in = join(args.input_dir, f)
    path_out = join(args.output_dir, f)
    if f.endswith(".repo.gz") and f.endswith("@System.repo.gz"):
        repo_contents = []
        with gzip.open(join(str(args.input_dir), f), "rt") as fin:
            repo_contents = fin.readlines()
        for line in repo_contents:
            if line.startswith("=Pkg: "):
                system_repo_pkgs.append(solv_line_pkg_to_nevra(line))

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
                if line.startswith("erase "):
                    pkg_repo_line = (line[6:])
                    add_pkg_to_dict(pkgs_to_keep_per_repo, pkg_repo_line)
                if line.startswith("reinstall "):
                    # remove reinstall
                    pkgs_repo = (line[10:])
                    installed_pkg_line = pkgs_repo.split(' ')[0]
                    reinstall_pkg_line = pkgs_repo.split(' ')[1]
                    add_pkg_to_dict(pkgs_to_keep_per_repo, installed_pkg_line)
                    add_pkg_to_dict(pkgs_to_keep_per_repo, reinstall_pkg_line)
                if line.startswith("upgrade "):
                    # remove upgrade
                    pkgs_repo = (line[8:])
                    from_upgraded_pkg_line = pkgs_repo.split(' ')[0]
                    to_upgrade_pkg_line = pkgs_repo.split(' ')[1]
                    add_pkg_to_dict(pkgs_to_keep_per_repo, from_upgraded_pkg_line)
                    add_pkg_to_dict(pkgs_to_keep_per_repo, to_upgrade_pkg_line)
                if line.startswith("problem "):
                    # For example:
                    # problem 3f47a1e1 info package sssd-ipa-2.9.4-3.el8_10.x86_64 requires sssd-common = 2.9.4-3.el8_10, but none of the providers can be installed
                    # problem 3f47a1e1 solution 008890f1 allow libsss_autofs-2.7.3-4.el8_7.1.x86_64@@System
                    problem_type = (line[17:])
                    if problem_type.startswith("solution "):
                        pkgs_repo = (problem_type[24:])
                        add_pkg_to_dict(pkgs_to_keep_per_repo, pkgs_repo)

    if f.endswith("testcase.t"):
        with open(path_in, "rt") as fin:
            result = fin.readlines()
            for line in result:
                # remove ending new line
                line = line[:-1]
                if line.startswith("job "):
                    elems = line.split(" ")
                    for elem in elems:
                        if '@' in elem:
                            add_pkg_to_dict(pkgs_to_keep_per_repo, elem)

    copyfile(path_in, path_out)

print("Keeping pkgs:")
pprint.pprint(pkgs_to_keep_per_repo)

print("Processing repo:")
for repo in repos:
    pruned_repo = []
    # remove ending ".repo.gz"
    repo_name = repo[:-8]
    if pkgs_to_keep_per_repo.get(repo_name) is None:
        continue
    print(repo_name)
    repo_contents = []
    with gzip.open(join(str(args.input_dir), repo), "rt") as fin:
        repo_contents = fin.readlines()
    keep = True
    for line in repo_contents:
        if line.startswith("=Sum:"):
            continue
        # Drop everthing after vendor: Tim and all files
        if line.startswith("=Vnd:"):
            keep = False
        if line.startswith("=Pkg: "):
            pkg = solv_line_pkg_to_nevra(line)
            keep = False
            keep |= should_keep(pkg, pkgs_to_keep_per_repo[repo_name], args.keep_all_versions)
            if (args.keep_installed):
                keep |= should_keep(pkg, system_repo_pkgs, args.keep_all_versions)
        if keep:
            pruned_repo.append(line)

    with gzip.open(join(args.output_dir, repo), "wt") as fout:
        for line in pruned_repo:
            fout.write(line)
