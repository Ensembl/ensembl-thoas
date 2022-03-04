from mongoengine import Document


class ThoasDocument(Document):
    meta = {'allow_inheritance': True}