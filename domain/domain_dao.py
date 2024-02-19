import os
from typing import TypeVar, Type, Iterable, Generic, Tuple
import dataclasses
import concurrent.futures as futures
import logging

from domain.domain_protocol import DomainProtocol

DomainT = TypeVar('DomainT', bound=DomainProtocol)


@dataclasses.dataclass(frozen=True)
class DomainFileDAO(Generic[DomainT]):

    _file_path: str
    _domain_cls: Type[DomainT]

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
        elif self._file_path.endswith('.pb'):
            self._write_to_text_binary(domain_objects, replace)
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
                file.write(domain_object.to_proto().SerializeToString().decode(
                    'utf-8'))
                file.write('\n')


@dataclasses.dataclass(frozen=True)
class CompressedDomainFileDAO(Generic[DomainT]):

    _dir_path: str
    _domain_cls: Type[DomainT]

    def __post_init__(self):
        if not os.path.exists(self._dir_path):
            raise FileNotFoundError(f'File not found: {self._dir_path}')

    @staticmethod
    def _read_from_compressed_text_binary(domain_cls: Type[DomainT],
                                          file_path: str) -> DomainT:
        with open(file_path, 'rb') as file:
            return domain_cls.from_compressed(file.read())

    def _ff_path(self, file_path: str) -> str:
        return f'{self._dir_path}/{file_path}'

    @property
    def file_paths(self) -> Iterable[str]:
        return map(self._ff_path, os.listdir(self._dir_path))

    @staticmethod
    def _inc_from_path(file_path: str) -> int:
        return int(file_path.split('_')[-1].split('.')[0])

    def _parallel_read(self) -> Iterable[Tuple[str, DomainT]]:
        with futures.ProcessPoolExecutor() as exexutor:
            futures_dict = {}
            for file_path in self.file_paths:
                future = exexutor.submit(
                    self._read_from_compressed_text_binary, self._domain_cls,
                    file_path)
                futures_dict[future] = file_path
            for future in futures.as_completed(futures_dict):
                file_path = futures_dict[future]
                yield (file_path, future.result())

    def read(self, parallelize: bool = False) -> Iterable[DomainT]:
        read_fn = self._parallel_read if parallelize else self._sequential_read
        for _, domains in sorted(read_fn(),
                                 key=lambda x: self._inc_from_path(x[0])):
            yield domains

    def _sequential_read(self) -> Iterable[Tuple[str, DomainT]]:
        for file_path in self.file_paths:
            domains = self._read_from_compressed_text_binary(
                self._domain_cls, file_path)
            yield (file_path, domains)

    def clear_cache(self):
        if os.path.exists(self._dir_path):
            for file in os.listdir(self._dir_path):
                os.remove(f'{self._dir_path}/{file}')

    def write(self, domain_objects: Iterable[DomainT]):
        if not os.path.exists(self._dir_path):
            os.makedirs(self._dir_path, exist_ok=True)
        curr_chunk = max([
            int(file.split('_')[1].split('.')[0])
            for file in os.listdir(self._dir_path)
        ] or [0])
        for domain_object in domain_objects:
            curr_chunk += 1
            with open(f'{self._dir_path}/chunk_{curr_chunk}.pb', 'wb') as file:
                file.write(domain_object.to_compressed())
