import numpy as np
from .parameters import ParameterList


class NoiseModelInterface:
    def __init__(self):
        self.parameter_list = ParameterList()

    def vector_contribution(self, model_error_dict):
        raise NotImplementedError()

    def loglike_contribution(self, model_error_dict):
        raise NotImplementedError()

    def _loglike_term(self, error, sigma):
        return -0.5 * (
            len(error) * np.log(2.0 * np.pi * sigma ** 2)
            + np.sum(np.square(error / sigma ** 2))
        )


class SingleSensorNoise(NoiseModelInterface):
    """
    Noise model with single term for _all_ contributions of the model error.
    """

    def vector_contribution(self, model_error_dict):
        vector_terms = []
        for exp_me in model_error_dict.values():
            if not isinstance(exp_me, dict):
                raise RuntimeError(
                    "The `SingleSensorNoise` model assumes that your model "
                    "error returns a dict {some_key : numbers}, but yours did "
                    "not. Use `SingleNoise` instead."
                )
            for sensor_me in exp_me.values():
                vector_terms.append(sensor_me)
        return np.concatenate(vector_terms)

    def jacobian_contribution(self, jacobian_dict):
        jacobian_terms = []
        for exp_jacobian in jacobian_dict.values():
            if not isinstance(exp_jacobian, dict):
                raise RuntimeError(
                    "The `SingleSensorNoise` model assumes that your model "
                    "error returns a dict {some_key : numbers}, but yours did "
                    "not. Use `SingleNoise` instead."
                )
            for sensor_jacobian in exp_jacobian.values():
                jacobian_terms.append(sensor_jacobian)

        noise_group_jacobian = np.vstack(jacobian_terms)
        return noise_group_jacobian


class UncorrelatedNoiseTerm(NoiseModelInterface):
    """
    Uncorrelated noise term that allows to specify exactly which output 
    (defined by key and sensor) from the model error is taken for the term.
    """

    def __init__(self):
        super().__init__()
        self.parameter_list.define("precision")
        self.terms = []

    def add(self, sensor, key=None):
        self.terms.append((sensor, key))

    def vector_contribution(self, model_error_dict):
        vector_terms = []
        for (sensor, key) in self.terms:
            vector_terms.append(model_error_dict[key][sensor])
        return np.concatenate(vector_terms)

    def loglike_contribution(self, model_error_dict):
        error = self.vector_contribution(model_error_dict)
        sigma = 1.0 / self.parameter_list["precision"] ** 0.5
        return self._loglike_term(error, sigma)

    def jacobian_contribution(self, jacobian_dict):
        jacobian_terms = []
        for (sensor, key) in self.terms:
            jacobian_terms.append(jacobian_dict[key][sensor])
        noise_group_jacobian = np.vstack(jacobian_terms)
        return noise_group_jacobian

class UncorrelatedSensorNoise(NoiseModelInterface):
    """
    Uncorrelated noise term that allows to specify exactly which sensors
    from the model error are taken for the term.
    """

    def __init__(self, sensors):
        super().__init__()
        self.parameter_list.define("precision")
        self.sensors = sensors

    def vector_contribution(self, model_error_dict):
        vector_terms = []
        for exp_me in model_error_dict.values():
            for sensor, values in exp_me.items():
                if sensor in self.sensors:
                    vector_terms.append(values)

        if not vector_terms:
            raise RuntimeError(
                "The model error response did not contain any "
                f"contributions from sensors {[s.name for s in self.sensors]}."
            )

        return np.concatenate(vector_terms)

    def loglike_contribution(self, model_error_dict):
        error = self.vector_contribution(model_error_dict)
        sigma = 1.0 / self.parameter_list["precision"] ** 0.5
        return self._loglike_term(error, sigma)
