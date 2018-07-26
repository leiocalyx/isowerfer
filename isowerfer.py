#!/usr/bin/python3

import subprocess
import sys
import argparse
import getpass
import os
import atexit
import ipaddress
import socket
import time
import fcntl

def isowerferpath():
    return os.path.dirname(os.path.realpath(sys.argv[0]))

######################## some arguments can be defined here ############################

#change these to whatever suits you best
#unpacked iso location
unpackedpath =  isowerferpath() + "/preseediso/"
#Path to supermicro IPMI tool
smcipmi = isowerferpath() + "/SMCIPMITool"

#something to default to if no arguments are provided
#these two can be blank
subdomain = "ipmi"
domain = "bru"

#It's probably ADMIN on supermicro
ipmiusername = "ADMIN"

########################################################################################

parser = argparse.ArgumentParser(description='command line arguments')
parser.add_argument('-s','--srvr', help='server name, it will be used as hostname', required=True)
parser.add_argument('-ip','--ip', help='ip field')
parser.add_argument('-u','--subdomain', help='subdomain field')
parser.add_argument('-d','--domain', help='domain field')
inputargs = parser.parse_args()

srvinput = inputargs.srvr

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

if inputargs.ip:
    try:
        srvip = inputargs.ip
        ipaddress.ip_address(srvip)
    except ValueError as err:
        print(err)
        sys.exit(1)
else: 
    try:
        srvip = socket.gethostbyname(nslname)
    except Exception:
        print("Can't resolve ip, and no -ip argument present, closing...")
        sys.exit(1)

ipmipass = getpass.getpass('IPMI password is needed: ')

#editing the network template and preseed file
networktemplate = isowerferpath() + "/templates/network.template"
networkedited = unpackedpath + "/preseed/interfaces"
preseedtemplate = isowerferpath() + "/templates/preseed.template"
preseededited = unpackedpath + "/preseed/yggdrasil.seed"

def editfiles(filein, fileout, replacethis, withthis):
    try:
        fileedit = open(filein).read()
        for a, b in zip(replacethis, withthis):
            fileedit = fileedit.replace(a, b)
        filewrite = open(fileout, 'w+')
        filewrite.write(fileedit)
        filewrite.close()
    except:
        raise


#blocks execution of other instances of isowerfer from breaking stuff
lockfile = "/tmp/isowerfer.lock"
lockcheck = open(lockfile, "w+")
while True:
    try:
        fcntl.lockf(lockcheck, fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
    except BlockingIOError as err:
        expectederr = 11
        if err.errno == expectederr:
            print("Another isowerfer process is running, waiting for config files to be unlocked...")
            time.sleep(10)
            continue
        else:
            raise

editfiles(networktemplate, networkedited, ['ip_here', 'domain_here'], [srvip, domain])
editfiles(preseedtemplate, preseededited, ['unassignedhostname', 'unassigneddomain'], [srvinput, domain])

#generating .iso file
isowerferpid = os.getpid()
isofilepath = "/tmp/isowerfed" + str(isowerferpid) + ".iso"
subprocess.run('mkisofs -r -V isowerfed -cache-inodes -J -l -b isolinux/isolinux.bin -c boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o ' + isofilepath + ' ' + unpackedpath, shell=True)

#lock is lifted
fcntl.lockf(lockcheck, fcntl.LOCK_UN)


args = (smcipmi, ipmisrv, ipmiusername, ipmipass, "shell")
smshell = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE, bufsize=1, universal_newlines=True)

commands = ["vmwa dev2iso {}\n".format(isofilepath),
            "ipmi power bootoption 3\n",
            "ipmi power cycle 3\n",
            "sleep 643\n",
            "vmwa dev2stop\n",
            "vmwa status\n",
            "exit\n"
            ]

def commandipmi(a):
    smshell.stdin.write(a)

for c in commands: 
    commandipmi(c)
    
#this kills iso file on exit and tries to kill it after it is mounted.  
def removeiso():
    os.remove(isofilepath)

try:    
    atexit.register(removeiso)  
except:
    pass

for line in smshell.stdout:
    print(line)
    if "VM Plug-In OK!!" in line:
        os.remove(isofilepath)
        print("ISO file was successfully mounted, deleting " + isofilepath + "...")
smshell.wait()