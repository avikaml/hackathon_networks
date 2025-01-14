import socket
import threading
import time
import os
import random
from Msg import OfferMsg, RequestMsg, PayloadMsg
import AnsiFixer
import math

TCP = AnsiFixer.colorizeStr("[TCP]", AnsiFixer.BLUE)
UDP = AnsiFixer.colorizeStr("[UDP]", AnsiFixer.GREEN)
SERVER = AnsiFixer.colorizeStr("[SERVER]", AnsiFixer.MAGENTA)
ERROR = AnsiFixer.colorizeStr("[ERROR]", AnsiFixer.RED)

# TODO: add more comments

# TODO: check if port numbers are okay/if it matters
tcp_port = random.randint(5003, 60000)  # Randomly selected port number for TCP
udp_port = random.randint(5003, 60000)  # Randomly selected port number for UDP
if tcp_port == udp_port:
    udp_port += 1

constant_udp_port = 5002
buffer_size = 1024  # Size of each packet in bytes
# TODO: broadcast interval should be 1 second
broadcast_interval = 1  # Interval for sending broadcast offers in seconds
offer_message = "offer"
server_ip = "0.0.0.0"  # the server's IP address
udp_threads = []
tcp_backlog = 100

def handle_tcp(client_socket):
    print(f"{TCP} Client connected")

    file_size = int(client_socket.recv(buffer_size).decode().strip())
    start_time = time.time()

    bytes_sent = 0
    while bytes_sent < file_size:
        chunk = os.urandom(min(buffer_size, file_size - bytes_sent))
        client_socket.send(chunk)
        bytes_sent += len(chunk)

    client_socket.close()
    elapsed_time = time.time() - start_time
    print(f"{TCP} Finished sending {file_size} bytes in {elapsed_time:.2f} seconds")

def handle_udp(request, addr):
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # udp_socket.bind(("0.0.0.0", udp_port))
    
    file_size = request.fileSize
    print(f"{UDP} Received request for {file_size} bytes from {addr}")
    start_time = time.time()

    total_segment_count = math.ceil(file_size / buffer_size)
    if(file_size < buffer_size):
        total_segment_count = 1

    bytes_sent = 0
    current_segment_count = 1
    while current_segment_count <= total_segment_count:
        chunk = os.urandom(min(buffer_size, file_size - bytes_sent))
        payload_msg = PayloadMsg()
        byte_arr = payload_msg.encode(total_segment_count, current_segment_count, chunk)

        # (!!!) start for testing (!!!)
        # # simulate packet loss
        # if current_segment_count % 3 == 0:
        #     current_segment_count += 1
        # else:
        #     udp_socket.sendto(byte_arr, addr)

        #     # simulate duplicate packet
        #     if current_segment_count % 2 == 0:
        #         udp_socket.sendto(byte_arr, addr)

        #     bytes_sent += len(chunk)
        #     print(f"{UDP} Sent packet {current_segment_count} of {total_segment_count} to {addr}, size {len(chunk)}")
        #     current_segment_count += 1
        # (!!!) end for testing (!!!)
    
        udp_socket.sendto(byte_arr, addr)

        bytes_sent += len(chunk)
        # print(f"{UDP} Sent packet {current_segment_count} of {total_segment_count} to {addr}, size {len(chunk)}")
        current_segment_count += 1

    elapsed_time = time.time() - start_time
    print(f"{UDP} Finished sending {file_size} bytes in {elapsed_time:.2f} seconds")


def listen_udp():
    print(f"{UDP} Listening on port {udp_port}")

    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.bind(("0.0.0.0", udp_port))

    while True:
        data, addr = udp_socket.recvfrom(buffer_size)
        request = RequestMsg()
        try:
            request.decode(data)
        except Exception as e:
            print(f"Error: {e}")
            continue

        if request is not None:
            udp_thread = threading.Thread(target=handle_udp, args=(request, addr,), daemon=True)
            udp_threads.append(udp_thread)
            udp_thread.start()

# announces broadcast offers
def broadcast_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    offer_message = OfferMsg()
    byte_arr = offer_message.encode(udp_port, tcp_port)

    while True:
        udp_socket.sendto(byte_arr, ('<broadcast>', constant_udp_port))  # Change to new port
        print(f"{SERVER} Broadcasting offer on port UDP: {udp_port}, TCP: {tcp_port}")
        time.sleep(broadcast_interval)

def start_server():
    # TCP setup
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind((server_ip, tcp_port))
    tcp_socket.listen(tcp_backlog)

    print(f"{SERVER} started, listening on IP address {server_ip}")
    print(f"{TCP} Listening on port {tcp_port}")

    # Broadcast offers(in separate thread)
    broadcast_thread = threading.Thread(target=broadcast_offers, daemon=True)
    broadcast_thread.start()

    # Listen for UDP requests
    udp_thread = threading.Thread(target=listen_udp, daemon=True)
    udp_thread.start()

    # Accepting the TCP cons 
    while True:
        client_socket, _ = tcp_socket.accept()
        tcp_thread = threading.Thread(target=handle_tcp, args=(client_socket,))
        tcp_thread.start()

team_name_ascii_art = '''
 /$$$$$$$                  /$$       /$$   /$$             /$$        
| $$__  $$                | $$      | $$  | $$            | $$        
| $$  \ $$  /$$$$$$   /$$$$$$$      | $$  | $$  /$$$$$$  /$$$$$$      
| $$$$$$$/ /$$__  $$ /$$__  $$      | $$$$$$$$ /$$__  $$|_  $$_/      
| $$__  $$| $$$$$$$$| $$  | $$      | $$__  $$| $$  \ $$  | $$        
| $$  \ $$| $$_____/| $$  | $$      | $$  | $$| $$  | $$  | $$ /$$    
| $$  | $$|  $$$$$$$|  $$$$$$$      | $$  | $$|  $$$$$$/  |  $$$$/    
|__/  |__/ \_______/ \_______/      |__/  |__/ \______/    \___/      
                                                                      
                                                                      
                                                                      
  /$$$$$$  /$$       /$$ /$$ /$$                                      
 /$$__  $$| $$      |__/| $$|__/                                      
| $$  \__/| $$$$$$$  /$$| $$ /$$                                      
| $$      | $$__  $$| $$| $$| $$                                      
| $$      | $$  \ $$| $$| $$| $$                                      
| $$    $$| $$  | $$| $$| $$| $$                                      
|  $$$$$$/| $$  | $$| $$| $$| $$                                      
 \______/ |__/  |__/|__/|__/|__/                                      
                                                                      
                                                                      
                                                                      
 /$$$$$$$                        /$$                                  
| $$__  $$                      | $$                                  
| $$  \ $$  /$$$$$$  /$$   /$$ /$$$$$$    /$$$$$$   /$$$$$$   /$$$$$$$
| $$$$$$$/ /$$__  $$| $$  | $$|_  $$_/   /$$__  $$ /$$__  $$ /$$_____/
| $$__  $$| $$  \ $$| $$  | $$  | $$    | $$$$$$$$| $$  \__/|  $$$$$$ 
| $$  \ $$| $$  | $$| $$  | $$  | $$ /$$| $$_____/| $$       \____  $$
| $$  | $$|  $$$$$$/|  $$$$$$/  |  $$$$/|  $$$$$$$| $$       /$$$$$$$/
|__/  |__/ \______/  \______/    \___/   \_______/|__/      |_______/ 


⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡾⠃⠀⠀⠀⠀⠀⠀⠰⣶⡀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡿⠁⣴⠇⠀⠀⠀⠀⠸⣦⠈⢿⡄⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⡇⢸⡏⢰⡇⠀⠀⢸⡆⢸⡆⢸⡇⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡇⠘⣧⡈⠃⢰⡆⠘⢁⣼⠁⣸⡇⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣄⠘⠃⠀⢸⡇⠀⠘⠁⣰⡟⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠃⠀⠀⢸⡇⠀⠀⠘⠋⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠃⠀⠀⠀⠀⠀⠀⠀
⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
⠀⢸⣿⣟⠉⢻⡟⠉⢻⡟⠉⣻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
⠀⢸⣿⣿⣷⣿⣿⣶⣿⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀
⠀⠈⠉⠉⢉⣉⣉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⣉⣉⡉⠉⠉⠁⠀
⠀⠀⠀⠀⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠉⠀⠀⠀⠀


'''

team_name_ascii_art = AnsiFixer.colorizeStr(team_name_ascii_art, AnsiFixer.BLUE)

def print_ascii_art():
    print(team_name_ascii_art)

if __name__ == "__main__":
    try:
        print_ascii_art()
        start_server()
    except KeyboardInterrupt:
        print(f"\n{SERVER} stopped")
        # TODO: print statistics to screen and file
        exit(0)