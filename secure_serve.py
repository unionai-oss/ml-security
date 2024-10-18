import hashlib

import flytekit as fk
import joblib
import pandas as pd

from flytekit.types.file import FlyteFile

from train import image
from secure_train import Model



@fk.task(container_image=image)
def batch_predict(model: FlyteFile, md5hash: str, data: pd.DataFrame) -> list[float]:
    with open(model, "rb") as f:
        model_md5hash = hashlib.md5(f.read()).hexdigest()
    if model_md5hash != md5hash:
        raise ValueError(
            f"⛔️ Model md5hash mismatch: expected {md5hash}, found {model_md5hash}."
        )
    with open(model, "rb") as f:
        model = joblib.load(f)
    return [float(x) for x in model.predict(data)]


@fk.workflow
def run(model: FlyteFile, md5hash: str, data: pd.DataFrame) -> list[float]:
    return batch_predict(model, md5hash, data)
