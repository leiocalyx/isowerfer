#!/usr/bin/python3

import subprocess

interfaces = subprocess.check_output(["ip", "l"]).decode("utf-8")
interfaces = interfaces.splitlines()

#this kills list numbers
int = [a[3:150] for a in interfaces]

ints = []
for line in int:
 if line.startswith("en"):
  if "NO-CARRIER" not in line:
   ints.append(line.split(':')[0])

i = open("/etc/network/interfaces").read()
i = i.replace('interface0', ints[0])
i = i.replace('interface1', ints[1])
f = open("/etc/network/interfaces", 'w')
f.write(i)
f.close()

