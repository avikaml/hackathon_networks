import socket
import threading
import time

# TODO: add more comments
# TODO: check if the randomly selected port numbers are okay/if it matters(same in server)
udp_port = 5002  
buffer_size = 1024  # Size of each packet in bytes
offer_message = "offer"
timeout = 1  # Timeout for detecting end of UDP transfer in seconds

# TCP transfer 
def handle_tcp(server_ip, file_size):
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.connect((server_ip, 5003))  # Change to new port
    tcp_socket.send(f"{file_size}\n".encode())

    start_time = time.time()
    bytes_received = 0
    while bytes_received < file_size:
        data = tcp_socket.recv(buffer_size)
        bytes_received += len(data)

    tcp_socket.close()
    elapsed_time = time.time() - start_time
    speed = (bytes_received * 8) / elapsed_time
    print(f"TCP transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second")

# UDP transfer
def handle_udp(server_ip, file_size):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.settimeout(timeout)
    udp_socket.sendto(f"REQUEST {file_size}".encode(), (server_ip, udp_port))

    start_time = time.time()
    bytes_received = 0
    packets_received = 0
    packets_lost = 0
    last_packet_time = time.time()

    while bytes_received < file_size:
        try:
            data, _ = udp_socket.recvfrom(buffer_size)
            sequence_number = int.from_bytes(data[:4], 'big')
            bytes_received += len(data) - 4
            packets_received += 1
            last_packet_time = time.time()
            print(f"[UDP] Received packet {sequence_number}")
        except socket.timeout:
            if time.time() - last_packet_time > timeout:
                break
            packets_lost += 1

    elapsed_time = time.time() - start_time
    speed = (bytes_received * 8) / elapsed_time
    if packets_received + packets_lost > 0:
        success_rate = (packets_received / (packets_received + packets_lost)) * 100
    else:
        success_rate = 0
    print(f"UDP transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second, percentage of packets received successfully: {success_rate:.2f}%")

def listen_for_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", udp_port))
    print("Client started, listening for offer requests...")

    while True:
        data, addr = udp_socket.recvfrom(buffer_size)
        if data.decode() == offer_message:
            print(f"Received offer from {addr[0]}")
            return addr[0]

def start_client():
    server_ip = listen_for_offers()
    file_size = int(input("Enter file size (in bytes): "))
    tcp_connections = int(input("Enter number of TCP connections: "))
    udp_connections = int(input("Enter number of UDP connections: "))
    threads = []

    for _ in range(tcp_connections): # adding a tcp connection per thread
        tcp_thread = threading.Thread(target=handle_tcp, args=(server_ip, file_size))
        threads.append(tcp_thread)
        tcp_thread.start()

    for _ in range(udp_connections): # Adding a udp connection per thread
        udp_thread = threading.Thread(target=handle_udp, args=(server_ip, file_size))
        threads.append(udp_thread)
        udp_thread.start()

    # wait for all threads to complete before listening to more offers
    for thread in threads:
        thread.join()

    print("All transfers complete, listening to offer requests")

if __name__ == "__main__":
    start_client()