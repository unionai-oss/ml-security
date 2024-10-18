# ML Security

```bash
flytectl demo start
export SANDBOX=1
```

Train a model:

```bash
pyflyte run --remote train.py wine_classification_workflow
```

Demo the pickle attack:

```bash
python pickle_attack.py
```

Go to demo minio instance `http://localhost:30080/minio`:

Overwrite the file `model.joblib` pointing to the trained model file
by going to the UI and uploading the file to the same path.

Then run batch predict workflow:

```bash
pyflyte run --remote serve.py run --model s3://<PATH_TO_MODEL>/model.joblib --data feature.parquet
```

Go to the Flyte UI execution view and go to the task's Kubernetes logs to see
execution of malicious code.

## Mitagation

Run secure training:

```bash
pyflyte run --remote secure_train.py wine_classification_workflow
```

Overwrite the file `model.joblib` pointing to the trained model file as
described above.

Then, run secure batch predict:

```bash
pyflyte run --remote secure_serve.py run --model s3://<PATH_TO_MODEL>/model.joblib --md5hash <MD5_HASH> --data feature.parquet
```

Go to the Flyte UI execution view to see that the workflow failed due to
a md5hash mismatch.
