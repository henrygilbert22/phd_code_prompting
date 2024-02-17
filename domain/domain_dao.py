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
        if ".jsonl" not in self._file_path:
            raise ValueError(f'File {self._file_path} is not a jsonl file')

    def read(self) -> Iterable[DomainT]:
        for line in open(self._file_path, 'r'):
            yield self._domain_cls.from_json(line)

    def write_to_jsonl(self,
                       domain_objects: Iterable[DomainT],
                       replace: bool = True):
        mode = 'w' if replace else 'a'
        with open(self._file_path, mode) as file:
            for domain_object in domain_objects:
                file.write(domain_object.to_json() + '\n')
