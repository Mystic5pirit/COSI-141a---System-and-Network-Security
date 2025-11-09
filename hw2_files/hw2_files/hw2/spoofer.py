from scapy.all import IP, UDP, send

def send_packet(src_ip, dst_ip, dst_port, payload):

    # We want to make sure that the payload is in bytes
    if isinstance(payload, str):
        payload = payload.encode('utf-8')

    # We want to check that the payload isn't too big and exit gracefully if it is
    if len(payload) > 150:
        print("Payload is too large, exiting gracefully")
        return

    # Make the IP layer
    ip_layer = IP(src=src_ip, dst=dst_ip)

    # Make the UDP layer
    udp_layer = UDP(dport=dst_port)

    # Assemble the packet
    packet = ip_layer / udp_layer / payload

    # Send the packet
    send(packet)