#!/usr/bin/python3

import subprocess
import sys
import argparse
import getpass

######################## some arguments can be defined here ############################

#something to default to if no arguments are provided
#these two can be blank
subdomain = "ipmi"
domain = "bru"

#It's probably ADMIN on supermicro
ipmiusername = "ADMIN"

#network configuration file locations
networktemplate = "/isowerfer/templates/network.template"
networkedited = "/isowerfer/preseediso/preseed/interfaces"

#preseed file locations
preseedtemplate = "/isowerfer/templates/preseed.template"
preseededited = "/isowerfer/preseediso/preseed/yggdrasil.seed"

#iso generating script
makeiso = "/isowerfer/makeiso"

#Path to supermicro IPMI tool
smcipmi = "/isowerfer/SMCIPMITool"

########################################################################################

parser = argparse.ArgumentParser(description='now with arguments')
parser.add_argument('-s','--srvr', help='server name, it will be used as hostname', required=True)
parser.add_argument('-p','--passw', help='password field')
parser.add_argument('-u','--subdomain', help='subdomain field')
parser.add_argument('-d','--domain', help='domain field')
inputargs = parser.parse_args()

srvinput = inputargs.srvr

if inputargs.passw:
    ipmipass = inputargs.passw
else:
	ipmipass = getpass.getpass('IPMI password is needed:')

if inputargs.subdomain:
    subdomain = inputargs.subdomain

if inputargs.domain:
    domain = inputargs.domain

if (subdomain and domain):
  ipmisrv = subdomain + "." + srvinput + "." + domain
elif subdomain:
  ipmisrv = subdomain + "." + srvinput
elif domain:
  ipmisrv = srvinput + "." + domain
else:
  ipmisrv = srvinput


if domain:
    nslname = srvinput + "." + domain
else:
    nslname = srvinput

#getting ip based on servername provided via nslookup
nsl = subprocess.check_output(["nslookup", nslname])
srvip = nsl.split(b"Address: ")[1].decode("utf8").strip()
#TODO: add a better mechanism for when the dns name isn't found.

#editing the network template
try:
    netedit = open(networktemplate).read()
    netedit = netedit.replace('ip_here', srvip)
    netedit = netedit.replace('domain_here', domain)
    netfile = open(networkedited, 'w')
    netfile.write(netedit)
    netfile.close()
except Exception:
    pass

#editing preseed file
try:
    preedit = open(preseedtemplate).read()
    preedit = preedit.replace('unassignedhostname', srvinput)
    preedit = preedit.replace('unassigneddomain', domain)
    prefile = open(preseededited, 'w')
    prefile.write(preedit)
    prefile.close()
except Exception:
    pass

#generating .iso file
subprocess.run(makeiso)

#maybe server name and password parameters?
args = (smcipmi, ipmisrv, ipmiusername, ipmipass, "shell")
smshell = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)

#this can be for looped, can it not?
#choose what to mount later, maybe
smshell.stdin.write(b'vmwa dev2iso /isowerfer/isofiles/ubuntuseed.iso\n')
smshell.stdin.flush()

smshell.stdin.write(b'ipmi power bootoption 3\n')
smshell.stdin.flush()

smshell.stdin.write(b'ipmi power cycle 3\n')
smshell.stdin.flush()

#everything is expected to complete in less than 643 seconds.
smshell.stdin.write(b'sleep 643\n')
smshell.stdin.flush()

#unmounting iso
smshell.stdin.write(b'vmwa dev2stop\n')
smshell.stdin.flush()
smshell.stdin.write(b'vmwa status\n')
smshell.stdin.flush()
smshell.stdin.write(b'exit\n')
smshell.stdin.flush()

for line in smshell.stdout:
    print(line)
smshell.wait()
