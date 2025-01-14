import time
import AnsiFixer
import Msg
import os
import time

TCP = AnsiFixer.colorizeStr("[TCP]", AnsiFixer.BLUE)
UDP = AnsiFixer.colorizeStr("[UDP]", AnsiFixer.GREEN)
CLIENT = AnsiFixer.colorizeStr("[CLIENT]", AnsiFixer.MAGENTA)
ERROR = AnsiFixer.colorizeStr("[ERROR]", AnsiFixer.RED)
THREAD_TCP = AnsiFixer.colorizeStr("[THREAD TCP]", AnsiFixer.BLUE)
THREAD_UDP = AnsiFixer.colorizeStr("[THREAD UDP]", AnsiFixer.GREEN)
BREAK = AnsiFixer.colorizeStr("--------------------------------------------------\n", AnsiFixer.YELLOW)

class Stats:
    def __init__(self, thread_num, i_am_tcp, server_ip, server_port):
        self.thread_num = thread_num
        self.i_am_tcp = i_am_tcp

        # get current hour and minute, minute and second as string
        start_time = time.strftime("%Hh-%Mm-%Ss", time.localtime())
        os.makedirs(f"stats", exist_ok=True)
        os.makedirs(f"stats/{start_time}", exist_ok=True)

        if i_am_tcp:
            self.file = open(f"stats/{start_time}/tcp_thread_{thread_num}.txt", "a")
            self.file.write(BREAK);
            self.file.write(BREAK);
            self.file.write(f"Start time: {start_time}\n")
            self.file.write(f"{TCP} thread({thread_num}):\nserver_up: {server_ip}\nserver_port: {server_port}\n")
        else:
            self.file = open(f"stats/{start_time}/udp_thread_{thread_num}.txt", "a")
            self.file.write(BREAK);
            self.file.write(BREAK);
            self.file.write(f"Start time: {start_time}\n")
            self.file.write(f"{UDP} thread({thread_num}):\nserver_up: {server_ip}\nserver_port: {server_port}\n")

    def print_msg(self, msg):
        self.file.write(msg + "\n")
        print(msg)

    def tcp_start_connection(self, file_size):
        self.tcp_start_time = time.time()
        self.tcp_file_size = file_size
        self.tcp_bytes_received = 0

    def tcp_stop_connection(self):
        self.tcp_stop_time = time.time()
        self.tcp_time = self.tcp_stop_time - self.tcp_start_time

    def tcp_got_packet(self, num_of_bytes):
        self.tcp_bytes_received += num_of_bytes

    def print_tcp_report(self):
        self.print_msg(f"{THREAD_TCP} {self.thread_num} {TCP} received {self.tcp_bytes_received} bytes in {self.tcp_time:.5f} seconds")

    def udp_start_connection(self, file_size):
        self.udp_start_time = time.time()
        self.udp_file_size = file_size
        self.udp_bytes_received = 0
        self.udp_waiting_for = []
        self.udp_packets_out_of_order = 0
        self.udp_packets_duplicate = 0
        self.udp_last_segment_count = 0
        self.udp_total_segment_count = 0

    def udp_stop_connection(self):
        self.udp_stop_time = time.time()
        self.udp_time = self.udp_stop_time - self.udp_start_time

        self.udp_packets_lost = len(self.udp_waiting_for)
    
    def udp_got_packet(self, payload_msg):

        if payload_msg.currentSegmentCount == 1:
            self.udp_waiting_for = list(range(1, payload_msg.totalSegmentCount + 1))
        
        if payload_msg.currentSegmentCount in self.udp_waiting_for:
            self.udp_waiting_for.remove(payload_msg.currentSegmentCount)
            self.udp_bytes_received += len(payload_msg.payload)

            if payload_msg.currentSegmentCount != self.udp_last_segment_count + 1:
                # got packet out of order
                self.udp_packets_out_of_order += 1
        else:
            # got duplicate packet
            self.udp_packets_duplicate += 1

        self.udp_last_segment_count = payload_msg.currentSegmentCount
        self.udp_total_segment_count = payload_msg.totalSegmentCount

    def print_udp_report(self):
        self.print_msg(f"{THREAD_UDP} {self.thread_num}: received of {self.udp_bytes_received} bytes in {self.udp_time:.5f} seconds")

        prec_lost = len(self.udp_waiting_for) / self.udp_total_segment_count * 100
        self.print_msg(f"{THREAD_UDP} {self.thread_num}: lost {self.udp_packets_lost} packets ({prec_lost:.2f}%)")

        perc_out_of_order = self.udp_packets_out_of_order / self.udp_total_segment_count * 100
        self.print_msg(f"{THREAD_UDP} {self.thread_num}: received {self.udp_packets_out_of_order} packets out of order ({perc_out_of_order:.2f}%)")

        perc_duplicate = self.udp_packets_duplicate / self.udp_total_segment_count * 100
        self.print_msg(f"{THREAD_UDP} {self.thread_num}: received {self.udp_packets_duplicate} duplicate packets ({perc_duplicate:.2f}%)")

        perc_bytes_lost = (self.udp_file_size - self.udp_bytes_received) / self.udp_file_size * 100
        self.print_msg(f"{THREAD_UDP} {self.thread_num}: lost {self.udp_file_size - self.udp_bytes_received} bytes ({perc_bytes_lost:.2f}%)")

    def got_error(self, msg):
        if self.i_am_tcp:
            self.print_msg(f"{ERROR} in {THREAD_TCP} {self.thread_num}: received {msg}")
        else:
            self.print_msg(f"{ERROR} in {THREAD_UDP} {self.thread_num}: received {msg}")