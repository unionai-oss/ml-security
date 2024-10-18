import flytekit as fk
import joblib
import pandas as pd

from flytekit.types.file import FlyteFile

from train import image



@fk.task(container_image=image)
def batch_predict(model: FlyteFile, data: pd.DataFrame) -> list[float]:
    with open(model, "rb") as f:
        model = joblib.load(f)
    return [float(x) for x in model.predict(data)]


@fk.workflow
def run(model: FlyteFile, data: pd.DataFrame) -> list[float]:
    return batch_predict(model, data)
