import sqlite3
from typing import Dict, Any


def _filter_data_by_sharing_level(data: Dict[str, Any], level: str) -> Dict[str, Any]:
    """Filter sensitive data based on sharing level"""
    if level == 'BASIC':
        return {k: v for k, v in data.items() if k not in ['address', 'username']}
    elif level == 'STANDARD':
        return {k: v for k, v in data.items() if k not in ['address']}
    elif level == 'FULL':
        return data
    else:
        return {}

class DataBase:
    def __init__(self):
        self.conn = None
        self.connect()
        # Create book table
        self.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Title TEXT,
                    Author TEXT,
                    Created TEXT,
                    Edition TEXT,
                    Publisher TEXT,
                    Book_condition TEXT,
                    Description TEXT
                );
            """)

        # Create offer table (Book is referenced)
        self.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    Id INTEGER PRIMARY KEY AUTOINCREMENT,
                    Book INTEGER NOT NULL,
                    Price REAL NOT NULL,
                    Status TEXT DEFAULT 'Available',
                    Seller_id INTEGER,
                    Buyer_id INTEGER,
                    FOREIGN KEY (Seller_id) REFERENCES customers(Id),
                    FOREIGN KEY (Book) REFERENCES Book(Id)
                    FOREIGN KEY (Buyer_id) REFERENCES customers(Id)
                );
            """)

        self.execute("""
                CREATE TABLE IF NOT EXISTS customers (
                Id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL, -- Name of the user, cannot be NULL
                address TEXT NOT NULL,
                wallet INTEGER DEFAULT 0,
                club_member TEXT DEFAULT 'NO',
                is_vendor TEXT DEFAULT 'NO',
                data_sharing_level TEXT DEFAULT 'NONE',  -- NONE/BASIC/STANDARD/FULL
                created_at DATETIME
                );
                """)

        # New table for marketing data
        self.execute(""" CREATE TABLE IF NOT EXISTS user_activity ( 
                        Id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        customer_id INTEGER NOT NULL, 
                        activity_type TEXT NOT NULL,
                        activity_data TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP, 
                        FOREIGN KEY (customer_id) REFERENCES customers(Id) ); 
                     """)

    def connect(self):
        self.conn = sqlite3.connect("DataBase.sqlite")

    def execute(self, sql, val=None):
        cursor = self.conn.cursor()
        if val:
            cursor.execute(sql, val)
        else:
            cursor.execute(sql)
        self.conn.commit()

        return cursor

    def commit(self):
        self.conn.commit()

    def addMoney(self, money, customer_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE customers SET wallet = customers.wallet + ? WHERE Id = ?", (money, customer_id))
        self.conn.commit()

    def removeMoney(self, money, customer_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE customers SET wallet = customers.wallet - ? WHERE Id = ?", (money, customer_id))
        self.conn.commit()

    def addClubMember(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE customers SET club_member = ? WHERE Id = ?", ("YES", customer_id))
        self.conn.commit()

    def deleteClubMember(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE customers SET club_member = ? WHERE Id = ?", ("NO", customer_id))
        self.conn.commit()

    def insertIntoBookTable(
                  self,
                  Title,
                  Author,
                  Created,
                  Edition,
                  Publisher,
                  Book_condition,
                  Description):
        self.execute("INSERT INTO books (Title, Author, Created, Edition, Publisher, Book_condition, Description) VALUES (?, ?, ?, ? ,? ,? ,?)", (Title,
                  Author,
                  Created,
                  Edition,
                  Publisher,
                  Book_condition,
                  Description))

        cursor = self.execute("SELECT * from books order by Id desc limit 1")
        return cursor.fetchone()[0]

    def insertIntoOfferTable(self,
            Book,
            Price,
            Status,
            Seller_id
            ):
        self.execute("INSERT INTO offers (Book, Price, Status ,Seller_id) VALUES (?, ?, ?, ?)",
                     (  Book,
                            Price,
                            Status,
                            Seller_id))

    def lookupExistingCustomer(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM customers WHERE username = ? LIMIT 1", (username,))
        return cursor.fetchone() is not None

    def getCustomerDetail(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM customers WHERE username = ? LIMIT 1", (username,))
        return cursor.fetchone()

    def getPriceOfBookIfAvailable(self, book_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT Price from books left join offers on offers.Book = books.id where books.id = ? and offers.Status = ?",
            (book_id, "Available"))
        result = cursor.fetchone()
        return result if result is None else result[0]

    def getBookDetail(self, book_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * from books where id = ?", (book_id,))
        result = cursor.fetchone()
        return result if result is None else result

    def setVendor(self, customer_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE customers SET is_vendor = ? WHERE Id = ?", ("YES", customer_id))
        self.conn.commit()

    def filterBook(self,
                   Title,
                   Author,
                   Created,
                   Edition,
                   Publisher,
                   Book_condition,
                   Description):

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT Id, Title,
                   Author,
                   Created,
                   Edition,
                   Publisher,
                   Book_condition,
                   Description,
                   Price FROM (SELECT * FROM (SELECT * FROM offers left join books ON offers.Book = books.Id) WHERE Status = "Available")
            WHERE 
                  Title LIKE ?
              And Author LIKE ?
              AND Created LIKE ?
              AND Edition LIKE ?
              AND Publisher LIKE ?
              AND Book_condition LIKE ?
              AND Description LIKE ?
        """, (
            f"%{Title}%",
            f"%{Author}%",
            f"%{Created}%",
            f"%{Edition}%",
            f"%{Publisher}%",
            f"%{Book_condition}%",
            f"%{Description}%"
        ))

        return cursor.fetchall()

    def setBookAsPurchased(self, Book, Buyer_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM offers WHERE Book = ? and Status = ?", (Book, "Available"))

        foundOffer = cursor.fetchone()

        if foundOffer is not None:
            cursor.execute("UPDATE offers SET Status = ?, Buyer_id = ? WHERE Book = ?", ("Sold", Buyer_id, Book))
            self.conn.commit()
        else:
            print("The book is not available")

    def setDataSharingLevel(self, customer_id, level):
        """Set data sharing level: NONE, BASIC, STANDARD, or FULL"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE customers SET data_sharing_level = ? WHERE Id = ?",
                       (level, customer_id))
        self.conn.commit()

    def trackUserInterest(self, customer_id: int, activity_type: str, activity_data: Dict[str, Any]):
        """Track user activity for marketing purposes if they consented"""
        cursor = self.conn.cursor()

        # Check if user consented to data sharing
        cursor.execute("SELECT data_sharing_level FROM customers WHERE Id = ?", (customer_id,))
        sharing_level = cursor.fetchone()[0]

        if sharing_level != 'NONE':
            # Filter data based on sharing level
            filtered_data = _filter_data_by_sharing_level(activity_data, sharing_level)

            cursor.execute(
                "INSERT INTO user_activity (customer_id, activity_type, activity_data) VALUES (?, ?, ?)",
                (customer_id, activity_type, str(filtered_data)))
            self.conn.commit()

db = DataBase()