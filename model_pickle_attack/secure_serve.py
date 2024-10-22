import flytekit as fk
import joblib
import pandas as pd

from flytekit.types.file import FlyteFile

from .train import image
from .secure_train import Model


@fk.task(container_image=image)
def model_guard(model: FlyteFile, md5hash: str) -> Model:
    return Model(file=model, md5hash=md5hash)


@fk.task(container_image=image)
def batch_predict(model: Model, data: pd.DataFrame) -> list[float]:
    with open(model, "rb") as f:
        model = joblib.load(f)
    return [float(x) for x in model.predict(data)]


@fk.workflow
def run(model: FlyteFile, md5hash: str, data: pd.DataFrame) -> list[float]:
    return batch_predict(model_guard(model, md5hash), data)
