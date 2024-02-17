import os
from typing import TypeVar, Type, Iterable, Generic
import dataclasses
from domain.domain_protocol import DomainProtocol

DomainT = TypeVar('DomainT', bound=DomainProtocol)


@dataclasses.dataclass(frozen=True)
class DomainFileDAO(Generic[DomainT]):

    _file_path: str
    _domain_cls: Type[DomainT]

    def __post_init__(self):
        if not os.path.exists(self._file_path):
            raise FileNotFoundError(f'File {self._file_path} not found')

    def read(self) -> Iterable[DomainT]:
        if self._file_path.endswith('.pb'):
            return self._read_from_text_binary()
        elif self._file_path.endswith('.jsonl'):
            return self._read_from_jsonl()
        else:
            raise ValueError(f'Unsupported file format: {self._file_path}')

    def write(self, domain_objects: Iterable[DomainT], replace: bool = True):
        if self._file_path.endswith('.jsonl'):
            self._write_to_jsonl(domain_objects, replace)
        else:
            raise ValueError(f'Unsupported file format: {self._file_path}')

    def _read_from_text_binary(self) -> Iterable[DomainT]:
        with open(self._file_path, 'r') as file:
            for line in file.readlines():
                proto = self._domain_cls.message_cls()()
                proto.ParseFromString(line.encode('utf-8'))
                yield self._domain_cls.from_proto(proto)

    def _read_from_jsonl(self) -> Iterable[DomainT]:
        with open(self._file_path, 'r') as file:
            for line in file:
                yield self._domain_cls.from_json(line)

    def _write_to_jsonl(self,
                        domain_objects: Iterable[DomainT],
                        replace: bool = True):
        mode = 'w' if replace else 'a'
        with open(self._file_path, mode) as file:
            for domain_object in domain_objects:
                file.write(domain_object.to_json() + '\n')

    def _write_to_text_binary(self,
                              domain_objects: Iterable[DomainT],
                              replace: bool = True):
        mode = 'w' if replace else 'a'
        with open(self._file_path, mode) as file:
            for domain_object in domain_objects:
                file.write(domain_object.to_proto().SerializeToString().encode(
                    'utf-8'))
                file.write('\n')
