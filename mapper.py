import inspect
import typing

import marshmallow.utils
from marshmallow import Schema, fields, types
from marshmallow.exceptions import RegistryError
from marshmallow.fields import Field

_model_registry = {}


def _register_model(cls: "MarshModel"):
    name = cls.__name__
    if name in _model_registry:
        raise RegistryError()

    _model_registry[name] = cls


# "Return" type of a field, i.e. how it will be stored
# def register_fields

_field_ret_type_reg = {
    fields.Integer: int,
    fields.Int: int,
    fields.Number: int,
    fields.Str: str,
    fields.String: str,
}

# def _register_field_types():
#     field_members=(getattr(fields,x) for x in dir(fields))
#     field_objs=[f for f in field_members if (inspect.isclass(f) and issubclass(f,fields.Field))]


def _create_init_fn(fields_: dict[str, Field]) -> typing.Callable:
    """Create an function from a list of fields"""
    args = []
    bodylines = []
    for name, field in fields_.items():
        sig = name
        type_ = _field_ret_type_reg.get(type(field))

        if type_:
            sig += f": {type_.__name__}"

        default = field.default
        if default == marshmallow.utils.missing:
            default = None

        if not field.required:
            sig += f" = {default}"

        args.append(sig)
        bodylines.append(f"  self.{name} = {name}")
    # import dataclasses
    txt = f"def __create_fn__(self, {', '.join(args)}) -> None:\n"
    txt += "\n".join(bodylines)

    ns = {}
    exec(txt, {}, ns)

    return ns["__create_fn__"]


def _get_meta_class(meta_dict: dict[str, typing.Any]) -> Schema:
    MetaCls = type("Meta", (object,), meta_dict)
    return type("_BaseSchema", (Schema,), {"Meta": MetaCls})


class MarshModel:
    _ma_schema: Schema
    _field_names: list[str]
    __meta_args__: dict[str, typing.Any] = {}

    def __init_subclass__(cls, **kw) -> None:
        super(MarshModel).__init_subclass__(**kw)

        cls._field_names = [
            f for f in dir(cls) if isinstance(getattr(cls, f), fields.Field)
        ]
        cls._ma_schema = _get_meta_class(cls.__meta_args__).from_dict(
            {name: getattr(cls, name) for name in cls._field_names}
        )()

        cls.__init__ = _create_init_fn(cls._ma_schema.fields)

        _register_model(cls)

    def load(self, *args, **kw):
        loaded = self._ma_schema.load(*args, **kw)
        for k, v in loaded.items():
            setattr(self, k, v)
        return self

    def dump(self):
        return self._ma_schema.dump(self)


MarshModel.load.__signature__ = inspect.signature(Schema.load)


class MMNested(fields.Nested):
    def __init__(self, nested: MarshModel, *args, **kw):
        nested = nested._ma_schema

        super().__init__(nested, *args, **kw)


MMNested.__init__.__signature__ = inspect.signature(fields.Nested.__init__)
