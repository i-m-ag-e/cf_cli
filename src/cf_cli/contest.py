import typer
import subprocess
import os
import pathlib
import re
from typing_extensions import Annotated
from typing import Optional, Any
from enum import Enum
import termcolor
import json
import requests

app = typer.Typer()

class LangOptions(str, Enum):
    CPP = "cpp"
    RUST = "rust"

class Problem:
    def __init__(self, name: str, points: float, rating: Optional[int], index: str, url: str):
        self.name = name
        self.points = points
        self.rating = rating
        self.index = index
        self.url = url

class Contest:
    contest_id: int
    name: str
    problems: list[Problem]
    division: list[int]
    finished: bool
    
    def __init__(self, contest_id: int, name: str, problems: list[Problem], finished: bool):
        self.contest_id = contest_id
        self.name = name
        self.problems = problems
        self.finished = finished

        div_search = re.search(r"Div.\s*(\d)\s*(?:\+\s*Div.\s*(\d))?", name)
        if div_search:
            self.division = [int(div_search.group(1))]
            if div_search.group(2):
                self.division.append(int(div_search.group(2)))
        else:
            self.division = []

    @staticmethod
    def from_dict(json_data: dict[str, Any]) -> "Contest":
        problems = list(map(lambda p : Problem(
            name = p["name"],
            points = p["points"],
            rating = p.get("rating"),
            index = p["index"],
            url = f"https://codeforces.com/contest/{json_data['contest']['id']}/problem/{p['index']}"
        ), json_data["problems"]))
        return Contest(
            contest_id = json_data["contest"]["id"],
            name = json_data["contest"]["name"],
            problems = problems,
            finished = json_data["contest"]["phase"] == "FINISHED"
        )

def get_contest_info(contest_id: int, dir: pathlib.Path, update: bool = False) -> tuple[Contest, bool]:
    print(f"Update: {update}")
    if not update and (dir / f"{contest_id}" / ".contest_info.cf").exists():
        termcolor.cprint(f"Contest {contest_id} already exists in {dir}. Use -u to update.", "yellow")
        with open(dir / f"{contest_id}" / ".contest_info.cf", 'r') as f:
            json_data: dict[str, Any] = json.load(f)
            return Contest.from_dict(json_data), False

    url = f"https://codeforces.com/api/contest.standings?contestId={contest_id}&from=1&count=1"
    termcolor.cprint(f"Fetching contest info from {url}", "green")
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get contest info: {response.status_code}")
    data = json.loads(response.text)

    return Contest.from_dict(data["result"]), True

@app.command()
def new(
    contest_id: Annotated[int, typer.Argument(help="Contest ID", show_default=False)],
    dir: Annotated[str, typer.Option("--dir", "-d",
                                     help="Directory to create the contest in")] = os.getcwd(),
    name: Annotated[Optional[str], typer.Option("--name", "-n", help="Contest name", show_default=False)] = None,
    template: Annotated[Optional[str], typer.Option("--template", "-t", help="Template file to use for the contest")] = None,
    lang: Annotated[LangOptions, typer.Option("--lang", "-l", help="Language to use")] = LangOptions.RUST,
):
    name = name or f"{id}"
    contest_dir = pathlib.Path(dir) / f"{name}"
    
    if contest_dir.exists():
        typer.echo(f"Contest {contest_dir} already exists", err=True)
    
    contest_info, _ = get_contest_info(contest_id, contest_dir, True)

    contest_dir.mkdir(parents = True, exist_ok = False)
    curdir = os.getcwd()
    os.chdir(contest_dir)

    # init the cargo package
    if lang == "rust":
        subprocess.run(["cargo", "init", "--name", f"{name}"], check = True)

    with open(".contest_info.cf", 'w') as f:
        json.dump(contest_info, f, indent = 4, default = lambda o: o.__dict__)

    os.chdir(curdir)



if __name__ == "__main__":
    app()