from flask import Flask
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

dbb = SQLAlchemy()







class Users(UserMixin ,dbb.Model):

    __tablename__ = 'users'


    id = dbb.Column(dbb.Integer, primary_key=True)
    username = dbb.Column(dbb.String(15), unique=True, nullable=False)
    email = dbb.Column(dbb.String(120), unique=True, nullable=False)
    password = dbb.Column(dbb.String(120), nullable=False)
    address = dbb.Column(dbb.String(150))
    phone = dbb.Column(dbb.Integer, unique=True)



    exps = dbb.relationship('Experience', back_populates='user', cascade='all, delete-orphan')
    edus = dbb.relationship('Education', back_populates='user',  cascade='all, delete-orphan')
    proj = dbb.relationship('Projects', back_populates='user', cascade='all, delete-orphan')
    acts = dbb.relationship('Activites_and_Interests', back_populates='user',   cascade='all, delete-orphan')
    refs = dbb.relationship('References', back_populates='user', cascade='all, delete-orphan')
    # Add this to your Users class
    conversations = dbb.relationship('Conversations', back_populates='user', cascade='all, delete-orphan')    


    def __repr__(self):
        return f'<User {self.username}>'
    

class Experience(dbb.Model):

    __tablename__ = 'experiences'


    id = dbb.Column(dbb.Integer, primary_key=True)
    user_id = dbb.Column(dbb.Integer, dbb.ForeignKey('users.id'), nullable=False)
    detail = dbb.Column(dbb.String, nullable = True)
    skills = dbb.Column(dbb.String, nullable= True)

    user = dbb.relationship('Users', back_populates='exps')

    def __repr__(self):
        return f'<Experience {self.id} for User {self.user_id}>'
    


class Education(dbb.Model):
    
    __tablename__ = 'education'

    ed_id = dbb.Column(dbb.Integer, primary_key=True)
    user_id = dbb.Column(dbb.Integer, dbb.ForeignKey('users.id'), nullable=False)
    detail =  dbb.Column(dbb.Text , nullable = False)

    user = dbb.relationship('Users', back_populates='edus')

    def __repr__(self):
        return f'<Education {self.ed_id} for User{self.user_id} >'



class Projects(dbb.Model):

    __tablename__='projects'

    proj_id = dbb.Column(dbb.Integer, primary_key=True)
    user_id = dbb.Column(dbb.Integer, dbb.ForeignKey('users.id'), nullable=False)
    detail =  dbb.Column(dbb.String(400), nullable = False)
    

    user = dbb.relationship('Users', back_populates='proj') 


    def __repr__(self):
        return f'<Project {self.proj_id} for User{self.user_id} >'



class Activites_and_Interests(dbb.Model):

    
    __tablename__ = 'activities'
    
    
    
    act_id = dbb.Column(dbb.Integer, primary_key=True)
    detail =  dbb.Column(dbb.Text, nullable = False)
    user_id = dbb.Column(dbb.Integer, dbb.ForeignKey('users.id'), nullable=False)

    user = dbb.relationship('Users', back_populates='acts') 



    def __repr__(self):
        return f'<Activites and interest {self.act_id} for User{self.user_id} >'




class References(dbb.Model):

    __tablename__ = 'refs'


    ref_id = dbb.Column(dbb.Integer, primary_key=True)
    detail =  dbb.Column(dbb.Text, nullable = False)
    user_id = dbb.Column(dbb.Integer, dbb.ForeignKey('users.id'), nullable=False)


    user = dbb.relationship('Users', back_populates='refs') 


    def __repr__(self):
        return f'<References {self.ref_id} for User{self.user_id} >'




class Conversations(dbb.Model):

    __tablename__ = 'conversations_users'


    conv_id = dbb.Column(dbb.Integer, primary_key=True)
    user_id = dbb.Column(dbb.Integer, dbb.ForeignKey('users.id'), nullable=False)
    title = dbb.Column(dbb.String(200), nullable=True )
    created_at = dbb.Column(dbb.DateTime, default=lambda: datetime.now(timezone.utc)) # CHANGE THIS, AS THIS WONT WORK
    
    
    # ADD this inside your Conversations class
    user = dbb.relationship('Users', back_populates='conversations')
    msgs = dbb.relationship('Messages', back_populates='conversation', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Message {self.conv_id} | {self.user_id}>'



class Messages(dbb.Model):

    __tablename__ = 'messages'

    msg_id = dbb.Column(dbb.Integer, primary_key=True)
    conv_id = dbb.Column(dbb.Integer, dbb.ForeignKey('conversations_users.conv_id'), nullable=False)
    role = dbb.Column(dbb.String(20), nullable=False)     # 'user' or 'assistant'
    detail = dbb.Column(dbb.Text, nullable=False)
    timestamp = dbb.Column(dbb.DateTime, default=lambda: datetime.now(timezone.utc))

    conversation = dbb.relationship('Conversations', back_populates='msgs')

    def __repr__(self):
        return f'<Message {self.msg_id} | {self.role}>'

