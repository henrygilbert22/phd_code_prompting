import concurrent.futures as futures
import json
from typing import Iterator, List, Dict, Optional, Iterable, Tuple
from itertools import product
import tqdm
import logging
from collections import defaultdict
from itertools import chain

from domain.problems_d import CodePatchingPromptD, ContestProblemD, SolutionD, PatchedSolutionD, PatchedSolutionSetD, ContestProblemSetD
from llm_handler.openai_handler import OpenAIHandler
import proto.patched_solutions_pb2 as ps_pb2
from domain.domain_dao import CompressedDomainFileDAO

RESPONSE_FORMAT = {"type": "json_object"}

GenArgsDict = Dict[str, Dict[CodePatchingPromptD, Dict[str, Dict[str, str]]]]


def get_prompted_solution(prompt: CodePatchingPromptD,
                          problem: ContestProblemD, solution: SolutionD,
                          model: 'ps_pb2.ModelType') -> PatchedSolutionD:
    formatted_prompt = prompt.format(function_description=problem.description)
    messages = [{
        "role": "system",
        "content": formatted_prompt
    }, {
        "role": "user",
        "content": solution.solution
    }]

    try:
        patched_solution_response = OpenAIHandler().get_chat_completion(
            messages=messages,
            model_type=model,
            response_format=RESPONSE_FORMAT)
        patched_response_dict: Dict[str, str] = json.loads(
            patched_solution_response)
        patched_solution = patched_response_dict.get('solution', "")
        if not patched_solution:
            logging.warning(
                f"Failed to patch solution for problem {problem.proto_id} and solution {solution.proto_id} - {model}"
            )
    except Exception as e:
        logging.error(
            f"Failed to patch solution for problem {problem.proto_id} and solution {solution.proto_id}  - {model} - {e}"
        )
        patched_solution = ""
        patched_response_dict = {}
    return PatchedSolutionD(
        solution_id=solution.proto_id,
        problem_id=problem.proto_id,
        prompt_id=prompt.proto_id,
        model=model,
        patched_solution=patched_solution,
        patched_response={"response": str(patched_response_dict)})


def generate_prompted_dataset(
        contest_problems: List[ContestProblemSetD],
        model_types: List['ps_pb2.ModelType'],
        prompts: List[CodePatchingPromptD],
        domain_reader: CompressedDomainFileDAO[PatchedSolutionSetD],
        max_workers: Optional[int] = None,
        result_batch_size: int = 500) -> Iterator[PatchedSolutionSetD]:

    new_arg_ids: Dict[Tuple[str, str, ps_pb2.ModelType, str],
                      Tuple[CodePatchingPromptD, ContestProblemD, SolutionD,
                            ps_pb2.ModelType]] = {}
    for contest_problem in contest_problems:
        for problem in contest_problem.problems:
            for solution in problem.incorrect_solutions:
                for model in model_types:
                    for prompt in prompts:
                        arg_id = (problem.proto_id, solution.proto_id, model,
                                  prompt.proto_id)
                        new_arg_ids[arg_id] = (prompt, problem, solution,
                                               model)

    existing_solutions: Dict[Tuple[str, str, ps_pb2.ModelType, str],
                             PatchedSolutionD] = {}
    for existing_set in domain_reader.read():
        for existing_sol in existing_set.solutions:
            arg_id = (existing_sol.problem_id, existing_sol.solution_id,
                      existing_sol.model, existing_sol.prompt_id)
            existing_solutions[arg_id] = existing_sol

    matching_cached_ids = set(new_arg_ids.keys()).intersection(
        existing_solutions.keys())
    logging.warning(f"Found {len(matching_cached_ids)} matching cached ids")
    new_arg_ids = {
        k: v
        for k, v in new_arg_ids.items() if k not in matching_cached_ids
    }
    cached_set = PatchedSolutionSetD(
        [existing_solutions[cached_id] for cached_id in matching_cached_ids])
    if cached_set.solutions:
        yield cached_set

    results = []
    gen_args = list(new_arg_ids.values())
    logging.warning(f"Generated {len(gen_args)}")
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        batched_futures: List[futures.Future[PatchedSolutionD]] = []
        result_pbar = tqdm.tqdm(total=len(gen_args), desc=f"Solutions")
        while gen_args:

            prompted_future = executor.submit(get_prompted_solution,
                                              *gen_args.pop())
            batched_futures.append(prompted_future)
            if len(batched_futures) < result_batch_size:
                continue

            completed, running = futures.wait(
                batched_futures,
                timeout=10,
                return_when=futures.FIRST_COMPLETED)
            results += [future.result() for future in completed]
            batched_futures = list(running)
            result_pbar.update(len(completed))

            if len(results) >= result_batch_size:
                yield from write_results(results, domain_reader)
                results = []

        final_timeout = 30
        try: 
            logging.warning(
                f"Waiting for {len(batched_futures)} futures - {final_timeout} seconds"
            )
            for future in futures.as_completed(batched_futures,
                                               timeout=final_timeout):
                results.append(future.result())
                result_pbar.update()
        except futures.TimeoutError:
            logging.warning(
                f"Timed out after {final_timeout} seconds with {len(batched_futures)} futures remaining"
            )
        finally:
            yield from write_results(results, domain_reader)


def write_results(
    solutions: List[PatchedSolutionD],
    domain_writer: CompressedDomainFileDAO[PatchedSolutionSetD]
) -> Iterable[PatchedSolutionSetD]:
    if solutions:
        solution_set_d = PatchedSolutionSetD(solutions=solutions)
        domain_writer.write([solution_set_d])
        yield solution_set_d
