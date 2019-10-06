import socket
import threading
import magic
from datetime import datetime


def writeIntoLog(direct, date_time, userIp, domain, myFile, statusCode, size, userAgent):
    f = open(direct, "a")
    currInfo = '[' + date_time + '] '
    currInfo += userIp + ' '
    currInfo += domain + ' '
    currInfo += myFile + ' '
    currInfo += statusCode + ' '
    currInfo += size + ' '
    currInfo += userAgent + '\r\n'
    f.write(currInfo)
    f.close()


class WorkerForClient(threading.Thread):
    def __init__(self, vhost, ip, port, documentRoots, conn, addr, log, checkDomain):
        threading.Thread.__init__(self)
        self.vhost = vhost
        self.ip = ip
        self.port = port
        self.documentRoots = documentRoots
        self.conn = conn
        self.addr = addr
        self.log = log
        self.checkDomain = checkDomain

    def run(self):

        with self.conn:
            request = b''
            while True:
                currRequest = self.conn.recv(1024)
                request += currRequest
                if len(currRequest) < 1024:
                    break

            decodedData = request.decode()
            arr = decodedData.split('\r\n')

            methodArr = arr[0].split(' ')
            method = methodArr[0]
            myFile = methodArr[1].split('?')[0]
            myFile = myFile.replace('%20', ' ')

            date = datetime.now()
            date_time = date.strftime("%a %b %-d %H:%M:%S %Y")
            userIp = self.addr[0]
            domain = ''
            userAgent = ''
            connection = ''
            rangeVal = ''
            etagVal = ''

            for header in arr:
                if header.find('Host:') != -1:
                    domain = header[header.find('Host:') + 6:]
                    domain = domain.split(':')[0]
                elif header.find('User-Agent:') != -1:
                    userAgent = header[header.find('User-Agent:') + 12:]
                elif header.find('Connection:') != -1:
                    connection = header[header.find('Connection:') + 12:]
                elif header.find('Range: bytes=') != -1:
                    rangeVal = header[header.find('Range: bytes=') + 13:]
                elif header.find('host:') != -1:
                    domain = header[header.find('host:') + 6:]
                    domain = domain.split(':')[0]
                elif header.find('If-None-Match:') != -1:
                    etagVal = header[header.find('If-None-Match:') + 15:]
            
            
            header = ''
            currResponse = b''
            if not domain in self.checkDomain[(self.ip, self.port)]:
                header = 'HTTP/1.1 404 Not Found\r\n'
                currResponse = 'REQUESTED DOMAIN NOT FOUND\r\n'
                header += 'Content-Length: ' + str(len(currResponse)) + '\n\n'
                
                writeIntoLog(self.log + '/error.log', date_time, userIp, domain, myFile, '404', str(len(currResponse)), userAgent)
                self.conn.send((header + currResponse).encode())
                return


            statusCode = '200'
            try:
                mfile = open(self.documentRoots[domain] + myFile,'rb')
                currResponse = mfile.read()
                mfile.close()

                if rangeVal != '':
                    currArr = rangeVal.split('-')
                    statusCode = '206'
                    if currArr[1] != '':
                        if int(currArr[0]) > int(currArr[1]):
                            header = 'HTTP/1.1 416 Requested Range Not Satisfiable status\n\n'
                            writeIntoLog(self.log + '/error.log', date_time, userIp, domain, myFile, '416', str(len(currResponse)), userAgent)
                            self.conn.send(header.encode())
                            return

                        currResponse = currResponse[int(currArr[0]):int(currArr[1]) + 1]
                    else:
                        currResponse = currResponse[int(currArr[0]):]


                mime = magic.Magic(mime=True)
                mimetype = str(mime.from_file(self.documentRoots[domain] + myFile))

                #to have css in html
                if userAgent.find('Chrome') != -1 or userAgent.find('Mozilla') != -1:
                    if myFile.endswith('.css'):
                        mimetype = 'text/css'

                if etagVal == str(currResponse.__hash__()):
                    header = 'HTTP/1.1 304 Not Modified \n\n'
                    writeIntoLog(self.log + '/' + domain + '.log', date_time, userIp, domain, myFile, '304', '0', userAgent)
                    self.conn.send(header.encode())
                    return

                header = 'HTTP/1.1 ' + statusCode + ' OK\r\n'
                header += 'Host:' + domain + '\r\n'
                header += 'Server: My_Server\r\n'
                header += 'Date: ' + date_time + '\r\n'
                header += 'Content-Length: ' + str(len(currResponse)) + '\r\n'
                header += 'Content-Type: ' + mimetype + '\r\n'
                header += 'ETag: ' + str(currResponse.__hash__()) + ' \r\n'
                header += 'Accept-Ranges: bytes\r\n'
                header += 'Connection: keep-alive\r\n'
                header += 'Keep-Alive: 5\n\n'

            except Exception as e:
                print(e)
 
            
            writeIntoLog(self.log + "/" + domain + ".log", date_time, userIp, domain, myFile, statusCode, str(len(currResponse)), userAgent)
            if method == 'GET':
                response = header.encode()
                response += currResponse
            elif method == 'HEAD':
                response = header.encode()

            self.conn.sendall(response)





