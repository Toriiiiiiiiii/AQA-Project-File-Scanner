import socket
import json
import threading
import time

from generalizedDatabaseInterface_CLIENT import *
from util import *

HOST = "127.0.0.1"  # The server's hostname or IP address
PORT = 7777  # The port used by the server

class Client:
    def __init__(self, host, port) -> None:
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))
        
        self.isAlive = True
        self.listenerThread = threading.Thread(target=self.listenForDisconnectSignal)
        self.listenerThread.start()
        
        self.log = []
    
    def send(self, data):
        if type(data) != bytes:
            data = data.encode("ascii")
            
        self.sock.sendall(data)
    
    def recieve(self):
        result = self.sock.recv(1024)
        body = json.loads(bytes.decode(result, "ascii"))
        
        self.log.append(body)
        return body
    
    def getLastLog(self):
        if len(self.log) == 0:
            return
        
        return self.log[len(self.log) - 1]
    
    def sendQuery(self, query: str):
        body = {"type": "sql_query", "body": query}
        self.sock.sendall( json.dumps(body).encode("ascii") )
    
        bodyJSON = self.getLastLog()
        
        while not bodyJSON or bodyJSON["type"] != "sql_response" or bodyJSON["query"] != query:
            bodyJSON = self.getLastLog()
            
        return bodyJSON["body"]
    
    def describe(self, query: str):
        body = {"type": "sql_desc", "body": query}
        self.sock.sendall( json.dumps(body).encode("ascii") )
        
        bodyJSON = self.getLastLog()
        
        while not bodyJSON or bodyJSON["type"] != "sql_response":
            bodyJSON = self.getLastLog()
            
        return bodyJSON["body"]
    
    def listenForDisconnectSignal(self):
        self.sock.setblocking(1)
        while self.isAlive: 
            try:             
                self.recieve()
            except:
                self.isAlive = False
                break
                      
            if {"type": "signal", "body": "quit"} in self.log:
                print("[INFO] Received disconnect signal from server. Terminating connection...")
                self.isAlive = False
                
        self.sock.close()
    
def printHeader(message: str) -> None:
    headerTitle = "SEARCHLIGHT CYBER"
    
    longest = len(headerTitle) if len(headerTitle) > len(message) else len(message)
    print("*" + "=" * (longest + 4) + "*")
    print(("|  " + headerTitle + "  |") if longest == len(headerTitle) else ("|" + " " * int((longest - len(headerTitle) + 4)//2) + headerTitle + " " * int((longest - len(headerTitle) + 4)//2 + (1 if (longest - len(headerTitle) + 4) % 2 == 1 else 0)) + "|"))
    print(("|  " + message + "  |") if longest == len(message) else ("|" + " " * int((longest - len(message) + 4)//2) + message + " " * int((longest - len(message) + 4)//2 + (1 if (longest - len(message) + 4) % 2 == 1 else 0) ) + "|"))
    print("*" + "=" * (longest + 4) + "*")
    
    print()
    
def customerLogin(client: Client) -> tuple:
    firstTry = True
    loginSuccessful = False
    
    while not loginSuccessful:
        cls()
        printHeader("ACCOUNT LOGIN")
        
        if not firstTry:
            print("Error : Username or password is incorrect.")
        else:
            firstTry = False
        
        username = input("Email Address > ") 
        password = input("Password > ")
        
        loginResult = client.sendQuery(f"SELECT * FROM customerFile WHERE customerEmail='{username}' AND customerPassword='{password}'")
        
        if len(loginResult) != 0:
            return loginResult[0]

def customerRegister(client: Client) -> tuple:
    cls()
    printHeader("ACCOUNT REGISTRATION")
    
    name = input("Name > ")
    email = input("Email > ")
    psswd = input("Password > ")
    
    return client.sendQuery(f"INSERT INTO customerFile(customerName, customerEmail, customerPassword) VALUES ('{name}', '{email}', '{psswd}')")[0]
    
def customerLoginMenu(client: Client) -> tuple:
    cls()
    printHeader("FILE SCANNER")
    
    print("1) Login")
    print("2) Register")
    
    option = input("> ")
    while option not in ["1", "2"]:
        print()
        print("Please enter a valid choice!")
        option = input("> ")
        
    match option:
        case "1":
            return customerLogin(client)
        case "2":
            return customerRegister(client)
    
def scanFile(client: Client) -> None:
    global userID
    
    filePath = input("File Path > ")
    
    readSuccess = False
    while not readSuccess:
        try:
            with open(filePath, "rb") as f:
                fileContents = f.read()
                
            readSuccess = True
        except:
            print("Error - Could not read file.")
            
        if not readSuccess:
            filePath = input("File Path > ")
            
    toSend = json.dumps( {"type": "scan_request", "user_id": str(userID), "filename": filePath} )
    client.send( toSend )
        
    toSend = json.dumps( {"type": "transfer_begin", "body":len(fileContents)} )
    client.send(toSend)
    
    time.sleep(0.1)
    client.send(fileContents)
        
    toSend = json.dumps( {"type": "transfer_end"} )
    client.send(toSend)

    while True:
        last_log = client.getLastLog()
            
        if last_log["type"] == "scan_done":
            cls()
            printHeader("SCAN COMPLETE")
            
            totalMatches = 0
            for match in last_log["body"]:
                totalMatches += last_log["body"][match][0]
            
            totalSuspicion = last_log['susp']
            
            threatLevel = "Low"
            suggestedAction = "None"
            
            if totalSuspicion > 10:
                threatLevel = "Medium"
                suggestedAction = "Manual Analysis"
            if totalSuspicion > 30:
                threatLevel = "High"
                suggestedAction = "Quarrantine"
            if totalSuspicion > 50:
                threatLevel = "Extreme"
                suggestedAction = "Delete"
            
            print(f"Total matches found: {totalMatches}")
            print(f"Total Suspicion:     {totalSuspicion}")
            print(f"Threat Level:        {threatLevel}")
            print(f"Suggested Action:    {suggestedAction}")
            
            print()
            if len(last_log["body"]) > 0:
                printHeader("MATCH INFORMATION")
                
                for match in last_log["body"]:
                    matchInfo = last_log["body"][match]
                    
                    print(f"Rule Name:        {match}")
                    print(f"Rule Description: {matchInfo[1]}")
                    print(f"# of Matches:     {matchInfo[0]}")
                    print()
                
            break
    
def generateReports(client: Client):
    global userID
    
    cls()
    printHeader("SCAN REPORTS")
    
    allFiles = client.sendQuery(f"SELECT * FROM targetFile WHERE targetFile.customerID={userID}")

    for i, f in enumerate(allFiles):
        print(f"{i+1}) {f[1]} ({f[3]})")
        
    print("x) Back")
        
    option = input("> ")
    if option.lower() == "x":
        return
    
    while option not in [str(n) for n in range(1, len(allFiles) + 1)]:
        print("Please enter a valid choice!")
        option = input("> ")
        
    index = int(option) - 1
    target = allFiles[index]
    
    allMatches = client.sendQuery(f"SELECT * FROM scanFile WHERE targetID={target[0]}")
    
    totalSuspicion = 0
    numMatches = 0
    
    for match in allMatches:
        totalSuspicion += client.sendQuery(f"SELECT ruleSuspicion FROM ruleFile WHERE ruleID={match[2]}")[0][0]
        numMatches += match[4]
    
    threatLevel = "Low"
    suggestedAction = "None"
    
    if totalSuspicion > 10:
        threatLevel = "Medium"
        suggestedAction = "Manual Analysis"
    if totalSuspicion > 30:
        threatLevel = "High"
        suggestedAction = "Quarrantine"
    if totalSuspicion > 50:
        threatLevel = "Extreme"
        suggestedAction = "Delete"
    
    cls()
    printHeader(f"SCAN REPORT - {target[1]}")
    
    print(f"Filename:  {target[1]}")
    print(f"File ID:   {target[0]}")
    print(f"Scan Date: {target[3]}")
    print()
    print(f"Customer ID:    {userID}")
    print(f"Customer Name:  {userName}")
    print(f"Customer Email: {userEmail}")
    print()
    print(f"Number of matches: {numMatches}")
    print(f"Total Suspicion:   {totalSuspicion}")
    print(f"Threat Level:      {threatLevel}")
    print(f"Suggested Action:  {suggestedAction}")
    print()
    
    printHeader("MATCH DETAILS")
    
    for match in allMatches:
        ruleDetails = client.sendQuery(f"SELECT * FROM ruleFile WHERE ruleID={match[2]}")[0]
        patternDetails = client.sendQuery(f"SELECT * FROM patternFile WHERE patternID={match[3]}")[0]
        
        print(f"Rule ID:          {ruleDetails[0]}")
        print(f"Rule Name:        {ruleDetails[1]}")
        print(f"Rule Description: {ruleDetails[2]}")
        print(f"Pattern String:   {patternDetails[3]}")
        print(f"Occurances:       {match[4]}")
        
    print()
    print("1) Save as plain text")
    print("2) Save with formatting (Markdown)")
    print("3) Back")
    
    option = input("> ")
    while option not in ["1", "2", "3"]:
        print("Please enter a valid option!")
        option = input("> ")
        
    match option:
        case "1":
            filePath = input("File Path > ")
            f = open(filePath, "w")
            
            f.write(f"SCAN REPORT - {target[1]}\n")
            f.write(f"=============={'=' * len(target[1])}\n")
            f.write("\n")
            
            f.write(f"Filename:  {target[1]}\n")
            f.write(f"File ID:   {target[0]}\n")
            f.write(f"Scan Date: {target[3]}\n")
            f.write("\n")
            f.write(f"Customer ID:    {userID}\n")
            f.write(f"Customer Name:  {userName}\n")
            f.write(f"Customer Email: {userEmail}\n")
            f.write("\n")
            f.write(f"Number of matches: {numMatches}\n")
            f.write(f"Total Suspicion:   {totalSuspicion}\n")
            f.write(f"Threat Level:      {threatLevel}\n")
            f.write(f"Suggested Action:  {suggestedAction}\n")
            f.write("\n")
            
            f.write(f"MATCH DETAILS\n")
            f.write(f"-------------\n")
            f.write("\n")
            
            for match in allMatches:
                ruleDetails = client.sendQuery(f"SELECT * FROM ruleFile WHERE ruleID={match[2]}")[0]
                patternDetails = client.sendQuery(f"SELECT * FROM patternFile WHERE patternID={match[3]}")[0]
                
                f.write(f"Rule ID:          {ruleDetails[0]}\n")
                f.write(f"Rule Name:        {ruleDetails[1]}\n")
                f.write(f"Rule Description: {ruleDetails[2]}\n")
                f.write(f"Pattern String:   {patternDetails[3]}\n")
                f.write(f"Occurances:       {match[4]}\n")
                
            f.close()
            
        case "2":
            filePath = input("File Path > ")
            f = open(filePath, "w")
            
            f.write(f"## Scan Report - {target[1]}\n\n")
            
            f.write(f"- **Filename:**  {target[1]}\n")
            f.write(f"- **File ID:**   {target[0]}\n")
            f.write(f"- **Scan Date:** {target[3]}\n")
            f.write("---\n\n")
            f.write(f"- **Customer ID:**    {userID}\n")
            f.write(f"- **Customer Name:**  {userName}\n")
            f.write(f"- **Customer Email:** {userEmail}\n")
            f.write("---\n\n")
            f.write(f"- **Number of matches:** {numMatches}\n")
            f.write(f"- **Total Suspicion:**   {totalSuspicion}\n")
            f.write(f"- **Threat Level:**      {threatLevel}\n")
            f.write(f"- **Suggested Action:**  {suggestedAction}\n")
            
            f.write(f"### Match Details\n\n")
            
            for match in allMatches:
                ruleDetails = client.sendQuery(f"SELECT * FROM ruleFile WHERE ruleID={match[2]}")[0]
                patternDetails = client.sendQuery(f"SELECT * FROM patternFile WHERE patternID={match[3]}")[0]
                
                f.write(f"---\n\n")
                f.write(f"- **Rule ID:**          {ruleDetails[0]}\n")
                f.write(f"- **Rule Name:**        {ruleDetails[1]}\n")
                f.write(f"- **Rule Description:** {ruleDetails[2]}\n")
                f.write(f"- **Pattern String:**   {patternDetails[3]}\n")
                f.write(f"- **Occurances:**       {match[4]}\n")
                
            f.close()
            
    
def mainMenu(client: Client):
    global userID
    global userName
    global userEmail
    global userPassword
    
    cls()
    printHeader("MAIN MENU")
    
    print("1) Scan File")
    print("2) Generate Scan Reports")
    print("3) Quit")
    
    option = input("> ")
    while option not in ["1", "2", "3"]:
        print()
        print("Please enter a valid choice!")
        option = input("> ")
        
    match option:
        case "1":
            scanFile(client)
        case "2":
            generateReports(client)
        case "3":
            client.sock.close()
            client.listenerThread.join()
            quit()
            
    input("[PRESS ENTER] ")

userID = None
userName = None
userEmail = None
userPassword = None
    
if __name__ == "__main__":
    client = Client(HOST, PORT)
    
    userInfo = customerLoginMenu(client)
    
    userID = userInfo[0]
    userName = userInfo[1]
    userEmail = userInfo[2]
    userPassword = userInfo[3]
    
    while True:
        mainMenu(client)