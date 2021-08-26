from uuid import uuid4
import json
from fastapi import FastAPI, HTTPException, Depends, Form
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import bcrypt
import jwt
import database as db
import models
import logging

logger = logging.getLogger("controller")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("controller.log")
logger.addHandler(file_handler)
formatter = logging.Formatter("%(asctime)s: "
                              "%(levelname)s: "
                              "%(name)s: "
                              "%(message)s")
file_handler.setFormatter(formatter)

app = FastAPI()

origins = [
    "http://localhost:3000",
    "https://couchfest.herokuapp.com",
    "https://couchtest.herokuapp.com"
]

url_match = r"http://localhost:3000/?.*|" \
            r"https?://couchfest.herokuapp.com/?.*|" \
            r"https?://couchtest.herokuapp.com/?.*|"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=url_match,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/token')
JWT_SECRET = "CouchFestWebToken"


@app.post("/api/token")
async def generate_token(form_data: OAuth2PasswordRequestForm = Depends()):
    logger.info("Generating a token to identify user.")
    user_object = await db.fetch_credential(form_data.username)
    form_password = form_data.password
    user_credential = user_object.get("credential")
    is_valid = bcrypt.checkpw(form_password.encode(), user_credential.encode())
    if is_valid:
        _object = {
            "UserID": user_object.get("UserID"),
            "Username": user_object.get("Username"),
        }
        token = jwt.encode(_object, JWT_SECRET)
        return {
            "access_token": token,
            "token_type": "bearer"
        }
    return {
        "error": "Authentication failed! "
                 "Please enter your correct credentials."
    }


def generate_new_id(objects, identifier, model):
    logger.info(f"Generating new ID for {model}")
    if not objects:
        return "1"
    all_ids = sorted([i.get(identifier) for i in objects])
    if model.lower() == "events":
        all_ids = sorted([i.get(identifier).split("A")[-1] for i in objects])
        return f"A{str(int(all_ids[-1]) + 1)}"
    return str(int(all_ids[-1]) + 1)


@app.get("/api")
def read_root():
    return JSONResponse(status_code=200, content={"message": "API is working"})


@app.post("/api/create_user", response_model=models.Users)
async def create_user(
        firstname: str = Form(...),
        lastname: str = Form(...),
        username: str = Form(...),
        email: str = Form(...),
        password: str = Form(...)):

    _user = {
        "FirstName": firstname,
        "LastName": lastname,
        "Username": username,
        "Email": email,
    }
    logger.info("Creating a new user")
    # _user = user_object.dict(by_alias=True)
    users = await db.fetch_users()
    user_id_key = "UserID"
    new_user_id = generate_new_id(users, user_id_key, "Users")
    user_id = _user.get(user_id_key)
    if user_id is None:
        _user[user_id_key] = new_user_id
    else:
        id_response = await db.fetch_user(user_id)
        if id_response:
            raise HTTPException(409,
                                f"Conflict: User with ID {user_id} "
                                f"already exists! Try again")
    user_name = _user.get("Username")
    user_email = _user.get("Email")
    name_response = await db.fetch_user(user_name, by_id=False)
    email_response = await db.fetch_user_by_email(user_email)
    if name_response:
        raise HTTPException(409,
                            f"Conflict: User with username {user_name} "
                            f"already exists! Try again")
    if email_response:
        raise HTTPException(409,
                            f"Conflict: User with email {user_email} "
                            f"already exists! Try again")
    else:
        _user["AccountType"] = "Normal user"
        _user["PaymentType"] = uuid4().hex
        _user["MyEvents"] = []
        _user["MyTickets"] = []
        _user["MyGenres"] = []
        _user["InCart"] = []
        _user["IsAdmin"] = False
        _hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        _credential = {
            "UserID": new_user_id,
            "Username": username,
            "credential": _hashed.decode()
        }
        create_response = await db.create_user(_user)
        if create_response:
            add_login = await db.add_credential(_credential)
            _created = await db.fetch_user(create_response.get(user_id_key))
            if _created:
                _added = await db.fetch_credential(add_login.get("Username"))
                if _added:
                    return create_response

            error_message = {"error": "Couldn't create new user"}
            return error_message

    raise HTTPException(400, f"Bad request.")


@app.get("/api/users")
async def get_users():
    # logger.info("Getting all users")
    response = await db.fetch_users()
    if response:
        return JSONResponse(status_code=200, content=response)
    raise HTTPException(404, f"Users not found here.")


async def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    # user = db.query(_models.User).get(payload["id"])
    # response = await db.fetch_user(payload.get("Username"), by_id=False)
    logger.info("Getting currently logged in user.")
    response = await db.fetch_user(payload.get("UserID"))
    logger.info(response)
    if response:
        return response
    raise HTTPException(status_code=401, detail="Invalid Credentials")


@app.post("/api/user/verify", response_model=models.Credentials)
# async def verify_user(form_data: OAuth2PasswordRequestForm = Depends()):
async def verify_user(form_data: models.Credentials):
    _data = form_data.dict(by_alias=True)
    response = await db.fetch_credential(_data.get("Username"))
    # response = await db.fetch_credential(form_data.username)
    if response:
        return response
    raise HTTPException(404, f"Credentials not found here.")


@app.get("/api/users/me", response_model=models.Users)
async def get_user(user: models.Users = Depends(get_current_user)):
    return user


@app.post("/api/user/authenticate")
async def authenticate_user(form_data: models.LoginForm):
    _data = form_data.dict(by_alias=True)
    user_object = await db.fetch_credential(_data.get("username"))
    form_password = _data.get("password")
    user_credential = user_object.get("credential")
    is_valid = bcrypt.checkpw(form_password.encode(), user_credential.encode())
    if is_valid:
        _object = {
            "UserID": user_object.get("UserID"),
            # "Username": user_object.get("Username"),
        }
        token = jwt.encode(_object, JWT_SECRET)
        return JSONResponse(status_code=200, content={
            "access_token": token,
            "token_type": "bearer"
        })
    return JSONResponse(status_code=500, content={
        "error": "Authentication failed! "
                 "Please enter your correct credentials."
    })


@app.get("/api/user/id/{user_id}", response_model=models.Users)
async def get_user_by_id(user_id):
    logger.info(f"Getting user by ID: {user_id}")
    response = await db.fetch_user(user_id)
    if response:
        return response
    raise HTTPException(404, f"User with ID {user_id} not found here.")


@app.get("/api/user/email/{user_email}", response_model=models.Users)
async def get_user_by_id(user_email):
    logger.info(f"Getting user by Email: {user_email}")
    response = await db.fetch_user_by_email(user_email)
    if response:
        return response
    raise HTTPException(404, f"User with email {user_email} not found here.")


@app.get("/api/user/name/{user_name}", response_model=models.Users)
async def get_user_by_name(user_name):
    logger.info(f"Getting user by UserName: {user_name}")
    response = await db.fetch_user(user_name, by_id=False)
    if response:
        return response
    raise HTTPException(404, f"User with ID {user_name} not found here.")


@app.put("/api/user/id/{user_id}", response_model=models.Users)
async def update_user_by_id(user_object: models.Users):
    # _obj = json.loads(jsonable_encoder(new_object))
    _obj = user_object.dict(by_alias=True)
    user_id = _obj.get("UserID")
    logger.info(f"Updating user by ID: {user_id}")
    in_cart = _obj.get("InCart")
    if in_cart:
        _obj["InCart"] = list(set(_obj["InCart"]))
    response = await db.fetch_user(user_id)
    if response:
        _updated = await db.update_user({"UserID": user_id}, _obj)
        return _updated
    raise HTTPException(404, f"User with ID {user_id} not found here.")


@app.put("/api/user/name/{user_name}", response_model=models.Users)
async def update_user_by_name(user_object: models.Users):
    _obj = user_object.dict(by_alias=True)
    user_name = _obj.get("Username")
    logger.info(f"Updating user by UserName: {user_name}")
    response = await db.fetch_user(user_name, by_id=False)
    if response:
        _updated = await db.update_user({"Username": user_name}, user_object)
        return _updated
    raise HTTPException(404, f"User with username {user_name} not found here.")


@app.delete("/api/user/id/{user_id}", response_model=models.Users)
async def delete_user_by_id(user_id):
    logger.info(f"Deleting user by ID: {user_id}")
    response = await db.fetch_user(user_id)
    if response:
        q = {"UserID": user_id}
        delete_response = await db.delete_user(q)
        if delete_response:
            remove_credential = await db.delete_credential(q)
            if remove_credential:
                return response
    raise HTTPException(404, f"User with ID {user_id} not found here.")


@app.delete("/api/user/name/{user_name}", response_model=models.Users)
async def delete_user_by_name(user_name):
    logger.info(f"Deleting user by UserName: {user_name}")
    response = await db.fetch_user(user_name, by_id=False)
    if response:
        delete_response = await db.delete_user({"Username": user_name})
        if delete_response:
            return response
    raise HTTPException(404, f"User with username {user_name} not found here.")


@app.post("/api/create_event/", response_model=models.Events)
async def create_event(event_object: models.Events):
    # _event = json.loads(jsonable_encoder(event_object))
    logger.info("Creating event")
    _event = event_object.dict(by_alias=True)
    events = await db.fetch_events()
    event_id_key = "EventID"
    new_event_id = generate_new_id(events, event_id_key, "Events")
    event_id = _event.get(event_id_key)
    if event_id is None:
        _event[event_id_key] = new_event_id
    else:
        id_response = await db.fetch_event(event_id)
        if id_response:
            raise HTTPException(409,
                                f"Conflict: Event with ID {event_id} "
                                f"already exists! Try again")
    event_name = _event.get("EventName")
    name_response = await db.fetch_event(event_name, by_id=False)
    if name_response:
        raise HTTPException(409,
                            f"Conflict: Event with event name {event_name} "
                            f"already exists! Try again")

    else:
        create_response = await db.create_event(_event)
        if create_response:
            _created = await db.fetch_event(create_response.get(event_id_key))
            if _created:
                return create_response

            error_message = {"error": "Couldn't create new event"}
            return error_message

    raise HTTPException(400, f"Bad request.")


@app.post("/api/save_contact_us/", response_model=models.ContactUs)
async def create_contact_form(form_object: models.ContactUs):
    # _event = json.loads(jsonable_encoder(event_object))
    logger.info("Creating Contact Us")
    _obj = form_object.dict(by_alias=True)
    forms = await db.fetch_contact_forms()
    id_key = "FormID"
    new_form_id = generate_new_id(forms, id_key, "ContactUs")
    form_id = _obj.get(id_key)
    if form_id is None:
        _obj[id_key] = new_form_id
    else:
        id_response = await db.fetch_contact_form(form_id)
        if id_response:
            raise HTTPException(409,
                                f"Conflict: Contact Form with ID {form_id} "
                                f"already exists! Try again")

    create_response = await db.create_contact_form(_obj)
    logger.info(f"create_response: {create_response}")
    if create_response:
        _created = await db.fetch_contact_form(create_response.get(id_key))
        if _created:
            return create_response

        error_message = {"error": "Couldn't create contact form"}
        return error_message

    raise HTTPException(400, f"Bad request.")


@app.get("/api/get_contact_us")
async def get_contact_forms():
    logger.info("Getting ContactUs forms")
    response = await db.fetch_contact_forms()
    if response:
        return response
    raise HTTPException(404, f"Contact Us forms not found here: {response}")


@app.get("/api/events")
async def get_events():
    # logger.info("Getting Events")
    response = await db.fetch_events()
    if response:
        return response
    raise HTTPException(404, f"Events not found here: {response}")


@app.get("/api/event/id/{event_id}", response_model=models.Events)
async def get_event_by_id(event_id):
    logger.info(f"Getting Event by ID: {event_id}")
    response = await db.fetch_event(event_id)
    if response:
        return response
    raise HTTPException(404, f"Event with ID {event_id} not found here.")


@app.get("/api/event/name/{event_name}", response_model=models.Events)
async def get_event_by_name(event_name):
    logger.info(f"Getting Events by name: {event_name}")
    response = await db.fetch_event(event_name, by_id=False)
    if response:
        return response
    raise HTTPException(404, f"Event with name {event_name} not found here.")


@app.put("/api/event/id/{event_id}", response_model=models.Events)
async def update_event_by_id(event_object: models.Events):
    # _obj = json.loads(jsonable_encoder(new_object))
    logger.info("Updating event")
    _event = event_object.dict(by_alias=True)
    logger.info(_event)
    event_id_key = "EventID"
    event_id = _event.get(event_id_key)
    response = await db.fetch_event(event_id)
    if response:
        _updated = await db.update_event({event_id_key: event_id}, _event)
        return _updated
    raise HTTPException(404, f"Event with ID {event_id} not found here.")


@app.put("/api/event/name/{event_name}", response_model=models.Events)
async def update_event_by_name(event_name, new_object):
    response = await db.fetch_event(event_name, by_id=False)
    if response:
        _updated = await db.update_event({"EventName": event_name}, new_object)
        return _updated
    raise HTTPException(404, f"Event with name {event_name} not found here.")


@app.delete("/api/event/id/{event_id}", response_model=models.Events)
async def delete_event_by_id(event_id):
    logger.info(f"Deleting Event by ID: {event_id}")
    response = await db.fetch_event(event_id)
    if response:
        delete_response = await db.delete_event({"EventID": event_id})
        if delete_response:
            return response
    raise HTTPException(404, f"Event with ID {event_id} not found here.")


@app.delete("/api/event/name/{event_name}", response_model=models.Events)
async def delete_event_by_name(event_name):
    response = await db.fetch_event(event_name, by_id=False)
    if response:
        delete_response = await db.delete_event({"EventName": event_name})
        if delete_response:
            return response
    raise HTTPException(404, f"Event with name {event_name} not found here.")


@app.get("/api/tickets")
async def get_tickets():
    logger.info("Getting Tickets")
    response = await db.fetch_tickets()
    if response:
        return response
    raise HTTPException(404, f"Tickets not found here.")
