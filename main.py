import json
import os
from worker import Worker


def createFile(vhost, log):
    myFile = open(log + "/" + vhost + ".log", "w+")
    myFile.close()


def main() :
    with open('config.json') as json_file:
        data = json.load(json_file)

        
        
        if not os.path.exists(data['log']):
            os.mkdir(data['log'])
        
        checkDomain = dict()
        documentRoots = dict()
        createFile('error', data['log'])
        for server in data['server']:
            createFile(server['vhost'], data['log'])
            
            curr = (server['ip'], server['port'])
            if checkDomain.__contains__(curr):
                checkDomain[curr].add(server['vhost'])
            else:
                emptySet = set()
                emptySet.add(server['vhost'])
                checkDomain[curr] = emptySet
            
            documentRoots[server['vhost']] = server['documentroot']


        
        used = set()
        for server in data['server']:
            curr = (server['ip'], server['port'])

            if curr not in used:
                used.add(curr)
                worker = Worker(server['vhost'], server['ip'], server['port'], documentRoots, data['log'], checkDomain)
                worker.start()


if __name__ == "__main__" :
    main()