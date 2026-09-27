# Decision trees

## What you will learn

- How a tree chooses splits and predicts a class.
- Why unrestricted trees can overfit.
- How depth, minimum leaf size, and class weights affect a tree.
- How `GridSearchCV` chooses tree settings with cross-validation.

## Run

```bash
ml_shit/bin/python scikit_learn_tuto/decision_trees/main.py
```

A tree is easy to inspect, but a single tree can be unstable: a small change in the data can produce a very different tree. The next lesson combines many trees to make a more robust prediction.
