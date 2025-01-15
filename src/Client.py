import socket
import threading
import time
import Msg
import AnsiFixer
import Stats

# TODO: add more comments
# TODO: check if the randomly selected port numbers are okay/if it matters(same in server)
listen_udp_port = 5002  
buffer_size = 5 + 16 + 1024  # Size of payload packet, 5 bytes for msg header, 16 bytes for MsgPayload header and 1024 bytes for payload
udp_timeout_ms = 1000  # Timeout for detecting end of UDP transfer in milliseconds

TCP = AnsiFixer.colorizeStr("[TCP]", AnsiFixer.BLUE)
UDP = AnsiFixer.colorizeStr("[UDP]", AnsiFixer.GREEN)
CLIENT = AnsiFixer.colorizeStr("[CLIENT]", AnsiFixer.MAGENTA)
ERROR = AnsiFixer.colorizeStr("[ERROR]", AnsiFixer.RED)
DUPLICATE = AnsiFixer.colorizeStr("DUPLICATE", AnsiFixer.RED)

# TCP transfer 
def handle_tcp(thread_num, server_ip, server_tcp_port, file_size):
    stats = Stats.Stats(thread_num, True, server_ip, server_tcp_port)
    stats.tcp_start_connection(file_size)

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    tcp_socket.connect((server_ip, server_tcp_port))
    tcp_socket.send(f"{file_size}\n".encode())

    bytes_received = 0
    while bytes_received < file_size:
        data = tcp_socket.recv(buffer_size)
        bytes_received += len(data)
        stats.tcp_got_packet(len(data))

    tcp_socket.close()
    stats.tcp_stop_connection()
    stats.print_tcp_report()

# UDP transfer
def handle_udp(thread_num, server_ip, server_udp_port, file_size):
    stats = Stats.Stats(thread_num, False, server_ip, server_udp_port)

    try:
        already_received = []

        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.settimeout(udp_timeout_ms / 1000)

        stats.udp_start_connection(file_size)

        byte_arr = Msg.RequestMsg().encode(file_size)
        udp_socket.sendto(byte_arr, (server_ip, server_udp_port))

        bytes_received = 0
        num_timeout = 0

        while bytes_received < file_size:
            try:
                data, _ = udp_socket.recvfrom(buffer_size)
                timeout = 0
                try:
                    payload_msg = Msg.PayloadMsg().decode(data)
                    stats.udp_got_packet(payload_msg)
                    if(payload_msg.currentSegmentCount in already_received):
                        # print(f"{UDP} Received packet {DUPLICATE} {payload_msg.currentSegmentCount}!")
                        continue

                    bytes_received += len(payload_msg.payload)
                    last_packet_time = time.time()
                    already_received.append(payload_msg.currentSegmentCount)
                    # print(f"{UDP} Received packet {payload_msg.currentSegmentCount} of {payload_msg.totalSegmentCount}, size {len(payload_msg.payload)}")
                except Exception as e:
                    stats.got_error(f"{UDP} {e}")
                    continue
            except socket.timeout:
                if(num_timeout >= 3):
                    # break if 3 timeouts in a row
                    break
                if time.time() - last_packet_time > timeout:
                    num_timeout += 1
        
        udp_socket.close()
    except Exception as e:
        stats.got_error(f"{UDP} {e}")
        stats.udp_stop_connection()
        stats.print_udp_report()
        return
        
    stats.udp_stop_connection()
    stats.print_udp_report()

def listen_for_offers():
    udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
    udp_socket.bind(("0.0.0.0", listen_udp_port))
    print(f"{CLIENT} started, listening for offer requests...")

    while True:
        data, addr = udp_socket.recvfrom(buffer_size)
        offer_message = Msg.OfferMsg().decode(data)

        # error checking
        if offer_message.magic_cookie !=  Msg.offerMsgCookie:
            # raise Exception("Invalid magic cookie")
            continue
        if offer_message.msg_type != Msg.offerMsgType:
            # raise Exception("Invalid message type")
            continue

        print(f"{CLIENT} Received offer from {addr[0]}")
        return offer_message, addr[0]

def start_client():
    print (f"{CLIENT} started")
    file_size = int(input(f"{CLIENT} Enter file size (in bytes): "))
    tcp_connections = int(input(f"{CLIENT} Enter number of TCP connections: "))
    udp_connections = int(input(f"{CLIENT} Enter number of UDP connections: "))

    while True:
        offer_message, server_ip = listen_for_offers()

        threads = []

        for i in range(tcp_connections): # adding a tcp connection per thread
            tcp_thread = threading.Thread(target=handle_tcp, args=(i, server_ip, offer_message.serverTCPPort, file_size))
            threads.append(tcp_thread)
            tcp_thread.start()

        for i in range(udp_connections): # Adding a udp connection per thread
            udp_thread = threading.Thread(target=handle_udp, args=(i, server_ip, offer_message.serverUDPPort, file_size))
            threads.append(udp_thread)
            udp_thread.start()

        # wait for all threads to complete before listening to more offers
        for thread in threads:
            thread.join()

        print(f"{CLIENT} All transfers complete, listening to offer requests")

        # TODO: uncomment to run continuously
        # return

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

team_name_ascii_art = AnsiFixer.colorizeStr(team_name_ascii_art, AnsiFixer.RED)

def print_ascii_art():
    print(team_name_ascii_art)

if __name__ == "__main__":
    try:
        print_ascii_art()
        start_client()
    except KeyboardInterrupt:
        print(f"\n{CLIENT} stopped")
        # TODO: print statistics to screen and file
        exit(0)