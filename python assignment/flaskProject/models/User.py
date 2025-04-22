import mongoengine as db
class User(db.Document):
    id = db.StringField(primary_key=True)
    username = db.StringField(required=True)
    email = db.StringField(required=True)
    password = db.StringField(required=True)



