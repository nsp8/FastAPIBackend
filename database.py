# from os import environ
import motor.motor_asyncio
from constants import TEST_DB, PROD_DB, MODE
import models
import logging

logger = logging.getLogger("database")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("database.log")
logger.addHandler(file_handler)
formatter = logging.Formatter("%(asctime)s: "
                              "%(levelname)s: "
                              "%(name)s: "
                              "%(message)s")
file_handler.setFormatter(formatter)

mongo_connection = PROD_DB if MODE == 1 else TEST_DB
client = motor.motor_asyncio.AsyncIOMotorClient(mongo_connection)
database = client.CouchFest if MODE == 1 else client.couchtest


async def fetch_user(prop, by_id=True):
    query = {"UserID": prop}
    if not by_id:
        query = {"Username": prop}
    doc = await database.Users.find_one(query)
    return doc


async def fetch_credential(username):
    logger.info(f"Fetching credential for: {username}")
    query = {"Username": username}
    doc = await database.Credentials.find_one(query)
    return doc


async def fetch_user_by_email(user_email):
    query = {"Email": user_email}
    doc = await database.Users.find_one(query)
    return doc


async def fetch_users():
    users = list()
    cursor = database.Users.find({})
    async for doc in cursor:
        users.append(models.Users(**doc).dict(by_alias=True))
    return users


async def fetch_credentials():
    users = list()
    cursor = database.Credentials.find({})
    async for doc in cursor:
        users.append(models.Credentials(**doc).dict(by_alias=True))
    return users


async def create_user(user_object):
    result = await database.Users.insert_one(user_object)
    if result:
        return user_object
    return None


async def add_credential(user_object):
    logger.info("Adding credentials for user")
    result = await database.Credentials.insert_one(user_object)
    if result:
        logger.info("Credential added!")
        return user_object
    return None


async def update_user(criteria, user_object):
    result = await database.Users.update_one(criteria, {"$set": user_object})
    if result:
        document = await database.Users.find_one(criteria)
        return document
    return None


async def delete_user(criteria):
    count_prev = await database.Users.count_documents({})
    document = await database.Users.find_one(criteria)
    result = await database.Users.delete_one(criteria)
    if result:
        count_now = await database.Users.count_documents({})
        _diff = count_prev - count_now
        _message = "document" if _diff == 1 else "documents"
        logger.info(f"{_diff} {_message} deleted from Users.")
        if _diff == 1:
            return document
        return None
    return None


async def delete_credential(criteria):
    count_prev = await database.Credentials.count_documents({})
    document = await database.Credentials.find_one(criteria)
    result = await database.Credentials.delete_one(criteria)
    if result:
        count_now = await database.Credentials.count_documents({})
        _diff = count_prev - count_now
        _message = "document" if _diff == 1 else "documents"
        logger.info(f"{_diff} {_message} deleted from Credentials.")
        if _diff == 1:
            return document
        return None
    return None


async def delete_contact_form(criteria):
    count_prev = await database.ContactUs.count_documents({})
    document = await database.ContactUs.find_one(criteria)
    result = await database.ContactUs.delete_one(criteria)
    if result:
        count_now = await database.ContactUs.count_documents({})
        _diff = count_prev - count_now
        _message = "document" if _diff == 1 else "documents"
        logger.info(f"{_diff} {_message} deleted from ContactUs.")
        if _diff == 1:
            return document
        return None
    return None


async def fetch_events():
    events = list()
    cursor = database.Events.find({})
    async for doc in cursor:
        events.append(models.Events(**doc).dict(by_alias=True))
    return events


async def fetch_contact_forms():
    forms = list()
    cursor = database.ContactUs.find({})
    async for doc in cursor:
        forms.append(models.ContactUs(**doc).dict(by_alias=True))
    return forms


async def fetch_tickets():
    tickets = list()
    cursor = database.Tickets.find({})
    async for doc in cursor:
        tickets.append(models.Tickets(**doc).dict(by_alias=True))
    return tickets


async def create_event(event_object):
    result = await database.Events.insert_one(event_object)
    if result:
        return event_object
    return None


async def create_contact_form(form_object):
    result = await database.ContactUs.insert_one(form_object)
    if result:
        return form_object
    return None


async def fetch_event(prop, by_id=True):
    query = {"EventID": prop}
    if not by_id:
        query = {"EventName": prop}
    doc = await database.Events.find_one(query)
    return doc


async def fetch_contact_form(prop):
    query = {"FormID": prop}
    # if not by_id:
    #     query = {"EventName": prop}
    doc = await database.ContactUs.find_one(query)
    return doc


async def delete_event(criteria):
    count_prev = await database.Events.count_documents({})
    document = await database.Events.find_one(criteria)
    result = await database.Events.delete_one(criteria)
    if result:
        count_now = await database.Events.count_documents({})
        _diff = count_prev - count_now
        _message = "document" if _diff == 1 else "documents"
        logger.info(f"{_diff} {_message} deleted from Events.")
        if _diff == 1:
            return document
        return None
    return None


async def update_event(criteria, event_object):
    result = await database.Events.update_one(criteria, {"$set": event_object})
    if result:
        document = await database.Events.find_one(criteria)
        return document
    return None
