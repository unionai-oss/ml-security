import ast
import json
import os
import subprocess
import tempfile
from datetime import timedelta

import flytekit as fk
from flytekit.deck import MarkdownRenderer
from functools import partial, wraps

registry = None
if int(os.getenv("SANDBOX", 1)):
    registry = "localhost:30000"


image = fk.ImageSpec(packages=["openai"], registry=registry)
guardrail_image = fk.ImageSpec(packages=["bandit"], registry=registry)

RESULT_VAR = "result"


task = partial(fk.task, container_image=image)


DISALLOWED_PATTERNS = [
    # restricted imports
    "import importlib",
    "import os",
    "import http",
    "import urllib",
    "import requests",
    "import httpx",
    "import subprocess",
    "import shutil",

    # no urls
    "https://",
    "http://",
]


def output_guard(fn):

    @wraps(fn)
    def wrapper(*args, **kwargs):
        out = fn(*args, **kwargs)
        assert isinstance(out, str)
        for disallowed in DISALLOWED_PATTERNS:
            if disallowed in out:
                raise ValueError(f"Prompt contains forbidden pattern '{disallowed}'")
        return out
    
    return wrapper


@task(secret_requests=[fk.Secret(group="openai", key="api_key")], enable_deck=True, deck_fields=[])
@output_guard
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
    fk.Deck("generated code", MarkdownRenderer().to_html(output))
    return output


def code_guard(fn):
    @wraps(fn)
    def wrapper(prompt: str):
        with tempfile.NamedTemporaryFile("w") as f:
            with tempfile.NamedTemporaryFile("w") as json_f:
                f.write(prompt)
                f.flush()

                subprocess.run(["bandit", "-f", "json", "-o", json_f.name, f.name])

                with open(json_f.name, "r") as json_read:
                    report = json.load(json_read)

                print(json.dumps(report, indent=4))
                
                if (
                    report["metrics"]["_totals"]["SEVERITY.HIGH"] > 0
                    or report["metrics"]["_totals"]["SEVERITY.MEDIUM"] > 0
                    or report["metrics"]["_totals"]["SEVERITY.LOW"] > 0
                ):
                    raise ValueError(
                        f"Prompt contains insecure code:\nBandit Report:\n{json.dumps(report, indent=4)}"
                    )

        return fn(prompt)
    return wrapper


@fk.task(container_image=guardrail_image)
@code_guard
def python_tool(prompt: str) -> str:
    _locals = {}
    exec(prompt, {}, _locals)
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
    code = generate_code(prompt)
    approved_code = fk.approve(code, "approve", timeout=timedelta(minutes=10))
    return python_tool(approved_code)
