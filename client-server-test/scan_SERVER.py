from util import *
import re

class Match:
    def __init__(self, ruleID, patternID, occurances) -> None:
        self.ruleID = ruleID
        self.patternID = patternID
        self.occurances = occurances
   
        
class FileScan:
    def __init__(self, fileContents: str, dbConn, dbCurs) -> None:
        self.__fileContents = fileContents
        self.matches = []
        self.scanResult = "None"
        
        self.dbConn = dbConn
        self.dbCurs = dbCurs
        
        self.__performScan()
       
    def __performScan(self) -> None:
        
        patternQueryResult = self.dbCurs.execute("SELECT * FROM patternFile").fetchall()
        for (self.__patternID, self.__ruleID, self.__patternType, self.__patternData) in patternQueryResult:
            match self.__patternType.upper():
                case "INS":
                    self.__matchInsensitive()
                case "STR":
                    self.__matchString()
                case "HEX":
                    self.__matchHex()
                case "RGX":
                    self.__matchRegex()
                case _:
                    print(f"[ERROR] Unrecognised pattern type '{self.__patternType}'")
                    print(f"    \-> Stopping scan.")
                    
                    self.scanResult = "Failure"
                    return
              
                
        self.scanResult = "Success"
        return
    
    def __matchInsensitive(self) -> None:
        self.__patternData = self.__patternData.lower()
                
        fileSubstringList = [self.__fileContents[i:i + len(self.__patternData)] 
                             for i in range(0, int(len(self.__fileContents)))]
        
        patternSearchList = []
        
        # Remove any substring that is smaller than the pattern
        # This speeds up the scan as it is not comparing 
        # strings at the end of the file.
        for substring in fileSubstringList:
            if len(substring) == len(self.__patternData):
                # Do not add any binary data - it will throw an error
                try:
                    patternSearchList.append(bytes.decode(substring).lower())
                except:
                    continue

        # Do not count number of matches if there are none
        if self.__patternData not in patternSearchList:
            return
        
        occurances = patternSearchList.count(self.__patternData)
        print(f"[MATCH]  Found {occurances} match(es) of rule {self.__ruleID} (Pattern {self.__patternID})")
        self.matches.append( Match(self.__ruleID, 
                                     self.__patternID, 
                                     occurances) )
    
    def __matchString(self) -> None:             
        fileSubstringList = [self.__fileContents[i:i + len(self.__patternData)] 
                             for i in range(0, int(len(self.__fileContents)))]
        
        patternSearchList = []
        
        # Remove any substring that is smaller than the pattern
        # This speeds up the scan as it is not comparing 
        # strings at the end of the file.
        for substring in fileSubstringList:
            if len(substring) == len(self.__patternData):
                # Do not add any binary data - it will throw an error
                try:
                    patternSearchList.append(bytes.decode(substring))
                except:
                    continue

        # Do not count number of matches if there are none
        if self.__patternData not in patternSearchList:
            return
        
        occurances = patternSearchList.count(self.__patternData)
        print(f"[MATCH]  Found {occurances} match(es) of rule {self.__ruleID} (Pattern {self.__patternID})")
        self.matches.append( Match(self.__ruleID, 
                                     self.__patternID, 
                                     occurances) )
    
    def __matchHex(self) -> None:
        patternBytes = bytes([int(num, 16) for num in self.__patternData.split(" ")])
                
        fileSubstringList = [self.__fileContents[i:i + len(patternBytes)] 
                             for i in range(0, int(len(self.__fileContents)))]
        
        patternSearchList = []
        
        # Remove any substring that is smaller than the pattern
        # This speeds up the scan as it is not comparing 
        # strings at the end of the file.
        for substring in fileSubstringList:
            if len(substring) == len(patternBytes):
                patternSearchList.append(substring)

        # Do not count number of matches if there are none
        if patternBytes not in patternSearchList:
            return
        
        occurances = patternSearchList.count(patternBytes)
        print(f"[MATCH]  Found {occurances} match(es) of rule {self.__ruleID} (Pattern {self.__patternID})")
        self.matches.append( Match(self.__ruleID, 
                                   self.__patternID, 
                                   occurances) )
    
    def __matchRegex(self) -> None:
        try:
            self.__fileContents = bytes.decode(self.__fileContents)
        except:
            print("[WARN]   Regular Expressions can not be performed on binary files.")
            print("     \-> Skipping Regular Expression Pattern...")
            return
    
        allRegexMatches = re.findall(self.__patternData, self.__fileContents)
        if len(allRegexMatches > 0):
            print(f"[MATCH]  Found {len(allRegexMatches)} match(es) of rule {self.__ruleID} (Pattern {self.__patternID})")
            self.matches.append( Match(self.__ruleID, 
                                       self.__patternID, 
                                       len(allRegexMatches)) )