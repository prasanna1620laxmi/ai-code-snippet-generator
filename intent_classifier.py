"""TensorFlow intent classifier: requirement text -> code-generation category.

A tiny Keras model (TextVectorization -> Embedding -> Dense) trained in seconds on
data/synthetic_examples.json. Falls back to keyword rules if TensorFlow is missing.
"""
import json
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data" / "synthetic_examples.json"
STORE = BASE / "models_store"
KEYWORDS = {
    "APIs": ["api", "endpoint", "rest", "fastapi", "route", "http"],
    "Classes": ["class", "model", "object", "inherit", "attribute"],
    "CRUD Operations": ["crud", "insert", "database", "sqlite", "update record", "delete record"],
    "Data Processing": ["csv", "json file", "dataset", "dataframe", "filter rows", "parse file"],
    "Automation": ["automate", "script", "rename files", "report", "schedule", "workflow", "batch"],
    "Algorithms": ["sort", "search", "factorial", "fibonacci", "prime", "graph", "recursion"],
}

_model = None
_labels: list[str] = []


def _load_data() -> tuple[list[str], list[str]]:
    rows = json.loads(DATA.read_text())
    return [r["requirement"] for r in rows], [r["category"] for r in rows]


def _keyword_predict(text: str) -> tuple[str, float]:
    low = text.lower()
    scores = {c: sum(k in low for k in ks) for c, ks in KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return (best, 0.5) if scores[best] else ("Functions", 0.3)


def train(epochs: int = 40):
    import tensorflow as tf
    texts, cats = _load_data()
    labels = sorted(set(cats))
    y = [labels.index(c) for c in cats]
    vec = tf.keras.layers.TextVectorization(max_tokens=3000, output_sequence_length=24)
    vec.adapt(tf.constant(texts))
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(1,), dtype=tf.string),
        vec,
        tf.keras.layers.Embedding(3000, 32),
        tf.keras.layers.GlobalAveragePooling1D(),
        tf.keras.layers.Dense(48, activation="relu"),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(len(labels), activation="softmax"),
    ])
    model.compile("adam", "sparse_categorical_crossentropy", metrics=["accuracy"])
    model.fit(tf.constant(texts), tf.constant(y), epochs=epochs, batch_size=16, verbose=0, validation_split=0.15)
    STORE.mkdir(exist_ok=True)
    try:
        model.save(STORE / "intent.keras")
        (STORE / "labels.json").write_text(json.dumps(labels))
    except Exception:
        pass  # saving is an optimisation only; we retrain on next start
    return model, labels


def _ensure_model():
    global _model, _labels
    if _model is not None:
        return
    import tensorflow as tf
    try:
        _model = tf.keras.models.load_model(STORE / "intent.keras")
        _labels = json.loads((STORE / "labels.json").read_text())
    except Exception:
        _model, _labels = train()


def predict(text: str) -> tuple[str, float]:
    """Return (category, confidence)."""
    try:
        import numpy as np
        import tensorflow as tf
        _ensure_model()
        probs = _model.predict(tf.constant([text]), verbose=0)[0]
        i = int(np.argmax(probs))
        return _labels[i], float(probs[i])
    except Exception:
        return _keyword_predict(text)


if __name__ == "__main__":
    m, labels = train()
    print("trained; labels:", labels)
    for t in ["Create a REST endpoint for customers", "Sort a list using merge sort"]:
        print(t, "->", predict(t))
