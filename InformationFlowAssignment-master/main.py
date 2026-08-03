from db import db
from funcs import func
# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')
    db.connect()
    func.insertDefaultUsers()
    #func.offerBook("Database System Concepts", "Abraham Silberschatz", 2020, 7,
    #               "McGraw-Hill Education", "good",
    #               "Database management has evolved from a specialized computer application "
    #               "to a central component of virtually all enterprises, and, as a result"
    #               "knowledge about database systems has become an essential part "
    #               "of an education in computer science.", 1000, "John")
    #func.search("", "", "" , "", "", "", "")
    #func.purchase(1, "John")
    while True:
        func.takeInput()
