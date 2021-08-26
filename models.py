from pydantic import BaseModel, Field
from typing import Any


class Users(BaseModel):
    UserID: Any
    Username: Any
    FirstName: Any
    LastName: Any
    Email: Any
    AccountType: Any
    PaymentType: Any
    MyEvents: Any
    MyTickets: Any
    IsAdmin: Any
    MyGenres: Any
    InCart: Any

    class Config:
        allow_population_by_field_name = True


class Events(BaseModel):
    EventID: Any
    EventName: Any
    EventDescription: Any
    Venue: Any
    Artists: Any
    EventDate: Any
    EventTime: Any
    EventEndTime: Any
    EventType: Any
    Price: Any
    GenreID: Any
    Image: Any
    Genres: Any
    IsHero: Any
    HostName: Any
    specialNote: Any
    headlineArtist: Any


class Tickets(BaseModel):
    TicketNumber: Any
    EventID: Any
    UserID: Any
    PaymentMethod: Any
    PurchaseDate: Any


class Credentials(BaseModel):
    UserID: str
    Username: str
    credential: str


class LoginForm(BaseModel):
    username: str
    password: str


class UserRegistration(BaseModel):
    firstname: str
    lastname: str
    username: str
    email: str
    password: str


class ContactUs(BaseModel):
    FormID: Any
    Name: Any
    PhoneNumber: Any
    Email: Any
    Subject: Any
    Message: Any
