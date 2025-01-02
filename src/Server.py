import socket
import threading
import time
import os

# TODO: add more comments

# TODO: check if port numbers are okay/if it matters
tcp_port = 5003  # Current tcp port number
udp_port = 5001
buffer_size = 1024  # Size of each packet in bytes
broadcast_interval = 1  # Interval for sending broadcast offers in seconds
offer_message = "offer"
server_ip = "172.1.0.4"  # the server's IP address

def handle_tcp(client_socket):
    print("[TCP] Client connected")

    file_size = int(client_socket.recv(buffer_size).decode().strip())
    start_time = time.time()

    bytes_sent = 0
    while bytes_sent < file_size:
        chunk = os.urandom(min(buffer_size, file_size - bytes_sent))
        client_socket.send(chunk)
        bytes_sent += len(chunk)

    client_socket.close()
    elapsed_time = time.time() - start_time
    print(f"[TCP] Finished sending {file_size} bytes in {elapsed_time:.2f} seconds")

def handle_udp():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", udp_port))

    print(f"[UDP] Listening on port {udp_port}")

    while True:
        data, addr = udp_socket.recvfrom(buffer_size)
        if data.decode().startswith("REQUEST"):
            file_size = int(data.decode().split()[1])
            print(f"[UDP] Starting data transfer to {addr}")
            start_time = time.time()

            bytes_sent = 0
            sequence_number = 0
            while bytes_sent < file_size:
                chunk = os.urandom(min(buffer_size - 4, file_size - bytes_sent))
                packet = sequence_number.to_bytes(4, 'big') + chunk
                udp_socket.sendto(packet, addr)
                bytes_sent += len(chunk)
                sequence_number += 1
                print(f"[UDP] Sent packet {sequence_number} to {addr}")

            elapsed_time = time.time() - start_time
            print(f"[UDP] Finished sending {file_size} bytes in {elapsed_time:.2f} seconds")

# announces broadcast offers
def broadcast_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        udp_socket.sendto(offer_message.encode(), ('<broadcast>', 5002))  # Change to new port
        print(f"Broadcasting offer on port 5002")
        time.sleep(broadcast_interval)

def start_server():
    # TCP setup
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(("0.0.0.0", tcp_port))
    tcp_socket.listen(5)

    print(f"Server started, listening on IP address {server_ip}")
    print(f"[TCP] Listening on port {tcp_port}")

    # UDP setup(in separate thread)
    udp_thread = threading.Thread(target=handle_udp, daemon=True)
    udp_thread.start()

    # Broadcast offers(in separate thread)
    broadcast_thread = threading.Thread(target=broadcast_offers, daemon=True)
    broadcast_thread.start()
    # Accepting the TCP cons 
    while True:
        client_socket, _ = tcp_socket.accept()
        tcp_thread = threading.Thread(target=handle_tcp, args=(client_socket,))
        tcp_thread.start()

if __name__ == "__main__":
    start_server()