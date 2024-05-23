import xml.etree.ElementTree as ElementTree
import socket
import sys
import os
import struct

def transmit_message(connection, data):
    """Transmits a message over the specified socket connection. Converts data to bytes if it's a string and appends the message length as a 4-byte prefix."""
    if isinstance(data, str):
        data = data.encode()
    elif isinstance(data, bytes):
        pass
    else:
        raise ValueError("Data must be a byte sequence or a string")
    msg_length = integer_to_bytes(len(data))
    connection.sendall(msg_length + data)

def receive_message(connection):
    """Receives a message from the specified socket connection. Reads the 4-byte message length prefix and then retrieves the complete message."""
    raw_msg_length = receive_all(connection, 4)
    if not raw_msg_length:
        return None
    msg_length = bytes_to_integer(raw_msg_length)
    return receive_all(connection, msg_length)

def receive_all(connection, n):
    """Receives n bytes from the socket connection, ensuring that all bytes are received before returning."""
    data = bytearray()
    while len(data) < n:
        packet = connection.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def integer_to_bytes(i):
    """Converts an integer to a 4-byte big-endian byte sequence."""
    return i.to_bytes(4, byteorder='big')

def bytes_to_integer(b):
    """Converts a 4-byte big-endian byte sequence to an integer."""
    return int.from_bytes(b, byteorder='big')

def obtain_manifest_data(video_identifier):
    """Reads and returns the content of the manifest file for the specified video."""
    MANIFEST_FILE_PATH = f"data/{video_identifier}/manifest.mpd"
    with open(MANIFEST_FILE_PATH, 'rb') as file:
        return file.read()

def chunk_exists(video_identifier, bitrate, chunk_number):
    """Checks if the specified video chunk exists based on its parameters."""
    chunk_path = os.path.join("data", video_identifier, "chunks", f"{video_identifier}_{bitrate}_{chunk_number.zfill(5)}.m4s")
    return os.path.exists(chunk_path)

def obtain_chunk_data(video_identifier, bitrate, chunk_number):
    """Reads and returns the content of the specified video chunk if it exists, otherwise returns an error message."""
    chunk_path = os.path.join(video_identifier, "chunks", f"{video_identifier}_{bitrate}_{chunk_number.zfill(5)}.m4s")
    if os.path.exists(chunk_path):
        with open(chunk_path, 'rb') as file:
            return file.read()
    return "Chunk not found".encode()

def handle_client_connection(client_socket):
    """Handles the communication with a connected client. Processes client requests and sends appropriate responses."""
    try:
        while True:
            request = receive_message(client_socket).decode()
            if not request:
                break

            print(f"Received request: {request}")

            if request.startswith("GET_MANIFEST"):
                _, video_identifier = request.split()
                data = obtain_manifest_data(video_identifier)
                transmit_message(client_socket, data)
            elif request.startswith("GET_CHUNK"):
                _, video_identifier, bitrate, chunk_number = request.split()
                if chunk_exists(video_identifier, bitrate, chunk_number):
                    data = obtain_chunk_data(video_identifier, bitrate, chunk_number)
                    transmit_message(client_socket, data)
                else:
                    transmit_message(client_socket, "Chunk not found")
            else:
                transmit_message(client_socket, "Invalid request")
    finally:
        client_socket.close()

def initiate_server(listening_port):
    """Starts the server and listens for incoming client connections on the specified port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind(('', listening_port))
        server_socket.listen()
        print(f"Server listening on port {listening_port}")

        while True:
            client_socket, _ = server_socket.accept()
            print("Accepted connection from client")
            handle_client_connection(client_socket)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 server.py <listening_port>")
        sys.exit(1)

    listening_port = int(sys.argv[1])
    if 49152 <= listening_port <= 65535:
        initiate_server(listening_port)
    else:
        print("Error: listening_port must be between 49152 and 65535")
        sys.exit(1)
