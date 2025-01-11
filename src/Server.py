import socket
import threading
import time
import os
import random
from Msg import OfferMsg, RequestMsg, PayloadMsg

# TODO: add more comments

# TODO: check if port numbers are okay/if it matters
tcp_port = random.randint(5003, 60000)  # Randomly selected port number for TCP
udp_port = random.randint(5003, 60000)  # Randomly selected port number for UDP
if tcp_port == udp_port:
    udp_port += 1

constant_udp_port = 5002
buffer_size = 1024  # Size of each packet in bytes
# TODO: broadcast interval should be 1 second
broadcast_interval = 10  # Interval for sending broadcast offers in seconds
offer_message = "offer"
server_ip = "0.0.0.0"  # the server's IP address

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
    try:
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(("0.0.0.0", udp_port))

        print(f"[UDP] Listening on port {udp_port}")

        while True:
            data, addr = udp_socket.recvfrom(buffer_size)
    
            request = RequestMsg()
            try:
                request.decode(data)
            except Exception as e:
                print(f"Error: {e}")
                continue

            if request is not None:
                file_size = request.fileSize
                print(f"[UDP] Received request for {file_size} bytes from {addr}")
                start_time = time.time()

                total_segment_count = (file_size + buffer_size - 1) // buffer_size

                bytes_sent = 0
                current_segment_count = 0
                while current_segment_count < total_segment_count:
                    chunk = os.urandom(min(buffer_size - 4, file_size - bytes_sent))
                    payload_msg = PayloadMsg()
                    byte_arr = payload_msg.encode(total_segment_count, current_segment_count, chunk)

                    udp_socket.sendto(byte_arr, addr)

                    bytes_sent += len(chunk)
                    current_segment_count += 1
                    print(f"[UDP] Sent packet {current_segment_count} of {total_segment_count} to {addr}")
                
                elapsed_time = time.time() - start_time
                print(f"[UDP] Finished sending {file_size} bytes in {elapsed_time:.2f} seconds")

    except Exception as e:
        print(f"Error: {e}")

# announces broadcast offers
def broadcast_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    offer_message = OfferMsg()
    byte_arr = offer_message.encode(udp_port, tcp_port)

    while True:
        udp_socket.sendto(byte_arr, ('<broadcast>', constant_udp_port))  # Change to new port
        print(f"Broadcasting offer on port UDP: {udp_port}, TCP: {tcp_port}")
        time.sleep(broadcast_interval)

def start_server():
    # TCP setup
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((server_ip, tcp_port))
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