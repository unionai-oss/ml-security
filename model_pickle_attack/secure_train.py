import hashlib
from dataclasses import dataclass
from dataclasses_json import dataclass_json

import flytekit as fk
import joblib
import pandas as pd
from flytekit.deck import MarkdownRenderer
from flytekit.types.file import FlyteFile
from sklearn.datasets import load_wine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

from .train import task


@dataclass_json
@dataclass
class Model:
    file: FlyteFile
    md5hash: str

    def __post_init__(self):
        with open(self.file, "rb") as f:
            md5hash = hashlib.md5(f.read()).hexdigest()
        if md5hash != self.md5hash:
            raise ValueError(
                "⛔️ Model md5hash mismatch: expected "
                f"{self.md5hash}, found {md5hash}."
            )


@task
def load_data() -> tuple[pd.DataFrame, pd.Series]:
    wine = load_wine()
    X = pd.DataFrame(wine.data, columns=wine.feature_names)
    y = pd.Series(wine.target)
    return X, y


@task
def split_data(X: pd.DataFrame, y: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    return train_test_split(X, y, test_size=0.2, random_state=42)


@task
def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> Model:
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    path = "model.joblib"
    joblib.dump(model, path)
    md5hash = hashlib.md5(open(path, 'rb').read()).hexdigest()
    return Model(file=FlyteFile(path=path), md5hash=md5hash)


@task(enable_deck=True)
def evaluate_model(model: Model, X_test: pd.DataFrame, y_test: pd.Series) -> float:
    with open(model.file, "rb") as f:
        model = joblib.load(f)
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    deck = fk.Deck(name="Accuracy Report", html=MarkdownRenderer().to_html(f"# Test accuracy: {accuracy}"))
    fk.current_context().decks.insert(0, deck)
    return accuracy


@fk.workflow
def wine_classification_workflow() -> float:
    X, y = load_data()
    X_train, X_test, y_train, y_test = split_data(X, y)
    model = train_model(X_train, y_train)
    accuracy = evaluate_model(model, X_test, y_test)
    return accuracy

if __name__ == "__main__":
    wine_classification_workflow()
