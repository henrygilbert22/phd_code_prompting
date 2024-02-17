from __future__ import annotations
import dataclasses
from typing import Dict, List, ClassVar
from google.protobuf.duration_pb2 import Duration
import enum

from proto.contest_problem_pb2 import ContestProblem
import proto.patched_solutions_pb2 as ps_pb2
from domain.domain_protocol import DomainProtocol


@dataclasses.dataclass(frozen=True)
class TestD(DomainProtocol[ContestProblem.Test]):
    input: str
    output: str

    @classmethod
    def from_proto(cls, proto: ContestProblem.Test) -> TestD:
        return TestD(input=proto.input, output=proto.output)

    def to_proto(self) -> ContestProblem.Test:
        return ContestProblem.Test(input=self.input, output=self.output)

    def __str__(self) -> str:
        return f"Test Input: {self.input}\nExpected Output: {self.output}\n"


@dataclasses.dataclass(frozen=True)
class SolutionD(DomainProtocol[ContestProblem.Solution]):
    solution: str
    language: ContestProblem.Solution.Language

    @classmethod
    def from_proto(cls, proto: ContestProblem.Solution) -> SolutionD:
        return SolutionD(solution=proto.solution, language=proto.language)

    def to_proto(self) -> ContestProblem.Solution:
        return ContestProblem.Solution(solution=self.solution,
                                       language=self.language)


@dataclasses.dataclass(frozen=True)
class ContestProblemD(DomainProtocol[ContestProblem]):
    DEFAULT_TIME_LIMIT_SEC: ClassVar[int] = 10
    name: str
    description: str
    difficulty: ContestProblem.Difficulty
    time_limit_nsec: int
    memory_limit_bytes: int

    public_tests: List[TestD]
    private_tests: List[TestD]
    generated_tests: List[TestD]
    solutions: List[SolutionD]
    incorrect_solutions: List[SolutionD]

    cf_points: float
    cf_rating: int

    @property
    def tests(self) -> List[TestD]:
        return self.public_tests + self.private_tests

    @property
    def time_limit_sec(self) -> float:
        return self.time_limit_nsec / 1e9

    @classmethod
    def from_proto(cls, proto: ContestProblem) -> ContestProblemD:
        return ContestProblemD(
            name=proto.name,
            description=proto.description,
            difficulty=proto.difficulty,
            time_limit_nsec=proto.time_limit.ToNanoseconds(),
            memory_limit_bytes=proto.memory_limit_bytes,
            public_tests=[
                TestD.from_proto(test) for test in proto.public_tests
            ],
            private_tests=[
                TestD.from_proto(test) for test in proto.private_tests
            ],
            generated_tests=[
                TestD.from_proto(test) for test in proto.generated_tests
            ],
            solutions=[
                SolutionD.from_proto(solution) for solution in proto.solutions
            ],
            incorrect_solutions=[
                SolutionD.from_proto(solution)
                for solution in proto.incorrect_solutions
            ],
            cf_points=proto.cf_points,
            cf_rating=proto.cf_rating)

    def to_proto(self) -> ContestProblem:
        return ContestProblem(
            name=self.name,
            description=self.description,
            difficulty=self.difficulty,
            time_limit=Duration(nanos=self.time_limit_nsec),
            memory_limit_bytes=self.memory_limit_bytes,
            public_tests=[test.to_proto() for test in self.public_tests],
            private_tests=[test.to_proto() for test in self.private_tests],
            generated_tests=[test.to_proto() for test in self.generated_tests],
            solutions=[solution.to_proto() for solution in self.solutions],
            incorrect_solutions=[
                solution.to_proto() for solution in self.incorrect_solutions
            ],
            cf_points=self.cf_points,
            cf_rating=self.cf_rating)


@dataclasses.dataclass(frozen=True)
class TestResultD(DomainProtocol[ps_pb2.TestResult]):
    test_id: str
    problem_id: str
    solution_id: str
    solution_output: str
    exception_info: str

    @classmethod
    def from_proto(cls, proto: ps_pb2.TestResult) -> TestResultD:
        return TestResultD(test_id=proto.test_id,
                           problem_id=proto.problem_id,
                           solution_id=proto.solution_id,
                           solution_output=proto.solution_output,
                           exception_info=proto.exception_info)

    def to_proto(self) -> ps_pb2.TestResult:
        return ps_pb2.TestResult(test_id=self.test_id,
                                 problem_id=self.problem_id,
                                 solution_id=self.solution_id,
                                 solution_output=self.solution_output,
                                 exception_info=self.exception_info)


@dataclasses.dataclass(frozen=True)
class CodePatchingPromptD(DomainProtocol[ps_pb2.CodePatchingPrompt]):
    prompt_name: str
    unformated_prompt: str

    def format(self, **format_kwargs) -> str:
        return self.unformated_prompt.format(**format_kwargs)

    @classmethod
    def from_proto(cls,
                   proto: ps_pb2.CodePatchingPrompt) -> CodePatchingPromptD:
        return CodePatchingPromptD(prompt_name=proto.prompt_name,
                                   unformated_prompt=proto.unformated_prompt)

    def to_proto(self) -> ps_pb2.CodePatchingPrompt:
        return ps_pb2.CodePatchingPrompt(
            prompt_name=self.prompt_name,
            unformated_prompt=self.unformated_prompt)


@dataclasses.dataclass(frozen=True)
class PromptedSolutionD(DomainProtocol[ps_pb2.PatchedSolution]):
    solution_id: str
    problem_id: str
    prompt_id: str
    model: ps_pb2.ModelType
    patched_solution: str
    patched_response: Dict[str, str]

    @classmethod
    def from_proto(cls, proto: ps_pb2.PatchedSolution) -> PromptedSolutionD:
        return PromptedSolutionD(solution_id=proto.solution_id,
                                 problem_id=proto.problem_id,
                                 prompt_id=proto.prompt_id,
                                 model=proto.model,
                                 patched_solution=proto.patched_solution,
                                 patched_response=dict(proto.patched_response))

    def to_proto(self) -> ps_pb2.PatchedSolution:
        return ps_pb2.PatchedSolution(solution_id=self.solution_id,
                                      problem_id=self.problem_id,
                                      prompt_id=self.prompt_id,
                                      model=self.model,
                                      patched_solution=self.patched_solution,
                                      patched_response=self.patched_response)
