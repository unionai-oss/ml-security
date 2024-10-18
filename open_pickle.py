import joblib

with open("model.joblib", "rb") as f:
    model = joblib.load(f)

print(model)
