import datetime
import os

from db import db

class Functions:
    @staticmethod
    def insertDefaultUsers():
        db.connect()

        customers = [
            ("John", "Highway 21", datetime.date.today()),
            ("Alice", "Maple Street 12", datetime.date.today() + datetime.timedelta(days=1)),
            ("Bob", "Oak Avenue 33", datetime.date.today() + datetime.timedelta(days=24)),
            ("Clara", "Pine Lane 5", datetime.date.today() + datetime.timedelta(days=21)),
            ("David", "Elm Street 42", datetime.date.today() + datetime.timedelta(days=4)),
            ("Eva", "Cedar Road 19", datetime.date.today() + datetime.timedelta(days=2.5)),
            ("Frank", "Birch Boulevard 7", datetime.date.today() + datetime.timedelta(days=12)),
            ("Grace", "Spruce Way 16", datetime.date.today() + datetime.timedelta(days=15)),
            ("Henry", "Willow Drive 28", datetime.date.today() + datetime.timedelta(days=7)),
            ("Isla", "Chestnut Circle 3", datetime.date.today() + datetime.timedelta(days=32)),
        ]

        for val in customers:
            db.execute("INSERT INTO customers (username, address, created_at) VALUES (?, ?, ?) ON CONFLICT (username) DO NOTHING", val)

        db.commit()

    def offerBook(self,
                  Title,
                  Author,
                  Created,
                  Edition,
                  Publisher,
                  Book_condition,
                  Description,
                  Price,
                  customerName,
                  Status = "Available",
                ):

        try :
            bookId = db.insertIntoBookTable(Title,
                      Author,
                      Created,
                      Edition,
                      Publisher,
                      Book_condition,
                      Description)

            # Gets the whole customer row in DB
            wholeCustomer = db.getCustomerDetail(customerName)
            db.setVendor(wholeCustomer[0])

            # Track a user's offering behavior if they consented to data sharing
            if wholeCustomer[4] == "YES":  # Club member
                db.trackUserInterest(wholeCustomer[0], "OFFER", {
                    'book_id': bookId,
                    'title': Title,
                    'price': Price
                })

            db.insertIntoOfferTable(bookId, Price, Status, wholeCustomer[0])

        except Exception as e :
           print( "exception occurred " + str(e))

    def search(self,
               Title,
               Author,
               Created,
               Edition,
               Publisher,
               Book_condition,
               Description,
               customerName
               ):
        try:
            books = db.filterBook(Title, Author, Created, Edition, Publisher, Book_condition, Description)

            # Track search terms if user consented to data sharing
            customerInfo = db.getCustomerDetail(customerName)
            if customerInfo and customerInfo[4] == "YES":
                search_terms = {
                    'title': Title,
                    'author': Author,
                    'year': Created,
                    'edition': Edition,
                    'condition': Book_condition,
                    'publisher': Publisher
                }

                if customerInfo[6] != "BASIC" :
                    db.trackUserInterest(customerInfo[0], "SEARCH", search_terms)

            print("\nList of available books to be purchased:")
            print('[Id][Title][Author][Year][Edition][Publisher][Condition][Description][Price]')
            for book in books:
                print(book)

        except Exception as e :
            print("exception occurred " + str(e) + "\n")
            print(self.search.__name__)


    def purchase(self, bookId, customerName):
        try:
            customerBuyerAddress = db.getCustomerDetail(customerName)[2]
            customerId = db.getCustomerDetail(customerName)[0]
            wallet = db.getCustomerDetail(customerName)[3]
            bookDetail = db.getBookDetail(bookId)
            isClubMember = db.getCustomerDetail(customerName)[4]

            # get book price
            bookPrice = db.getPriceOfBookIfAvailable(bookId)

            if bookPrice is None:
                print("Book does not exist or is unavailable")
                return

            #check whether customer has money
            if bookPrice > wallet:
                print("You do not have enough money")
                return

            #set book as purchased if they do and subtract money according to the book price
            if isClubMember == 'YES':
                db.removeMoney(bookPrice * 0.9, customerId)
                if db.getCustomerDetail(customerName)[6] == "FULL":
                    db.trackUserInterest(customerId, "PURCHASE", {
                        'book_id': bookId,
                        'title': bookDetail[1],
                        'author': bookDetail[2],
                        'Condition': bookDetail[6],
                        'price': bookPrice,
                        'address': customerBuyerAddress
                    })
                else :
                    db.trackUserInterest(customerId, "PURCHASE", {
                        'book_id': bookId,
                        'title': bookDetail[1],
                        'author': bookDetail[2],
                        'Condition': bookDetail[6],
                        'price': bookPrice
                    })
            else:
                db.removeMoney(bookPrice, customerId)

            db.setBookAsPurchased(bookId, customerId)
            print("\nPurchase completed with id: " + bookId)

            pathBuyer = './ConfirmationBuyer.txt'
            pathSeller = './ConfirmationSeller.txt'

            if not os.path.exists(pathBuyer):
                open("ConfirmationBuyer.txt", "x")

            if not os.path.exists(pathSeller):
                open("ConfirmationSeller.txt", "x")

            with open("ConfirmationBuyer.txt", "w") as f:
                f.write("Thanks for purchasing the book with id " + str(bookId) + " - " + str(bookDetail[1]) +
                        ".\nPrice: " + str(bookPrice) +
                        "\nCustomer address: " + customerBuyerAddress +
                        "\nThe book will be sent to you within 5 working days.\n")

            with open("ConfirmationSeller.txt", "w") as f:
                f.write("Customer " + str(customerName) + " has purchased your book with id " + str(bookId) +
                        " - " + str(bookDetail[1]) +
                        ".\nPrice: " + str(bookPrice) +
                        "\nCustomer address: " + customerBuyerAddress +
                        "\nYou have 2 working days to send the book to the buyer.\n")

            print("A receipt has been sent successfully to both you and the seller. Have a nice day!")

        except Exception as e :
            print("exception occurred " + str(e) + "\n")
            print(self.purchase.__name__)

    def takeInput(self):
        while True:
            customerName = input("Choose login: ")
            result = db.lookupExistingCustomer(customerName)
            if result:
                break
        print("\nLogin was successful")
        while True:
            customerInfo = db.getCustomerDetail(customerName)
            print("\n[ Wallet: {} ]".format(customerInfo[3]))
            print("1. Offer ")
            print("2. Search ")
            print("3. Purchase ")
            print("4. Add money ")
            print("5. Club member management ")
            print("6. Exit ")

            stringInput = input("\nChoose option: ")
            db.lookupExistingCustomer(stringInput)
            match stringInput:
                case "1":
                    Title = input("Enter Title: ")
                    Author = input("Enter Author: ")
                    Created = input("Enter Year: ")
                    Edition = input("Enter Edition: ")
                    Publisher = input("Enter Publisher: ")
                    Book_condition = input("Enter Condition: ")
                    Description = input("Enter Description: ")
                    Price = input("Enter Price: ")

                    self.offerBook(
                        Title,
                        Author,
                        Created,
                        Edition,
                        Publisher,
                        Book_condition,
                        Description,
                        Price,
                        customerName)
                    print('\nOffer placed\n')

                case "2":
                    ViewAll = input("View all books?: ")
                    if ViewAll.lower() == "yes" or ViewAll.lower() == "y":
                        self.search("", "", "", "", "", "", "", customerName)
                    else:
                        Title = input("Enter Title: ")
                        Author = input("Enter Author: ")
                        Created = input("Enter Year: ")
                        Edition = input("Enter Edition: ")
                        Publisher = input("Enter Publisher: ")
                        Book_condition = input("Enter Condition: ")
                        Description = input("Enter Description: ")
                        self.search(Title,
                                    Author,
                                    Created,
                                    Edition,
                                    Publisher,
                                    Book_condition,
                                    Description,
                                    customerName)

                case "3":
                    Book_id = input("Enter Book ID: ")
                    if customerInfo[4] == 'NO':
                        print("Do you want to subscribe to our club membership? Terms of agreement applies. (Y/N): ")
                        sellDataConsent = input("Enter YES/NO: ").upper()
                        if sellDataConsent in ["YES", "Y"]:
                            db.addClubMember(db.getCustomerDetail(customerName)[0])
                        self.purchase(Book_id, customerName)
                    else :
                        self.purchase(Book_id, customerName)

                case "4":
                    print("Insert money")
                    money = input("Enter Money: ")
                    db.addMoney(money, db.getCustomerDetail(customerName)[0])
                    print("\nMoney added successfully")

                case "5":
                    sharing_levels = {
                        'a': 'BASIC',
                        'b': 'STANDARD',
                        'c': 'FULL'
                    }

                    if customerInfo[4] == 'NO':
                        print("\nDo you want to be a club member, get discounts and see full activity? Terms of agreement applies. ")
                        print("\nClub membership benefits:")
                        print("1. 10% discount on purchases")
                        print("2. Early access to new arrivals")
                        print("\nData sharing options for better experience :):")
                        print("a. Basic: Purchase history only")
                        print("b. Standard: Purchase + search history")
                        print("c. Full: All activity including address")
                        choice = input("Enter option (1/2) or (a/b/c): ")

                        if choice in ['1', '2', '3']:
                            db.addClubMember(customerInfo[0])
                        elif choice.lower() in sharing_levels:
                            db.addClubMember(customerInfo[0])
                            db.setDataSharingLevel(customerInfo[0], sharing_levels[choice.lower()])

                    elif customerInfo[4] == 'YES':
                        print("\nWelcome club member!\nWant to delete your club member status and miss your discounts? ")
                        deleteDataConsent = input("Enter YES/NO: ").upper()
                        if deleteDataConsent in ["YES", "Y"]:
                            db.deleteClubMember(db.getCustomerDetail(customerName)[0])
                            db.setDataSharingLevel(db.getCustomerDetail(customerName)[0], "NONE")
                        else :
                            print("\nYou are still a club member! See you next time!")

                case "6":
                    print("\nSee you next time!")
                    exit()

                case "q":
                    break

                case _:
                    print("Illegal input")

func = Functions()