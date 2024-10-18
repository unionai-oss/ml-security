from flytekit.types.file import FlyteFile


class StrictFile(FlyteFile):
    def __init__(self, path: str):
        super().__init__(path)

    def read(self) -> str:
        with open(self.path, "r") as f:
            return f.read()
