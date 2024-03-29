from __future__ import annotations
import dataclasses
from typing import Dict, List, ClassVar, Any
import google.protobuf.duration_pb2 as duration_pb2

from proto.contest_problem_pb2 import ContestProblem
import proto.patched_solutions_pb2 as ps_pb2
from domain.domain_protocol import DomainProtocol


@dataclasses.dataclass(frozen=True)
class ContestProblemSetD(DomainProtocol[ps_pb2.ContestProblemSet]):
    problems: List[ContestProblemD]

    @classmethod
    def from_proto(cls, proto: ps_pb2.ContestProblemSet) -> ContestProblemSetD:
        return ContestProblemSetD(problems=[
            ContestProblemD.from_proto(problem) for problem in proto.problems
        ])

    def to_proto(self) -> ps_pb2.ContestProblemSet:
        return ps_pb2.ContestProblemSet(
            problems=[problem.to_proto() for problem in self.problems])

    @classmethod
    def compressed_from_df(cls, df) -> bytes:
        domain = ContestProblemSetD(ContestProblemD.from_df(df))
        return domain.to_compressed()


@dataclasses.dataclass(frozen=True)
class PatchedSolutionSetD(DomainProtocol[ps_pb2.PatchedSolutionSet]):
    solutions: List[PatchedSolutionD]

    @classmethod
    def from_proto(cls,
                   proto: ps_pb2.PatchedSolutionSet) -> PatchedSolutionSetD:
        return PatchedSolutionSetD(solutions=[
            PatchedSolutionD.from_proto(solution)
            for solution in proto.patched_solutions
        ])

    def to_proto(self) -> ps_pb2.PatchedSolutionSet:
        return ps_pb2.PatchedSolutionSet(patched_solutions=[
            solution.to_proto() for solution in self.solutions
        ])


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

    @classmethod
    def from_df_row(cls, row_dict: Dict[str, Any]) -> ContestProblemD:
        seconds = int(row_dict.get("time_limit.seconds", 1))
        return ContestProblemD(
            name=row_dict["name"],
            description=row_dict["description"],
            difficulty=ContestProblem.Difficulty.Name(
                int(row_dict["difficulty"] or 0)),
            time_limit_nsec=int(seconds * 1e9),
            memory_limit_bytes=row_dict["memory_limit_bytes"],
            public_tests=[
                TestD(input, output)
                for input, output in zip(row_dict["public_tests"]["input"],
                                         row_dict["public_tests"]["output"])
            ],
            private_tests=[
                TestD(input, output)
                for input, output in zip(row_dict["private_tests"]["input"],
                                         row_dict["private_tests"]["output"])
            ],
            generated_tests=[
                TestD(input, output)
                for input, output in zip(row_dict["generated_tests"]["input"],
                                         row_dict["generated_tests"]["output"])
            ],
            solutions=[
                SolutionD(solution, language=lang or 0)  # type: ignore
                for solution, lang in zip(row_dict["solutions"]["solution"],
                                          row_dict["solutions"]["language"])
            ],
            incorrect_solutions=[
                SolutionD(solution, language=lang or 0)  # type: ignore
                for solution, lang in zip(
                    row_dict["incorrect_solutions"]["solution"],
                    row_dict["incorrect_solutions"]["language"])
            ],
            cf_points=row_dict["cf_points"],
            cf_rating=row_dict["cf_rating"])

    def to_proto(self) -> ContestProblem:
        return ContestProblem(
            name=self.name,
            description=self.description,
            difficulty=self.difficulty,
            time_limit=duration_pb2.Duration(seconds=int(self.time_limit_nsec /
                                                         1e9)),
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

    def only_python_solutions(self) -> ContestProblemD:
        sol_filter = lambda sol: sol.language == ContestProblem.Solution.Language.PYTHON3
        return dataclasses.replace(self,
                                   solutions=list(
                                       filter(sol_filter, self.solutions)),
                                   incorrect_solutions=list(
                                       filter(sol_filter,
                                              self.incorrect_solutions)))

    @classmethod
    def from_df(cls, df) -> List[ContestProblemD]:
        problem_ds = [
            cls.from_df_row(row_dict) for _, row_dict in df.iterrows()
        ]
        only_python_ds = [
            problem.only_python_solutions() for problem in problem_ds
        ]
        return [
            problem for problem in only_python_ds
            if problem.solutions and problem.incorrect_solutions
        ]


@dataclasses.dataclass(frozen=True)
class TestResultSetD(DomainProtocol[ps_pb2.TestResultSet]):
    test_results: List[TestResultD]

    @property
    def score(self) -> float:
        return sum(test_result.is_correct
                   for test_result in self.test_results) / len(
                       self.test_results)

    @classmethod
    def from_proto(cls, proto: ps_pb2.TestResultSet) -> TestResultSetD:
        return TestResultSetD(test_results=[
            TestResultD.from_proto(test_result)
            for test_result in proto.test_results
        ])

    def to_proto(self) -> ps_pb2.TestResultSet:
        return ps_pb2.TestResultSet(test_results=[
            test_result.to_proto() for test_result in self.test_results
        ])


@dataclasses.dataclass(frozen=True)
class TestResultD(DomainProtocol[ps_pb2.TestResult]):
    test_id: str
    problem_id: str
    solution_id: str
    solution_output: str
    exception_info: str
    expected_output: str

    @property
    def is_correct(self) -> bool:
        return self.solution_output == self.expected_output

    @classmethod
    def from_proto(cls, proto: ps_pb2.TestResult) -> TestResultD:
        return TestResultD(test_id=proto.test_id,
                           problem_id=proto.problem_id,
                           solution_id=proto.solution_id,
                           solution_output=proto.solution_output,
                           exception_info=proto.exception_info,
                           expected_output=proto.expected_output)

    def to_proto(self) -> ps_pb2.TestResult:
        return ps_pb2.TestResult(test_id=self.test_id,
                                 problem_id=self.problem_id,
                                 solution_id=self.solution_id,
                                 solution_output=self.solution_output,
                                 exception_info=self.exception_info,
                                 expected_output=self.expected_output)


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
class PatchedSolutionD(DomainProtocol[ps_pb2.PatchedSolution]):
    solution_id: str
    problem_id: str
    prompt_id: str
    model: ps_pb2.ModelType
    patched_solution: str
    patched_response: Dict[str, str]

    @classmethod
    def from_proto(cls, proto: ps_pb2.PatchedSolution) -> PatchedSolutionD:
        return PatchedSolutionD(solution_id=proto.solution_id,
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
