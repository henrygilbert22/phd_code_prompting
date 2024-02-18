from domain.problems_d import CodePatchingPromptD

USER_PROMPT = """
### PROBLEM DESCRIPTION ###
{function_description}

### BUGGY PYTHON SOLUTION FILE ###
{reference_solution}
"""

CODE_PATCHING_PROMPT_BASE = """
Your a state-of-the-art software engineer at a top tech company.
Your job is to fix a bug in a python solution file.
You will be given a description of the problem and the incorrect solution file as a string.

You will recieve input in the following format:

    ### PROBLEM DESCRIPTION ###
        ...

    ### BUGGY PYTHON SOLUTION FILE ###
        ...

The "solution" should be a valid python file that can be run with exec() and passes all the tests.
The generated solution should be general enough to pass all possible tests. 
The solution should take the same input and return the same output as the original solution file.

You will return the following in JSON format:
    {{
        "solution": "Fixed python solution file as a string"
"""

CODE_PATCHING_PROMPT_BASE_VO = CODE_PATCHING_PROMPT_BASE + """
    }}"""

CODE_PATCHING_PROMPT_BASE_EXPLANATION = CODE_PATCHING_PROMPT_BASE + """
    "change_description":   ["Change 1 Desc", "Change 2 Desc", ...],
    }}
    For each change, describe the change you made to the solution file.
"""

CODE_PATCHING_PROMPT_BASE_TEST_GENERATION = CODE_PATCHING_PROMPT_BASE + """
    "test_description":    ["Test 1 Desc", "Test 2 Desc", ...],
    }}
    Prior to generating the solution, 
    you should first describe one or more tests that you would use to verify the correctness of the solution.
    Provide the list of test descriptions in the "test_description" field.
"""

CODE_PATCHING_PROMPT_SELF_EVALUATION = CODE_PATCHING_PROMPT_BASE + """
    }}

    Before returning the JSON object with with the solution under the "solution" field,
    evaluate the correctness of your solution. 

    Specifically, to mirror the downstream evaluation process:
        1. Create your JSON return object in python code as a string
        2. Validate that it can be parsed as a JSON object
        3. Pull the "solution" field from the JSON object as a string 'solution_string'
        4. Use subprocess to execute the solution internally - ex:

            ```python3
            completed_process = subprocess.run(
                ["python3", "-c", solution_string],
                input=test_input,       # test_input is the input as a string for the test case
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10) 
            stdout = completed_process.stdout
            stderr = completed_process.stderr
                ```
        5. Verify the completed_process ran succesfully and generated the expected output.

    If any of the above steps fail, revaluate your solution, make any necessary changes, and re-run the self-evaluation process.
    Once you have a solution that passes the self-evaluation process, return the JSON object as a string.
"""

CODE_PATCHING_PROMPT_MINIMAL = """
    The following python file has a bug.
    Fix it and return the fixed file a string in a JSON object as follows:
    
        {
            "solution": "Fixed python solution file as a string"
        }

"""

PROMPTS = [
    CodePatchingPromptD(prompt_name="code_patching_prompt_base",
                        unformated_prompt=CODE_PATCHING_PROMPT_BASE),
    CodePatchingPromptD(
        prompt_name="code_patching_prompt_base_explanation",
        unformated_prompt=CODE_PATCHING_PROMPT_BASE_EXPLANATION),
    CodePatchingPromptD(
        prompt_name="code_patching_prompt_base_test_generation",
        unformated_prompt=CODE_PATCHING_PROMPT_BASE_TEST_GENERATION),
    CodePatchingPromptD(
        prompt_name="code_patching_prompt_self_evaluation",
        unformated_prompt=CODE_PATCHING_PROMPT_SELF_EVALUATION),
    CodePatchingPromptD(prompt_name="code_patching_prompt_minimal",
                        unformated_prompt=CODE_PATCHING_PROMPT_MINIMAL),
]
