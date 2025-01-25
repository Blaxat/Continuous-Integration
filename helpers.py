import socket

def communicate(host, port, message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(message.encode('utf-8'))
        response = s.recv(1024)
        return response.decode('utf-8')
    except socket.error as e:
        print(f"Communication error with {host}:{port} - {e}")
