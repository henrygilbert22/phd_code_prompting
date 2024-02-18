from __future__ import annotations
from typing import TypeVar, get_args, Type, Protocol, Optional, Tuple
from google.protobuf import json_format, message
import hashlib
import gzip
import dataclasses

MessageType = TypeVar("MessageType", bound=message.Message)
DomainProtocolType = TypeVar("DomainProtocolType", bound='DomainProtocol')

@dataclasses.dataclass(frozen=True)
class DomainProtocol(Protocol[MessageType]):
    

    
    @property
    def proto_id(self) -> str:
        return hashlib.sha256(
            self.to_proto().SerializeToString(deterministic=True)).hexdigest()

    @classmethod
    def message_cls(cls: Type[DomainProtocolType]) -> Type[MessageType]:
        orig_bases: Optional[Tuple[Type[MessageType],
                                   ...]] = getattr(cls, "__orig_bases__", None)
        if not orig_bases:
            raise ValueError(f"Class {cls} does not have __orig_bases__")
        if len(orig_bases) != 1:
            raise ValueError(
                f"Class {cls} has unexpected number of bases: {orig_bases}")
        return get_args(orig_bases[0])[0]

    def to_proto(self) -> MessageType:
        ...

    @classmethod
    def from_proto(cls: Type[DomainProtocolType],
                   proto: MessageType) -> MessageType:
        ...

    @classmethod
    def from_json(cls: Type[DomainProtocolType], json_str: str) -> MessageType:
        try:
            proto = cls.message_cls()()
            json_format.Parse(json_str, proto)
            return cls.from_proto(proto)
        except json_format.ParseError as e:
            raise ValueError(f"Failed to parse json string: {json_str} - {e}")

    def to_json(self) -> str:
        return json_format.MessageToJson(self.to_proto()).replace("\n", " ")

    @classmethod
    def from_dict(cls: Type[DomainProtocolType], d: dict) -> MessageType:
        try:
            proto = cls.message_cls()()
            json_format.ParseDict(d, proto)
            return cls.from_proto(proto)
        except json_format.ParseError as e:
            raise ValueError(f"Failed to parse dict: {e}")

    def to_compressed(self) -> bytes:
        return gzip.compress(self.to_proto().SerializeToString())

    @classmethod
    def from_compressed(cls: Type[DomainProtocolType],
                        compressed: bytes) -> DomainProtocolType:
        proto = cls.message_cls()()
        proto.ParseFromString(gzip.decompress(compressed))
        return cls.from_proto(proto)
