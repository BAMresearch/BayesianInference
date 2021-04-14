![Python application](https://github.com/BAMresearch/BayesianInference/workflows/Python%20application/badge.svg?branch=master)

# Bayesian Inference
Collection of algorithms and helper classes to efficiently solve inference problems with both variational Bayesian and sampling methods.


# Installation as a package (should finally be automated whenever the version is changed)
Based on https://packaging.python.org/tutorials/packaging-projects/

Install a basic conda environment
```
conda env create --prefix ./conda-env -f environment.yml
```

Activate the environment
```
conda activate ./conda-env 
```

Install build
```
python -m pip install build
```

Build package
```
python -m build
```

Install package (replace * eventually by the file, if there is only one this should work)
```
python -m pip install dist/*.tar.gz
```


