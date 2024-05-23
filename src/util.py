import os
from os.path import isfile
import sqlite3

### Utility Functions ###

# Splits a camelCase string into words based on capitalisation.
# eg: "helloWorld" -> "Hello World"
# Used to help with generalised data entry/display
def splitCamelCase(camelCase: str) -> str:
    result = list(camelCase)
    wasLastCharacterLowercase = False
    for index, character in enumerate(result):
        if character.islower(): wasLastCharacterLowercase = True
        else:
            if wasLastCharacterLowercase == True:
                result.insert(index, " ")
                
            wasLastCharacterLowercase = False
            
    return "".join(result).title()


def cls():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")
    

def setupDatabase():
    global databaseConn, databaseCurs

    sqlCommand = ""
    sqlCommand += "CREATE TABLE targetFile("
    sqlCommand += "targetID INTEGER PRIMARY KEY AUTOINCREMENT,"
    sqlCommand += "fileName TEXT,"
    sqlCommand += "customerID INTEGER,"
    sqlCommand += "scanDate TEXT)"

    databaseCurs.execute(sqlCommand)

    sqlCommand = ""
    sqlCommand += "CREATE TABLE scanFile("
    sqlCommand += "scanID INTEGER PRIMARY KEY AUTOINCREMENT,"
    sqlCommand += "targetID INTEGER,"
    sqlCommand += "ruleID INTEGER,"
    sqlCommand += "patternID INTEGER,"
    sqlCommand += "numFound INTEGER)"

    databaseCurs.execute(sqlCommand)

    sqlCommand = ""
    sqlCommand += "CREATE TABLE ruleFile("
    sqlCommand += "ruleID INTEGER PRIMARY KEY AUTOINCREMENT,"
    sqlCommand += "ruleName TEXT,"
    sqlCommand += "ruleDescription TEXT,"
    sqlCommand += "ruleSuspicion REAL)"

    databaseCurs.execute(sqlCommand)

    sqlCommand = ""
    sqlCommand += "CREATE TABLE patternFile("
    sqlCommand += "patternID INTEGER PRIMARY KEY AUTOINCREMENT,"
    sqlCommand += "ruleID INTEGER,"
    sqlCommand += "patternType TEXT,"
    sqlCommand += "patternText TEXT)"

    databaseCurs.execute(sqlCommand)

    sqlCommand = ""
    sqlCommand += "CREATE TABLE customerFile("
    sqlCommand += "customerID INTEGER PRIMARY KEY AUTOINCREMENT,"
    sqlCommand += "customerName TEXT,"
    sqlCommand += "customerEmail TEXT)"

    databaseCurs.execute(sqlCommand)
    databaseConn.commit()
    
fileExists = isfile("SEARCHLIGHT CYBER DATABASE.db")
databaseConn = sqlite3.connect("SEARCHLIGHT CYBER DATABASE.db")
databaseCurs = databaseConn.cursor()

if not fileExists:
    setupDatabase()