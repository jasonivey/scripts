import socket

HOST = 'nas4a.ut1'        # The remote host
PORT = 24211              # The same port as used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
msg = r'/raid1/dwarchive/c/cyg.5016.12/2017/01/01/400003369_export_117000109_1-1_1170001101303.zdw.xz'
s.sendall(msg)
data = s.recv(1024)
s.close()
print 'Received: ', repr(data)
