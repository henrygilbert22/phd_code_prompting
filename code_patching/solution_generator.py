import concurrent.futures as futures
import json
from typing import Iterator, List, Dict, Optional, Iterable, Tuple, TypeAlias
from itertools import product
import tqdm
import logging

from domain.problems_d import CodePatchingPromptD, ContestProblemD, SolutionD, PatchedSolutionD, PatchedSolutionSetD, ContestProblemSetD
from llm_handler.openai_handler import OpenAIHandler as openai_handler
import proto.patched_solutions_pb2 as ps_pb2
from domain.domain_dao import CompressedDomainFileDAO

RESPONSE_FORMAT = {"type": "json_object"}


def get_prompted_solution(problem: ContestProblemD, solution: SolutionD,
                          prompt: CodePatchingPromptD,
                          model: 'ps_pb2.ModelType') -> PatchedSolutionD:

    if prompt.prompt_name == "code_patching_prompt_minimal":
        formatted_prompt = prompt.unformated_prompt
    else:
        formatted_prompt = prompt.format(
            function_description=problem.description)

    messages = [{
        "role": "system",
        "content": formatted_prompt
    }, {
        "role": "user",
        "content": solution.solution
    }]

    try:
        patched_solution_response = openai_handler.get_chat_completion(
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


# def get_get_batched_prompted_solutions(args: List[ArgsT]) -> List[PatchedSolutionD]:
#     return [get_prompted_solution(*arg) for arg in args]

ArgsIdT: TypeAlias = Tuple[str, str, str, 'ps_pb2.ModelType']
ArgsT: TypeAlias = Tuple[ContestProblemD, SolutionD, CodePatchingPromptD,
                         'ps_pb2.ModelType']


def generate_prompted_dataset(
        contest_problems: List[ContestProblemSetD],
        model_types: List['ps_pb2.ModelType'],
        prompts: List[CodePatchingPromptD],
        domain_reader: CompressedDomainFileDAO[PatchedSolutionSetD],
        max_workers: Optional[int] = None,
        result_batch_size: int = 500,
        dry_run: bool=False) -> Iterator[PatchedSolutionSetD]:

    new_id_dict: Dict[ArgsIdT, ArgsT] = {}
    problem_solution_pairs = [(problem, solution)
                              for problem_set in contest_problems
                              for problem in problem_set.problems
                              for solution in problem.incorrect_solutions]
    for (problem, solution), prompt, model in product(problem_solution_pairs,
                                                      prompts, model_types):
        arg_id = (problem.proto_id, solution.proto_id, prompt.proto_id, model)
        new_id_dict[arg_id] = (problem, solution, prompt, model)
    logging.warning(f"Generated new {len(new_id_dict)} args")

    results = []
    for existing_set in domain_reader.read():
        for existing_sol in existing_set.solutions:
            arg_id = (existing_sol.problem_id, existing_sol.solution_id,
                      existing_sol.prompt_id, existing_sol.model)
            if arg_id in new_id_dict:
                results.append(existing_sol)
                new_id_dict.pop(arg_id)

    logging.warning(f"Skipped {len(results)} already generated solutions")
    if dry_run:
        logging.warning(f"Dry run, not generating solutions")
        return
    
    if results:
        yield PatchedSolutionSetD(solutions=results)
        results = []

    gen_args = list(new_id_dict.values())
    logging.warning(f"Generated {len(gen_args)} and")
    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:

        solution_futures = [
            executor.submit(get_prompted_solution, *args) for args in gen_args
        ]

        results_pbar = tqdm.tqdm(total=len(gen_args), desc="Solutions")
        for future in futures.as_completed(solution_futures):
            results.append(future.result())
            results_pbar.update()
            if len(results) >= result_batch_size:
                yield from write_results(results, domain_reader)
                results = []

        if results:
            yield from write_results(results, domain_reader)


def write_results(
    solutions: List[PatchedSolutionD],
    domain_writer: CompressedDomainFileDAO[PatchedSolutionSetD]
) -> Iterable[PatchedSolutionSetD]:
    if solutions:
        solution_set_d = PatchedSolutionSetD(solutions=solutions)
        domain_writer.write([solution_set_d])
        yield solution_set_d
