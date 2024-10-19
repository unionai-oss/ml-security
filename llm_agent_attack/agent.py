import os
import ast
import flytekit as fk



RESULT_VAR = "result"

registry = None
if int(os.getenv("SANDBOX", 1)):
    registry = "localhost:30000"


image = fk.ImageSpec(packages=["openai"], registry=registry)


@fk.task(
    secret_requests=[fk.Secret(group="openai", key="api_key")],
    container_image=image,
)
def generate_code(prompt: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=fk.current_context().secrets.get(group="openai", key="api_key"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": (
                "You are a helpful assistant that generates python code to answer questions."
                "You must always return python code only, no explanations, markdown, or comments."
                f"The last line of the python code must assign the result to a variable named `{RESULT_VAR}`."
            )},
            {"role": "user", "content": prompt},
        ],
    )
    output = parse_output(response.choices[0].message.content)
    print(f"generated output\n'{output}'")
    result = python_tool(output)
    return result


def python_tool(prompt: str) -> str:
    _locals = {}
    exec(prompt, globals(), _locals)
    result = _locals[RESULT_VAR]
    return str(result)


def parse_output(output: str) -> str:
    parsed_output = []
    for line in output.splitlines():
        if line.startswith("```"):
            continue
        parsed_output.append(line)

    assert RESULT_VAR in parsed_output[-1], f"The result variable {RESULT_VAR} must be assigned in the code."

    parsed_output = "\n".join(parsed_output)
    try:
        ast.parse(parsed_output)
    except SyntaxError as exc:
        raise SyntaxError(f"LLM generated invalid Python code: {exc}") from exc
    
    return parsed_output


@fk.workflow
def run(prompt: str) -> str:
    return generate_code(prompt)
