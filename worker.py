import socket
import threading
from forEachClient import WorkerForClient

class Worker(threading.Thread):
    def __init__(self, vhost, ip, port, documentRoots, log, checkDomain):
        threading.Thread.__init__(self)
        self.vhost = vhost
        self.ip = ip
        self.port = port
        self.documentRoots = documentRoots
        self.log = log
        self.checkDomain = checkDomain
        
    def run(self):
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.ip, self.port))
            s.listen()
            while True:
                conn, addr = s.accept()

                forClient = WorkerForClient(self.vhost, self.ip, self.port, self.documentRoots, conn, addr, self.log, self.checkDomain)
                forClient.start()
            


