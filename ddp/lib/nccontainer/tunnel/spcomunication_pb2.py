# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: spcomunication.proto

import sys

_b = sys.version_info[0] < 3 and (lambda x: x) or (lambda x: x.encode('latin1'))
from google.protobuf.internal import enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf import reflection as _reflection
from google.protobuf import symbol_database as _symbol_database
from google.protobuf import descriptor_pb2

# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()

DESCRIPTOR = _descriptor.FileDescriptor(
    name='spcomunication.proto',
    package='spcomunication',
    syntax='proto3',
    serialized_pb=_b(
        '\n\x14spcomunication.proto\x12\x0espcomunication\"\x8f\x01\n\x05spmsg\x12\"\n\x04type\x18\x01 \x01(\x0e\x32\x14.spcomunication.Type\x12\x13\n\x0bswitch_addr\x18\x02 \x01(\t\x12\x14\n\x0coperation_id\x18\x03 \x01(\t\x12\x13\n\x0bsproxy_port\x18\x05 \x01(\t\x12\x13\n\x0bsproxy_addr\x18\x04 \x01(\t\x12\r\n\x05state\x18\x06 \x01(\t*#\n\x04Type\x12\x08\n\x04PUSH\x10\x00\x12\x08\n\x04PULL\x10\x01\x12\x07\n\x03MAP\x10\x02\x62\x06proto3')
)

_TYPE = _descriptor.EnumDescriptor(
    name='Type',
    full_name='spcomunication.Type',
    filename=None,
    file=DESCRIPTOR,
    values=[
        _descriptor.EnumValueDescriptor(
            name='PUSH', index=0, number=0,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='PULL', index=1, number=1,
            options=None,
            type=None),
        _descriptor.EnumValueDescriptor(
            name='MAP', index=2, number=2,
            options=None,
            type=None),
    ],
    containing_type=None,
    options=None,
    serialized_start=186,
    serialized_end=221,
)
_sym_db.RegisterEnumDescriptor(_TYPE)

Type = enum_type_wrapper.EnumTypeWrapper(_TYPE)
PUSH = 0
PULL = 1
MAP = 2

_SPMSG = _descriptor.Descriptor(
    name='spmsg',
    full_name='spcomunication.spmsg',
    filename=None,
    file=DESCRIPTOR,
    containing_type=None,
    fields=[
        _descriptor.FieldDescriptor(
            name='type', full_name='spcomunication.spmsg.type', index=0,
            number=1, type=14, cpp_type=8, label=1,
            has_default_value=False, default_value=0,
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='switch_addr', full_name='spcomunication.spmsg.switch_addr', index=1,
            number=2, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='operation_id', full_name='spcomunication.spmsg.operation_id', index=2,
            number=3, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='sproxy_port', full_name='spcomunication.spmsg.sproxy_port', index=3,
            number=5, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='sproxy_addr', full_name='spcomunication.spmsg.sproxy_addr', index=4,
            number=4, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None, file=DESCRIPTOR),
        _descriptor.FieldDescriptor(
            name='state', full_name='spcomunication.spmsg.state', index=5,
            number=6, type=9, cpp_type=9, label=1,
            has_default_value=False, default_value=_b("").decode('utf-8'),
            message_type=None, enum_type=None, containing_type=None,
            is_extension=False, extension_scope=None,
            options=None, file=DESCRIPTOR),
    ],
    extensions=[
    ],
    nested_types=[],
    enum_types=[
    ],
    options=None,
    is_extendable=False,
    syntax='proto3',
    extension_ranges=[],
    oneofs=[
    ],
    serialized_start=41,
    serialized_end=184,
)

_SPMSG.fields_by_name['type'].enum_type = _TYPE
DESCRIPTOR.message_types_by_name['spmsg'] = _SPMSG
DESCRIPTOR.enum_types_by_name['Type'] = _TYPE
_sym_db.RegisterFileDescriptor(DESCRIPTOR)

spmsg = _reflection.GeneratedProtocolMessageType('spmsg', (_message.Message,), dict(
    DESCRIPTOR=_SPMSG,
    __module__='spcomunication_pb2'
    # @@protoc_insertion_point(class_scope:spcomunication.spmsg)
))
_sym_db.RegisterMessage(spmsg)


# @@protoc_insertion_point(module_scope)
