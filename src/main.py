###################################m
# SEARCHLIGHT CYBER - FILE SCANNER #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# Created by Cory "Tori" Hall      # 
####################################

### TODO
# [X] Main Menu
# [X] File Scan
# \-> [ ] Target File Database
# [X] Generalized Database Interface
# [X] Customer Menu
# [X] Rule/Pattern Menu
# [ ] Scan Reports

### File Imports ###
import json

from util import *
from scan import *
from generalizedDatabaseInterface import *

def loadRulesFromJson(path: str) -> None:
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
   
   
def exportRulesToJson(path: str) -> None:
    allRules = databaseCurs.execute(f"SELECT * FROM ruleFile").fetchall()
    
    fullJson = []
    
    for (ruleID, ruleName, ruleDesc, ruleSusp) in allRules:
        associatedPatterns = databaseCurs.execute(f"SELECT * FROM patternFile WHERE ruleID={ruleID}").fetchall()
        
        currentJson = {
            "name": ruleName,
            "desc": ruleDesc,
            "susp": ruleSusp,
            
            "patterns": []
        }
        
        for (patternID, pRuleID, patternType, patternValue) in associatedPatterns:
            currentJson["patterns"].append({"type": patternType, "value": patternValue})
    
        fullJson.append(currentJson)
        
    with open(path, "w") as f:
        json.dump(fullJson, f)
   
   
def scanFile():
    cls()
            
    print("+====================+")
    print("| SEARCHLIGHT CYBER: |")
    print("|      SCAN FILE     |")
    print("+====================+")
    print()
    filePath = input("Path of file to scan: ")
    scan = FileScan(filePath)
    
    if not scan.matches:
        print("SCAN FAILED")
        input("[PRESS ENTER]")
        return
    
    print()
    print("=====================")
    print("|    Scan Results   |")
    print("=====================")
    print()
    
    matchesFound = 0
    totalSuspicion = 0
    
    for match in scan.matches:
        matchesFound += match.occurances
        
        patternSuspicion = databaseCurs.execute(f"SELECT ruleSuspicion FROM ruleFile WHERE ruleID={match.ruleID}").fetchone()[0]
        totalSuspicion += patternSuspicion * match.occurances
        
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
        
    print(f"Total Matches:    {matchesFound}")
    print(f"Total Suspicion:  {totalSuspicion}")
    print(f"Threat Level:     {threatLevel}")
    print(f"Suggested Action: {suggestedAction}")


def ruleMenu():
    while True:
        cls()
        
        print("+====================+")
        print("| SEARCHLIGHT CYBER: |")
        print("|      RULE MENU     |")
        print("+====================+")
        print()
        print("  1) List Rules/Patterns")
        print("  2) Import Rules from JSON")
        print("  3) Export Rules to JSON")
        print("  4) Delete Rule")
        print("  5) Clear Rule Table")
        print("  6) Clear Pattern Table")
        print("  7) Back")
        
        userChoice = input(">> ")
    
        try:
            userChoice = int(userChoice)
        except:
            print("[ERROR] - Choice must be a number.")
            input()
            continue
        
        if userChoice < 1 or userChoice > 7:
            print("[ERROR] - Choice must be a listed option.")
            input()
            continue
        
        ruleFileInterface = GeneralDataInterface("ruleFile")
        
        match userChoice:
            case 1:
                cls()
                
                print("+====================+")
                print("| SEARCHLIGHT CYBER: |")
                print("|      RULE MENU     |")
                print("+====================+")
                print("  1) List Rules")
                print("  2) List Patterns")
                
                userChoice = input(">> ")
    
                try:
                    userChoice = int(userChoice)
                except:
                    print("[ERROR] - Choice must be a number.")
                    input()
                    continue
                
                if userChoice < 1 or userChoice > 2:
                    print("[ERROR] - Choice must be a listed option.")
                    input()
                    continue
                
                cls()
                match userChoice:
                    case 1:
                        ruleFileInterface.printAll()
                    case 2:
                        GeneralDataInterface("patternFile").printAll()
                
            case 2:
                filePath = input("Path of file to import : ")
                loadRulesFromJson(filePath)
            case 3:
                filePath = input("Path of file to save rules to : ")
                exportRulesToJson(filePath)
            case 4:
                id = ruleFileInterface.deleteRecord()
                
                userChoice = input("Delete associated patterns? (Y/n) : ").lower()
                while userChoice not in "yn":
                    print("[ERROR] - Choice must be Y or N.")
                    userChoice = input("Delete associated patterns? (Y/n) : ").lower()
                    
                if userChoice == "y":
                    databaseCurs.execute(f"DELETE FROM patternFile WHERE ruleID={id}")
                    databaseConn.commit()
            case 5:
                userChoice = input("Confirm Table Clear? **THIS CANNOT BE UNDONE** (Y/n) : ").lower()
                while userChoice not in "yn":
                    print("[ERROR] - Choice must be Y or N.")
                    userChoice = input("Confirm Table Clear? **THIS CANNOT BE UNDONE** (Y/n) : ").lower()
                    
                confirmation = input("Type 'Clear ruleFile' to continue: ").lower()
                if confirmation != "clear rulefile":
                    print("[ABORTING CLEAR]")
                else:
                    databaseCurs.execute("DELETE FROM ruleFile")
                    databaseConn.commit()
            case 6:
                userChoice = input("Confirm Table Clear? **THIS CANNOT BE UNDONE** (Y/n) : ").lower()
                while userChoice not in "yn":
                    print("[ERROR] - Choice must be Y or N.")
                    userChoice = input("Confirm Table Clear? **THIS CANNOT BE UNDONE** (Y/n) : ").lower()
                    
                confirmation = input("Type 'Clear patternFile' to continue: ").lower()
                if confirmation != "clear rulefile":
                    print("[ABORTING CLEAR]")
                else:
                    databaseCurs.execute("DELETE FROM patternFile")
                    databaseConn.commit()
            case 7:
                return
            
        input("[PRESS ENTER]")
        
        
def customerMenu():
    while True:
        cls()
        
        print("+========================+")
        print("|   SEARCHLIGHT CYBER:   |")
        print("|      CUSTOMER MENU     |")
        print("+========================+")
        print()
        print("  1) List Customers")
        print("  2) Add New Customer")
        print("  3) Update Customer")
        print("  4) Delete Customer")
        print("  5) Back")
        
        userChoice = input(">> ")
        
        try:
            userChoice = int(userChoice)
        except:
            print("[ERROR] - Choice must be a number.")
            return
        
        if userChoice < 1 or userChoice > 5:
            print("[ERROR] - Choice must be a listed option.")
            return
        
        customerFileInterface = GeneralDataInterface("customerFile")
        
        match userChoice:
            case 1:
                cls()
                customerFileInterface.printAll()
                
            case 2:
                customerFileInterface.insertNewRecord()
            
            case 3:
                customerFileInterface.updateRecord()
                
            case 4:
                customerFileInterface.deleteRecord()
                
            case 5:
                return
            
        input("[PRESS ENTER]")
    
        
def main():
    cls()
    
    print("+====================+")
    print("| SEARCHLIGHT CYBER: |")
    print("|      MAIN MENU     |")
    print("+====================+")
    print()
    print("  1) Scan File")
    print("  2) Customer Menu")
    print("  3) Rule/Pattern Menu")
    print("  4) Generate Scan reports")
    print("  5) Quit")
    
    userChoice = input(">> ")
    
    try:
        userChoice = int(userChoice)
    except:
        print("[ERROR] - Choice must be a number.")
        return
    
    if userChoice < 1 or userChoice > 5:
        print("[ERROR] - Choice must be a listed option.")
        return
    
    match userChoice:
        case 1:
            scanFile()               
        case 2:
            customerMenu()
        case 3:
            ruleMenu()
        case 4:
            pass
        case 5:
            quit(0)
            
    input("[PRESS ENTER]")
    
    
### Main Code ###
   
while True:
    main()