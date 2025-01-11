import socket
import threading
import time
import Msg
import AnsiFixer

# TODO: add more comments
# TODO: check if the randomly selected port numbers are okay/if it matters(same in server)
listen_udp_port = 5002  
buffer_size = 1024  # Size of each packet in bytes
offer_message = "offer"
timeout = 1  # Timeout for detecting end of UDP transfer in seconds

TCP = AnsiFixer.colorizeStr("[TCP]", AnsiFixer.BLUE)
UDP = AnsiFixer.colorizeStr("[UDP]", AnsiFixer.GREEN)
CLIENT = AnsiFixer.colorizeStr("[CLIENT]", AnsiFixer.MAGENTA)
ERROR = AnsiFixer.colorizeStr("[ERROR]", AnsiFixer.RED)

# TCP transfer 
def handle_tcp(server_ip, server_tcp_port, file_size):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    tcp_socket.connect((server_ip, server_tcp_port))
    tcp_socket.send(f"{file_size}\n".encode())

    start_time = time.time()
    bytes_received = 0
    while bytes_received < file_size:
        data = tcp_socket.recv(buffer_size)
        bytes_received += len(data)

    tcp_socket.close()
    elapsed_time = time.time() - start_time
    speed = (bytes_received * 8) / elapsed_time
    print(f"{TCP} transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second")

# UDP transfer
def handle_udp(server_ip, server_udp_port, file_size):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(timeout)

    byte_arr = Msg.RequestMsg().encode(file_size)
    udp_socket.sendto(byte_arr, (server_ip, server_udp_port))

    start_time = time.time()
    bytes_received = 0
    packets_received = 0
    packets_lost = 0
    timeout_happend = False
    last_packet_time = time.time()

    while bytes_received < file_size:
        try:
            data, _ = udp_socket.recvfrom(buffer_size)
            payload_msg = Msg.PayloadMsg().decode(data)
            bytes_received += len(data) - 4
            packets_received += 1
            last_packet_time = time.time()
            print(f"{UDP} Received packet {payload_msg.currentSegmentCount}")
        except socket.timeout:
            if time.time() - last_packet_time > timeout:
                timeout_happend = True
                break
            packets_lost += 1

    elapsed_time = time.time() - start_time
    speed = (bytes_received * 8) / elapsed_time
    if packets_received + packets_lost > 0:
        success_rate = (packets_received / (packets_received + packets_lost)) * 100
    else:
        success_rate = 0

    if not timeout_happend:
        print(f"{UDP} transfer finished, total time: {elapsed_time:.2f} seconds\n total speed: {speed:.2f} bits/second\n percentage of packets received successfully: {success_rate:.2f}%")
    else:
        print(f"{UDP} transfer TIMED OUT, total time: {elapsed_time:.2f} seconds\n total speed: {speed:.2f} bits/second\n percentage of packets received successfully: {success_rate:.2f}%")

def listen_for_offers():
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        udp_socket.bind(("0.0.0.0", listen_udp_port))
        print(f"{CLIENT} started, listening for offer requests...")

        while True:
            data, addr = udp_socket.recvfrom(buffer_size)
            offer_message = Msg.OfferMsg().decode(data)

            # error checking
            if offer_message.magic_cookie !=  Msg.offerMsgCookie:
                raise Exception("Invalid magic cookie")
            if offer_message.msg_type != Msg.offerMsgType:
                raise Exception("Invalid message type")

            print(f"{CLIENT} Received offer from {addr[0]}")
            return offer_message, addr[0]
    except Exception as e:
        print(f"{ERROR}: {e}")

def start_client():
    print (f"{CLIENT} Starting client...")
    file_size = int(input(f"{CLIENT} Enter file size (in bytes): "))
    tcp_connections = int(input(f"{CLIENT} Enter number of TCP connections: "))
    udp_connections = int(input(f"{CLIENT} Enter number of UDP connections: "))

    while True:
        offer_message, server_ip = listen_for_offers()

        threads = []

        for _ in range(tcp_connections): # adding a tcp connection per thread
            tcp_thread = threading.Thread(target=handle_tcp, args=(server_ip, offer_message.serverTCPPort, file_size))
            threads.append(tcp_thread)
            tcp_thread.start()

        for _ in range(udp_connections): # Adding a udp connection per thread
            udp_thread = threading.Thread(target=handle_udp, args=(server_ip, offer_message.serverUDPPort, file_size))
            threads.append(udp_thread)
            udp_thread.start()

        # wait for all threads to complete before listening to more offers
        for thread in threads:
            thread.join()

        print(f"{CLIENT} All transfers complete, listening to offer requests")

if __name__ == "__main__":
    start_client()