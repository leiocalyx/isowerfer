# Isowerfer
Requirements:
Linux with Python3, mkisofs SMCIPMITool, and an unpacked Ubuntu ISO (tested on 16.04)

Isowerfer changes several parameters in order to customize ubuntu installation. 
You will need to make your own preseed and txt.cfg file, though the parts which the script interacts with are provided. 

After customising the preseed and the network file, an iso image is generated and mounted via IPMI, and the server is rebooted to install from the cd. 
If all Ubuntu unattend parameters were specified correctly - you should have an installed system in 10 minutes or less. 

The network.template provided is for a two interface bond with a vlan. 
The preseed.template is provided as an example, and should be customised according to your needs. 
