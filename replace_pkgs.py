#!/usr/bin/python3

import sys

if len(sys.argv) != 4:
    print("""We replace "<packages>" string in testcase_template_path with correctly formated list_of_pkgs_path
We output mytestcase.t with inserted pkgs

Usage: replace_pkgs.py <testcase_template_path> <list_of_pkgs_path> <out_testcase>
""")
    sys.exit(0)
#input file
fin = open(sys.argv[1], "rt")
finpkgs = open(sys.argv[2], "rt")
pkgs = finpkgs.read()
finpkgs.close()
pkgs = pkgs.replace("\n", " ")
#output file to write the result to
fout = open(sys.argv[3], "wt")
#for each line in the input file
for line in fin:
	#read replace the string and write to output file
	fout.write(line.replace('<packages>', pkgs))
#close input and output files
fin.close()
fout.close()
