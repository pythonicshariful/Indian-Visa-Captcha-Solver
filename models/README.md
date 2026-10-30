# CNN model file goes here

The `cnn` solver needs the trained Keras model at:

```
models/captcha_model.keras
```

The file is ~51 MB, so it is **not stored in this git repo** (see
`.gitignore`). Download it here and copy it into this folder:

**[Download captcha_model.keras (Google Drive)](https://drive.google.com/file/d/1jxr-zIRxLjDlbN1cPWebpR2NrvYsaTqA/view?usp=drivesdk)**

It comes from the `captcha-breaker-ml` project (trained on the
Captcha-v2 dataset with the GeeksforGeeks CNN architecture).

Model limits (measured on held-out test data): 5 characters only,
lowercase a-z + 0-9 output, per-char accuracy ~54%, and it was NOT
trained on Indian Visa captchas — see `cnn_solver.py` for details.
