import concurrent.futures as futures
from typing import List, Optional, Iterable, Tuple, Dict
from itertools import product
import tqdm
import subprocess
import logging

from domain.problems_d import PatchedSolutionD, TestResultSetD, TestD, TestResultD
from domain.domain_dao import CompressedDomainFileDAO


def execute_solution(solution: PatchedSolutionD, test: TestD) -> TestResultD:
    stdout = ""
    stderr = "Unhandled exception"
    try:
        completed_process = subprocess.run(
            ["python3", "-c", solution.patched_solution],
            input=test.input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10)
        stdout = completed_process.stdout
        stderr = completed_process.stderr
    except subprocess.TimeoutExpired as e:
        stderr = f"Timeout - {str(e)}"
    finally:
        return TestResultD(solution_id=solution.proto_id,
                           problem_id=solution.problem_id,
                           test_id=test.proto_id,
                           solution_output=stdout,
                           exception_info=stderr,
                           expected_output=test.output)


def compute_batch(
        exec_args: List[Tuple[PatchedSolutionD, TestD]]) -> List[TestResultD]:
    results = []
    for solution, test in exec_args:
        results.append(execute_solution(solution, test))
    return results


def eval_patched_solutions(
        problem_tests: Dict[str, List[TestD]],
        patched_solutions: Dict[str, List[PatchedSolutionD]],
        domain_writer: CompressedDomainFileDAO[TestResultSetD],
        max_workers: Optional[int] = None,
        process_batch_size: int = 10,
        batch_size: int = 1000) -> Iterable[TestResultSetD]:
    if not set(problem_tests.keys()) == set(patched_solutions.keys()):
        raise ValueError(
            "Problem tests and patched solutions keys do not match")
    if batch_size < process_batch_size:
        raise ValueError("Batch size must be greater than process batch size")

    new_args = {}
    for problem_id, solutions in patched_solutions.items():
        for solution, test in product(solutions, problem_tests[problem_id]):
            new_args[(solution.proto_id, test.proto_id)] = (solution, test)

    results = []
    for existing_solution_set in domain_writer.read():
        for existing_result in existing_solution_set.test_results:
            existign_args = (existing_result.solution_id,
                             existing_result.test_id)
            if existign_args in new_args:
                new_args.pop(existign_args)
                results.append(existing_result)

    logging.warning(f"Skipped {len(results)} already executed tests")
    if results:
        yield TestResultSetD(test_results=results)
        results = []

    arg_list = list(new_args.values())
    process_batches: List[List[Tuple[PatchedSolutionD, TestD]]] = [
        arg_list[i:i + process_batch_size]
        for i in range(0, len(arg_list), process_batch_size)
    ]

    logging.warning(
        f"{process_batch_size=} {batch_size=} - {len(process_batches)} batches - {len(arg_list)} total tests"
    )
    results_pbar = tqdm.tqdm(total=len(arg_list), desc="Test Evals")
    with futures.ProcessPoolExecutor(max_workers=max_workers) as executor:

        batch_futures = [
            executor.submit(compute_batch, process_batch)
            for process_batch in process_batches
        ]

        results: List[TestResultD] = []
        for future in futures.as_completed(batch_futures):
            test_results = future.result()
            results.extend(test_results)
            results_pbar.update(len(test_results))

            if len(results) >= batch_size:
                yield write_results(results, domain_writer)
                results = []
        if results:
            yield write_results(results, domain_writer)


def write_results(
        results: List[TestResultD],
        domain_writer: CompressedDomainFileDAO[TestResultSetD]
) -> TestResultSetD:
    result_set_d = TestResultSetD(test_results=results)
    if result_set_d.test_results:
        domain_writer.write([result_set_d])
    return result_set_d
