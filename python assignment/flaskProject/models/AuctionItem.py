from app import db

class AuctionItem(db.Document):
    id = db.StringField(primary_key=True)
    item_name = db.StringField()