from datetime import datetime
from pprint import pprint

from marshmallow import INCLUDE, fields

from mapper import MarshModel, MMNested


class UserModel(MarshModel):
    __meta_args__ = {"unknown": INCLUDE}

    name: str = fields.Str()
    email: str = fields.Email()
    created_at: datetime = fields.DateTime()


class BlogModel(MarshModel):
    title: str = fields.String()
    author: UserModel = MMNested(UserModel)


user_data = {"name": "Ronnie", "email": "ronnie@stones.com"}
user = UserModel().load(user_data)

blog = BlogModel(title="Something Completely Different", author=user)
result = blog.dump()
pprint(result)
