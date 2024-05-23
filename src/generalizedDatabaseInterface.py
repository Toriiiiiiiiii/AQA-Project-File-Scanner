from util import *

# Generalized Data Interface
# \-> Created to minimise repetition in code.
# \-> Every instance of this class can be connected to a table by name.
# \-> Allows for data entry, record updating and deleting in a table.
# \-> Class will automatically detect field names, types and the primary key.
class GeneralDataInterface:
    def __init__(self, tableName: str) -> None:
        self.tableName = tableName
        
        self.fieldNames = self.getFieldNames()
        self.fieldTypes = self.getFieldTypes()
        
        self.primaryKey = self.getPrimaryKeyName()
        self.primaryKeyIndex = self.fieldNames.index(self.primaryKey)
        
    # Returns a list of all fields in a table
    def getFieldNames(self) -> list:
        cursor = databaseCurs.execute(f"SELECT * FROM {self.tableName}")
        
        # List comprehension using query result information to get names of fields.
        return [description[0] for description in cursor.description]
    
    # Returns a list giving the corresponding types of the fields.
    def getFieldTypes(self) -> list:
        result = []
        
        # Get info for the table
        info = databaseCurs.execute(f"PRAGMA table_info('{self.tableName}')").fetchall()
        for fieldInfo in info:
            # fieldInfo[2] corresponds to the data type of the field.
            result.append(fieldInfo[2])
            
        return result
    
    # Returns the name of the primary key of a table
    def getPrimaryKeyName(self) -> str:
        return databaseCurs.execute(f"SELECT field.name FROM pragma_table_info('{self.tableName}') as field WHERE field.pk = 1").fetchone()[0]
    
    def printFieldValuesForEntry(self) -> None:
        index = 0
        for index, field in enumerate(self.fieldsWithoutPK):
            print(f" {index + 1}) {splitCamelCase(field)} : {self.fieldValues[index]}")
            
        print(f" {index + 2}) Confirm")
    
    def setupFields(self):
        self.fieldsWithoutPK = []
        self.typesWithoutPK = []
        self.fieldValues = []
        for index, field in enumerate(self.fieldNames):
            if field != self.primaryKey: 
                self.fieldsWithoutPK.append(field)
                self.typesWithoutPK.append(self.fieldTypes[index])
                self.fieldValues.append(None)
    
    # General function for data entry.
    # Used by both insertNewRecord() and updateRecord()
    def enterData(self) -> None:
        while True: 
            cls()

            self.printFieldValuesForEntry()
            option = input(">> ")
            
            try: 
                option = int(option)
            except:
                print("[ERROR] Choice must be an integer.")
                continue
            
            if option < 1 or option > len(self.fieldsWithoutPK) + 1:
                print(f"[ERORR] Choice must be between 1 and {len(self.fieldsWithoutPK) + 1}")
            
            if option == len(self.fieldsWithoutPK) + 1:
                break
            
            fieldIndex = option - 1
            newVal = input("New Value : ")
            
            if self.typesWithoutPK[fieldIndex] == "TEXT":
                newVal = f"'{newVal}'"
            
            self.fieldValues[fieldIndex] = newVal
    
    def deleteRecord(self) -> int:
        result = None

        while not result:
            recordID = input(f"{self.primaryKey} : ")
            sqlQuery = f"SELECT * FROM {self.tableName} WHERE {self.primaryKey}={recordID}"
            result = databaseCurs.execute(sqlQuery).fetchone()
            
            if not result:
                print(f"[ERROR] Record with ID {recordID} was not found!")
                
        confirm = input(f"Confirm deletion of record {recordID}? (Y/n) : ").lower()
        
        while confirm not in "yn":
            print("[ERROR] Invalid choice!")
            confirm = input(f"Confirm deletion of record {recordID}? (Y/n) : ").lower()
            
        if confirm == "n":
            return
        
        databaseCurs.execute(f"DELETE FROM {self.tableName} WHERE {self.primaryKey}={recordID}")
        databaseConn.commit()
        print("Record Deleted!")
        return recordID
    
    def updateRecord(self) -> None:
        self.setupFields()

        result = None

        while not result:
            recordID = input(f"{self.primaryKey} : ")
            sqlQuery = f"SELECT * FROM {self.tableName} WHERE {self.primaryKey}={recordID}"
            result = databaseCurs.execute(sqlQuery).fetchone()
            
            if not result:
                print(f"[ERROR] Record with ID {recordID} was not found!")
                
        self.fieldValues = []
        index = 0
        maxIndex = len(self.fieldsWithoutPK)
        while index < maxIndex:
            if index == self.primaryKeyIndex:
                maxIndex += 1
                index += 1
                continue
            
            self.fieldValues.append(f"'{result[index]}'" if self.fieldTypes[index] == "TEXT" else result[index])
            index += 1
            
        self.enterData()
        
        sql = f"UPDATE {self.tableName} SET "
        
        fieldSetStatements = []
        for index, field in enumerate(self.fieldsWithoutPK):
            fieldSetStatements.append(f"{field}={self.fieldValues[index]}")
            
        sql += ", ".join(fieldSetStatements)
        sql += f" WHERE {self.primaryKey}={recordID}"
        databaseCurs.execute(sql)
        databaseConn.commit()
        print("Record updated!")

    
    def insertNewRecord(self) -> None:
        self.setupFields()
                
        self.enterData()
            
        sql =  f"INSERT INTO {self.tableName}({', '.join(self.fieldsWithoutPK)})"
        sql += f"VALUES ({', '.join(self.fieldValues)})"
        
        databaseCurs.execute(sql)
        databaseConn.commit()
        print("Record Inserted!")
        
        
    def printAll(self) -> None:
        allRecords = databaseCurs.execute(f"SELECT * FROM {self.tableName}").fetchall()
        
        fieldLengths = {}
        
        for field in self.fieldNames:
            fieldLengths[field] = len(field)
        
        for record in allRecords:
            for fieldIndex in range(len(self.fieldNames)):
                fieldName = self.fieldNames[fieldIndex]
                
                if len(str(record[fieldIndex])) > fieldLengths[fieldName]:
                    fieldLengths[fieldName] = len(str(record[fieldIndex]))
                 
        print("| ", end="")
        for field in self.fieldNames:
            print(f"%-{fieldLengths[field]}s" %(field), end=" | ")
        print("\n|-", end="")
        
        for field in self.fieldNames:
            print(f"-" * fieldLengths[field], end="-|")
            
            if field != self.fieldNames[len(self.fieldNames)-1]:
                print("-", end="")
                
        for record in allRecords:
            print("\n| ", end="")
            for fieldIndex in range(len(self.fieldNames)):
                fieldName = self.fieldNames[fieldIndex]
                
                print(f"%-{fieldLengths[fieldName]}s" % record[fieldIndex], end=" | ")
        
        print("\n")