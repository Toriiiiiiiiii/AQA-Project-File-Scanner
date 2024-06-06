import socket
import threading
import sqlite3
import json
import datetime

from util import *
from scan_SERVER import *

def loadRulesFromJson(path: str) -> None:
    databaseConn = sqlite3.connect("SEARCHLIGHT CYBER DATABASE.db")
    databaseCurs = databaseConn.cursor()
    
    with open(path, "r") as f:
        contents = f.read()
        
    jsonContents = json.loads(contents)
    if type(jsonContents) != list:
        return
    
    for rule in jsonContents:
        databaseCurs.execute(f"INSERT INTO ruleFile(ruleName, ruleDescription, ruleSuspicion) VALUES ('{rule['name']}', '{rule['desc']}', {rule['susp']})")
        ruleID = databaseCurs.lastrowid
        
        for pattern in rule["patterns"]:
            databaseCurs.execute(f"INSERT INTO patternFile(ruleID, patternType, patternText) VALUES ({ruleID}, '{pattern['type']}', '{pattern['value']}')")
    
    databaseConn.commit()
    databaseConn.close()
   

def is_open(sock: socket.socket):
    try:
        sock.setblocking(0)
        data = sock.recv(16)
        if len(data) == 0:
            return False
        
    except BlockingIOError:
        return True
    
    except ConnectionResetError:
        return False
    
    except Exception as e:
        return True
    
    return True

class Server:
    def __init__(self, port) -> None:
        self.host = "127.0.0.1"
        self.port = port
        self.isRunning = True
        self.mainThread = threading.Thread(target=self.runServer)
        
        self.threads = []
        self.connectedAddresses = []
        self.connections = []
        
        print(f"[INFO] Listening on port {self.port}")
        
        # self.mainThread.daemon = True
        self.mainThread.start()
        
    def manageConnection(self, conn, addr):
        conn.setblocking(True)
        dbConn = sqlite3.connect("SEARCHLIGHT CYBER DATABASE.db")
        dbCurs = dbConn.cursor()
        
        while self.isRunning:
            try:
                data = conn.recv(1024)
            except:
                break
            
            if not data:
                return
            
            body = bytes.decode(data, "ascii")
            bodyJSON = json.loads(body)
            
            if bodyJSON["type"] == "sql_query":
                try:
                    result = dbCurs.execute(bodyJSON["body"]).fetchall()
                except Exception as e:
                    print(e)
                    result = str(e)
                
                result = {"type": "sql_response", "body": result, "query": bodyJSON["body"]}
                conn.sendall(str( json.dumps(result) ).encode("ascii"))
                dbConn.commit()
                
            if bodyJSON["type"] == "sql_desc":
                try:
                    result = dbCurs.execute(bodyJSON["body"]).description
                except Exception as e:
                    result = e
                
                result = {"type": "sql_response", "body": result}
                conn.sendall(str( json.dumps(result) ).encode("ascii"))
                dbConn.commit()
                
            if bodyJSON["type"] == "scan_request":
                userID = bodyJSON["user_id"]
                
                dbCurs.execute(f"INSERT INTO targetFile(fileName, customerID, scanDate) VALUES('{bodyJSON['filename']}', {userID}, '{datetime.date.today().strftime('%d/%m/%Y')}')")
                dbConn.commit()
                
                targetID = dbCurs.lastrowid
                
                transferStartMessage = conn.recv(1024)
                transferStartJSON = json.loads( bytes.decode(transferStartMessage, "ascii") )
                fileSize = transferStartJSON["body"]
                
                fileContents = conn.recv(fileSize)
                fileScanner = FileScan(fileContents, dbConn, dbCurs)
                
                ruleMatches = {}
                suspicion = 0
                for match in fileScanner.matches:
                    ruleRecord = dbCurs.execute(f"SELECT * FROM ruleFile WHERE ruleID={match.ruleID}").fetchone()
                    ruleMatches[ruleRecord[1]] = [match.occurances, ruleRecord[2]]
                    suspicion += ruleRecord[3]
                    
                    dbCurs.execute(f"INSERT INTO scanFile(targetID, ruleID, patternID, numFound) VALUES({targetID}, {match.ruleID}, {match.patternID}, {match.occurances})")
                    dbConn.commit()
                
                conn.sendall(json.dumps( {"type": "scan_done", "body": ruleMatches, "susp": suspicion} ).encode("ascii"))
            
        conn.close()
        dbConn.close()
        
    def runServer(self) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.socket.setblocking(False)
        
        while self.isRunning:
            conn = None
            while not conn:
                try:
                    conn, addr = self.socket.accept()
                    self.connectedAddresses.append(addr)
                    self.connections.append(conn)
                except KeyboardInterrupt:
                    self.isRunning = False
                    return
                except Exception as e:
                    if self.isRunning:
                        continue
                    else:
                        return
            
            connectionThread = threading.Thread(target=self.manageConnection, args=[conn, addr])
            connectionThread.start()
            self.threads.append(connectionThread)
            
        self.socket.close()
            
if __name__ == "__main__":
    server = Server(7777)
    
    while server.isRunning:
        consoleCmd = input("> ").lower()
        
        if consoleCmd == "quit":
            print("Waiting for clients to disconnect before quitting...")
            
            server.isRunning = False
            for index, thread in enumerate(server.threads):
                if thread.is_alive():
                    conn = server.connections[index]
                    
                    toSend = {"type": "signal", "body": "quit"}
                    conn.sendall(str.encode( json.dumps(toSend), "ascii" ))
                    
                    thread.join()
                    
            if server.mainThread.is_alive():
                server.mainThread.join()
                
            print("Clients disconnected! Quitting...")
                
        if consoleCmd == "sql":
            while True:
                print("== SQL Input : Type 'q' to go back. ==")
                command = input("sql > ")
                
                if command.lower() == "q": break
                elif command.lower() == "commit": databaseConn.commit()
                else:
                    try:
                        for record in databaseCurs.execute(command).fetchall():
                            print(record)
                            
                        print()
                    except Exception as e:
                        print(e)
                
        if consoleCmd in ["loadrules", "load"]:
            path = input("Rule Path > ")
            loadRulesFromJson(path)            
                
        if consoleCmd in ["connections", "conns"]:
            print("== Connections ==")
            for index, address in enumerate(server.connectedAddresses):
                if is_open(server.connections[index]):
                    print(f"\-> ipv4 : {address[0]}, port : {address[1]}")