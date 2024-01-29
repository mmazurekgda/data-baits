# from example.databases import databases_with_names, engines
# from data_baits.baits import DataModel
# from sqlalchemy import String
# from pydantic import model_validator
# from flask_security import UserMixin, RoleMixin
# import bcrypt
# from typing import List

# from sqlmodel import SQLModel, Field, Relationship


# class Role(SQLModel, RoleMixin):
#     name = Field(sa_type=String(80), nullable=False, unique=True)
#     description = Field(sa_type=String(255), nullable=True)


# class UserBase(SQLModel, UserMixin):
#     email: str = Field(sa_type=String(255), nullable=False, unique=True)
#     password: str = Field(sa_type=String(255), nullable=False)
#     roles: List[Role] = Relationship(back_populates="users")

#     @model_validator(mode="after")
#     def _hash_password(self) -> "UserBase":
#         self.password = bcrypt.hashpw(self.password, bcrypt.gensalt(13))
#         return self

#     def authenticate(self, name: str, password: str) -> bool:
#         if self.name != name:
#             return False
#         return bcrypt.checkpw(password, self.password)


# user = DataModel(
#     name="User",
#     database=databases_with_names["test_mysql"].database_name(),
#     model=UserBase,
#     engine=engines[databases_with_names["test_mysql"].database_name()],
# )
