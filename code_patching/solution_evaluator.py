import concurrent.futures as futures
from typing import List, Optional, Iterable
from itertools import product
import tqdm
import subprocess

from domain.problems_d import PromptedSolutionD, TestResultD, TestD
from domain.domain_dao import DomainFileDAO


def execute_solution(solution: PromptedSolutionD, test: TestD) -> TestResultD:
    process = subprocess.Popen(solution.patched_solution,
                               stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               shell=True)
    try:
        stdout, stderr = process.communicate(test.input.encode(), timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate()
    return TestResultD(solution_id=solution.solution_id,
                       problem_id=solution.problem_id,
                       test_id=test.proto_id,
                       solution_output=stdout.decode(),
                       exception_info=stderr.decode())


def eval_prompted_solutions(
        problem_tests: List[TestD],
        prompted_solutions: List[PromptedSolutionD],
        domain_writer: DomainFileDAO[TestResultD],
        max_workers: Optional[int] = None,
        result_batch_size: int = 100) -> Iterable[TestResultD]:

    new_args = [(sol.proto_id, test.proto_id)
                for sol, test in product(prompted_solutions, problem_tests)]
    for existing_result in domain_writer.read():
        existign_args = (existing_result.solution_id, existing_result.test_id)
        if existign_args in new_args:
            new_args.remove(existign_args)
            yield existing_result

    executor = futures.ProcessPoolExecutor(max_workers=max_workers)
    result_futures: List[futures.Future[TestResultD]] = []
    for solution, test in product(prompted_solutions, problem_tests):
        if (solution.proto_id, test.proto_id) in new_args:
            result_futures.append(
                executor.submit(execute_solution, solution, test))

    result_batch: List[TestResultD] = []
    for future in tqdm.tqdm(futures.as_completed(result_futures),
                            total=len(result_futures)):
        result_batch.append(future.result())
        if len(result_batch) >= result_batch_size:
            domain_writer.write_to_jsonl(result_batch)
            yield from result_batch
            result_batch.clear()
