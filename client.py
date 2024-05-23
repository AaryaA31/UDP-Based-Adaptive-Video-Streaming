from queue import Queue
import xml.etree.ElementTree as ET
import time
import socket
import sys
import os
import threading

def send_data(sock, data):
    if isinstance(data, str):
        data = data.encode()  
    msg_length = integer_to_bytes(len(data))  
    sock.sendall(msg_length + data)  

def receive_data(sock):
    raw_msg_length = receive_all(sock, 4)  
    if not raw_msg_length:
        return None
    msg_length = bytes_to_integer(raw_msg_length)  
    return receive_all(sock, msg_length)  

def receive_all(sock, n):
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def integer_to_bytes(i):
    return i.to_bytes(4, byteorder='big')

def bytes_to_integer(b):
    return int.from_bytes(b, byteorder='big')

def calculate_new_bandwidth(old_bandwidth, measured_bandwidth, alpha):
    return alpha * measured_bandwidth + (1 - alpha) * old_bandwidth

def save_chunk_to_file(chunk_data, video_id, bitrate, chunk_num):
    tmp_dir = "tmp"
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)  

    filename = f"{video_id}-{bitrate}-{str(chunk_num).zfill(5)}.m4s"
    file_path = os.path.join(tmp_dir, filename)
    with open(file_path, "wb") as file:
        file.write(chunk_data)

def download_chunk(sock, video_id, bitrate, chunk_num, log_file, old_bandwidth, alpha):
    request_message = f"GET_CHUNK {video_id} {bitrate} {chunk_num}"
    send_data(sock, request_message)
    start_time = time.time()
    chunk_data = receive_data(sock)
    end_time = time.time()
    if chunk_data is None:
        print("Failed to receive chunk data.")
        return 0, old_bandwidth
    chunk_size = len(chunk_data)
    duration = end_time - start_time
    measured_bandwidth = (chunk_size * 8) / duration
    bandwidth = calculate_new_bandwidth(old_bandwidth, measured_bandwidth, alpha)
    filename = f"{video_id}-{bitrate}-{str(chunk_num).zfill(5)}.m4s"

    save_chunk_to_file(chunk_data, video_id, bitrate, chunk_num)

    log_entry = f"{start_time} {duration} {measured_bandwidth} {bandwidth} {bitrate} {filename}\n"
    print(log_entry)
    log_file.write(log_entry)
    log_file.flush()

    return measured_bandwidth, bandwidth

def client(server_address, server_port, video_id, alpha, chunks_queue):
    log_file_path = "log.txt"
    with open(log_file_path, "w") as log_file:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((server_address, server_port))
                send_data(sock, f"GET_MANIFEST {video_id}")
                manifest_data = receive_data(sock).decode()
                print(manifest_data)
                root = ET.fromstring(manifest_data)
                bitrates = sorted([int(representation.get('bandwidth')) for representation in root.iter('Representation')])
                bandwidth = 250000 
                 
                for chunk_num in range(30):  
                    filtered_bitrates = [bitrate for bitrate in bitrates if bitrate * 1.5 <= bandwidth]
                    suitable_bitrate = max(filtered_bitrates) if filtered_bitrates else min(bitrates)
                    
                    measured_bandwidth, bandwidth = download_chunk(sock, video_id, suitable_bitrate, chunk_num, log_file, bandwidth, alpha)
        except Exception as e:
            print(f"Client error: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python3 client.py <server_address> <server_port> <video_id> <alpha>")
        sys.exit(1)

    server_address = sys.argv[1]
    server_port = int(sys.argv[2])
    video_id = sys.argv[3]
    alpha = float(sys.argv[4])
    chunks_queue = Queue()
    client_thread = threading.Thread(target=client, args=(server_address, server_port, video_id, alpha, chunks_queue))
    client_thread.start()