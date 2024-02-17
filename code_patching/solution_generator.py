import concurrent.futures as futures
import json
from typing import Iterator, List, Dict, Optional
from itertools import product
import tqdm

from domain.problems_d import CodePatchingPromptD, ContestProblemD, SolutionD, PromptedSolutionD
from llm_handler.openai_handler import OpenAIHandler
import proto.patched_solutions_pb2 as ps_pb2
from domain.domain_dao import DomainFileDAO

RESPONSE_FORMAT = {"type": "json_object"}

GenArgsDict = Dict[str, Dict[CodePatchingPromptD, Dict[str, Dict[str, str]]]]


def get_prompted_solution(prompt: CodePatchingPromptD,
                          problem: ContestProblemD, solution: SolutionD,
                          model: 'ps_pb2.ModelType') -> PromptedSolutionD:
    formatted_prompt = prompt.format(function_description=problem.description)
    messages = [{
        "role": "system",
        "content": formatted_prompt
    }, {
        "role": "user",
        "content": solution.solution
    }]
    patched_solution_response = OpenAIHandler().get_chat_completion(
        messages=messages, model_type=model, response_format=RESPONSE_FORMAT)
    patched_response_dict: Dict[str,
                                str] = json.loads(patched_solution_response)
    patched_solution = patched_response_dict.get('solution', "")
    return PromptedSolutionD(solution_id=solution.proto_id,
                             problem_id=problem.proto_id,
                             prompt_id=prompt.proto_id,
                             model=model,
                             patched_solution=patched_solution,
                             patched_response=patched_response_dict)


def generate_prompted_dataset(
        contest_problems: List[ContestProblemD],
        model_types: List[ps_pb2.ModelType],
        prompts: List[CodePatchingPromptD],
        domain_reader: DomainFileDAO[PromptedSolutionD],
        max_workers: Optional[int] = None,
        result_batch_size: int = 100) -> Iterator[PromptedSolutionD]:

    new_args = [(problem.proto_id, contest_sol.proto_id, model,
                 prompt.proto_id) for problem, model, prompt in product(
                     contest_problems, model_types, prompts)
                for contest_sol in problem.incorrect_solutions]
    for existing_sol in tqdm.tqdm(domain_reader.read()):
        existign_args = (existing_sol.problem_id, existing_sol.solution_id,
                         existing_sol.model, existing_sol.prompt_id)
        if existign_args in new_args:
            new_args.remove(existign_args)
            yield existing_sol

    executor = futures.ThreadPoolExecutor(max_workers=max_workers)
    prompt_futures: List[futures.Future[PromptedSolutionD]] = []
    for problem, model, prompt in product(contest_problems, model_types,
                                          prompts):
        for solution in problem.incorrect_solutions:
            if (problem.proto_id, solution.proto_id, model,
                    prompt.proto_id) in new_args:
                prompted_future = executor.submit(get_prompted_solution,
                                                  prompt, problem, solution,
                                                  model)
                prompt_futures.append(prompted_future)

    future_results: List[PromptedSolutionD] = []
    for future in tqdm.tqdm(futures.as_completed(prompt_futures),
                            total=len(prompt_futures)):
        future_results.append(future.result())
        if len(future_results) == result_batch_size:
            domain_reader.write_to_jsonl(future_results)
            yield from future_results
            future_results.clear()
