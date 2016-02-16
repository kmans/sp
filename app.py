import csv
import os
from hotfuzz import token_set_ratio

from flask import Flask, jsonify, abort, request
from flask_restful import Resource, Api, marshal_with, fields, reqparse
from flask_sqlalchemy import SQLAlchemy

from art import artSearch

app = Flask(__name__)

# setup configs
app.config.update(
    SECRET_KEY="RSdVWDXDT7fPTyhnxnglpbGZhKqMJxmbtjOQftSm4pXFLe9YRfQlJtYNNnhkjbN",
    SQLALCHEMY_DATABASE_URI="sqlite:///southpark.db",
    STATIC_ROOT=None,
    )

# API
api = Api(app)

# initialize database
db = SQLAlchemy(app)

#######################################
# MODELS                              #
#######################################
# Base = declarative_base()


class SouthPark(db.Model):
    # Tell SQLAlchemy what the table name is and if there's any table-specific arguments it should know about
    __tablename__ = 'southpark'
    __table_args__ = {'sqlite_autoincrement': True}
    # tell SQLAlchemy the name of column and its attributes:
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    season = db.Column(db.Integer)
    episode = db.Column(db.Integer)
    character = db.Column(db.Unicode(length=64))
    line = db.Column(db.UnicodeText)

# create all of the above tables (if more than one)
# Base.metadata.create_all(engine)

db.create_all()

#######################################
# FUNCTIONS                           #
#######################################


def populateData():
    # session = Session()

    # Commit the CSV data to the database
    for filename in os.listdir('./csv/'):
        seasonnum = int(filename[:-4].split('-')[1])
        if not db.session.query(SouthPark).filter(SouthPark.season == seasonnum).first():
            print('Committing data for Season {}...'.format(seasonnum))
            commitData(filename)
        else:
            print('*Skipping data for Season {}*'.format(seasonnum))


def commitData(filename):
    # Create the session object
    # session = Session()

    with open('./csv/' + filename, 'r') as csvfile:
        season = csv.reader(csvfile, delimiter=',', quotechar='\"')
        # headers should be "Season, Episode, Character, Line"
        headers = next(season)

        data = list(season)

        for d in data:
            record = SouthPark(
                season=int(d[0]),
                episode=int(d[1]),
                character=d[2].decode(errors="ignore"),
                line=d[3].decode(errors="ignore"),
            )

            # Add all the records
            db.session.add(record)

        # Attempt to commit all the records
        db.session.commit()

    # session.close()


def fixData(data):
    for item in data:
        if item['_sa_instance_state']:
            del item['_sa_instance_state']
        elif item['_labels']:
            del item['_labels']
    return data


def queryData(query):
    # session = Session()
    # remove common special characters from the query to normalize it a bit
    query = unicode(query).translate({ord(i): None for i in '!@#$%^&*()-+="~`;/'})
    # simplified query by adding % around each word to only grab the most suitable matches
    words = query.split()
    likequery = " ".join(map(lambda f: '%'+f+'%', words))
    records = db.session.query(SouthPark).filter(SouthPark.line.ilike(likequery)).all()

    # if we get something back, return the best 5 results
    if records:
        v = sorted(records, key=lambda j: token_set_ratio(query, j.__dict__['line'].split()), reverse=True)
        results = map(lambda q: q.__dict__, v[0:5])

        for quote in results:
            quote['art'] = artSearch(quote)
        return results
    else:
        return []


#######################################
# RESTFUL API                         #
#######################################


resource_fields = {

    'season': fields.Integer,
    'episode': fields.Integer,
    'character': fields.String,
    'line': fields.String,
    'art': fields.Url,
}


class FindQuotes(Resource):
    @marshal_with(resource_fields)
    def get(self, query):
        data = queryData(query)
        if data == []:
            return {}
        else:
            return data

api.add_resource(FindQuotes, '/query/<query>')


if __name__ == "__main__":

    # populateData()
    print 'Call populateData() to repopulate the database from the CSV dir'

    app.run(debug=True)
