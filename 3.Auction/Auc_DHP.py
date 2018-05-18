from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine, MetaData, Table, exc

from datetime import datetime as dt

app = Flask(__name__)

app.config.from_pyfile('config.cfg')
db = SQLAlchemy(app)

engine = create_engine("postgres://postgres:123456@localhost:5432/auction")

# TODO: after 28/3, add "Class" to all the Classes' name
# to understand the distinguished values passed to Column, FK, db.relationship:
# which to pass a table's name with columns,
# which to pass a Class name with attributes


class Item(db.Model):
    __tablename__ = 'item'
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    name = Column("Name", String, nullable=False)
    desc = Column("Description", String, nullable=False)
    start_time = Column("Start time", DateTime, nullable=False)
    # user.ID => Auction by : 1-m
    auction_by = Column("Auction by", Integer, ForeignKey('user.ID'), nullable=True)

    init_price = Column("Initial Price", Float, nullable=False)
    # User - Item : m-n => Bid
    item = db.relationship('Bid', backref='Item', lazy=True)

    @staticmethod
    def get_time():
        """
        :return: (String) time of execution in format 'dd/mm/yyyy hh:mm:ss'
        """
        now = dt.now()
        return now.strftime('%d/%m/%Y %H:%M:%S')

    def __init__(self, name, desc, init_price, auction_by=None):
        """
        :param name: (str) name of the item
        :param desc: (str) description of the item
        :param init_price: (float) Initial price in VND
        :param auction_by: (int) id of the user that auction the item.
        """
        self.name = name
        self.desc = desc
        self.init_price = init_price
        self.auction_by = auction_by
        self.start_time = self.get_time()
        db.session.add(self)


class User(db.Model):
    __tablename__ = 'user'
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    username = Column("Username", String, nullable=False, unique=True)
    password = Column("Password", String, nullable=False)
    # user.ID => Auction by : 1-m
    item = db.relationship('Item', backref='User', lazy=True)
    # User - Item : m-n => Bid
    bid = db.relationship('Bid', backref='User', lazy=True)

    def __init__(self, username, password):
        """
        :param username: (str) username must be unique
        :param password: (str)
        """
        self.username = username
        self.password = password
        db.session.add(self)

    # def __repr__(self):
    #     return "<User(name='%s', password='%s')>" % (
    #         self.username, self.password)


class Bid(db.Model):
    __tablename__ = 'bid'
    id = Column('ID', Integer, primary_key=True, autoincrement=True)
    # User - Item : m-n => Bid
    user_id = Column("User ID", Integer, ForeignKey("user.ID"), nullable=False)
    item_id = Column("Item ID", Integer, ForeignKey("item.ID"), nullable=False)

    price = Column("Price", Float, nullable=False)

    def __init__(self, user_id, item_id, price):
        """
        :param user_id: (int) Table User => column ID
        :param item_id: (int) Table Item => column ID
        :param price: (float) Bidding price in VND
        """
        self.user_id = user_id
        self.item_id = item_id
        self.price = price
        db.session.add(self)


def delete_table(table_name):
    """
    :param table_name: (String) name of the table to delete
    Delete the table if it's existed.
    """
    # table_is_exist = engine.dialect.has_table(engine.connect(),table_name)
    metadata = MetaData(engine)

    try:
        table = Table(table_name, metadata, autoload=True)
        table.drop(engine)
    except exc.NoSuchTableError:
        print(table_name, "table is not existed")


def find_winner_of(item_id):
    """
    Print a line that show item name, winner's username and the highest price.
    The winning (highest) price must higher than init_price in Item table, else print
    a result line of bidding failure.
    :param item_id: (int) ID of the item that need to find the winner of.
    """
    # get the list of all records that bid the item_id
    bidding_list = Bid.query.filter_by(item_id=item_id).all()

    if bidding_list is not None:
        # From bidding_list in the Bid table, get highest price record
        bid_win_row = max(bidding_list, key=lambda row: row.price)
        highest_price = bid_win_row.price

        # if below is True, print a notification and stop the function
        floor_price = Item.query.filter_by(id=item_id).first().init_price
        if highest_price < floor_price:
            print("There must be at least a bidder giving a price", end=' ')
            print("that higher than the floor price of the item")
            return

        # From User table, get the record of the winner then get the username
        winner_id = bid_win_row.user_id
        user_win_row = User.query.filter_by(id=winner_id).first()
        winner_username = user_win_row.username

        # from Item table, get the record of the bid item then get the name
        item_row = Item.query.filter_by(id=item_id).first()
        item_name = item_row.name
        print("The person getting the {} is {} with the price of {} VND"
              .format(item_name, winner_username, highest_price))
    else:
        print("the input item ID is not available ")


# ##### TEST AREA ##### #

# delete table in db before recreate all
delete_table("bid")
delete_table("item")
delete_table("user")

db.create_all()


# create 3 users
steve_jobs =   User(username='Steve Jobs', password='di tim viec')
bill_gates =   User(username='Bill Gates', password='hoa don tien dien')
cat =          User(username='boss',       password='meow')
# db.session.add(self) is implemented in __init__
db.session.commit()

# create item baseball
baseball = Item("baseball", "Orange, round-shaped", 100_000, cat.id)

db.session.commit()

# create bidding
bill_1 =    Bid(bill_gates.id, baseball.id,  40_000)
steve_1 =   Bid(steve_jobs.id, baseball.id,  50_000)
cat_1 =     Bid(cat.id,        baseball.id,  20_000)
steve_2 =   Bid(steve_jobs.id, baseball.id, 150_000)
bill_2 =    Bid(bill_gates.id, baseball.id, 160_000)
cat_2 =     Bid(cat.id,        baseball.id,  10_000)

db.session.commit()

# query the winner of item_id = 1 (baseball)
find_winner_of(1)
