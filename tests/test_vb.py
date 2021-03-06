import numpy as np
import unittest
from bayes.vb import *
from bayes.parameters import ParameterList
from bayes.noise import SingleSensorNoise


class ForwardModel:
    def __init__(self):
        self.xs = np.linspace(0.01, 0.1, 10)

    def __call__(self, parameters):
        m, c = parameters
        return c + self.xs * m

    def jacobian(self, parameters):
        m, c = parameters
        d_dm = self.xs
        d_dc = np.ones_like(self.xs)
        return np.vstack([d_dm, d_dc]).T


class ModelError(VariationalBayesInterface):
    def __init__(self, forward_model, data):
        """
        forward_model:
            forward model
        data:
            positions to evaluate, could correspond to sensor positions
        """
        self._forward_model = forward_model
        self._data = data

    def __call__(self, parameters):
        model = self._forward_model(parameters)
        errors = []
        for data in self._data:
            errors.append(model - data)

        return {"noise0": np.concatenate(errors)}


class ModelErrorWithJacobian(ModelError):
    def jacobian(self, parameters):
        jac = -self._forward_model.jacobian(parameters)
        full_jac = np.tile(jac, (len(self._data), 1))
        return {"noise0": full_jac}


class Test_VB(unittest.TestCase):
    def run_vb(self, n_data, given_jac=False, plot=False):
        np.random.seed(6174)

        fw = ForwardModel()
        param_true = [7.0, 10.0]
        noise_sd = 0.1

        data = []
        perfect_data = fw(param_true)
        for _ in range(n_data):
            data.append(perfect_data + np.random.normal(0, noise_sd, len(perfect_data)))

        if given_jac:
            me = ModelErrorWithJacobian(fw, data)
        else:
            me = ModelError(fw, data)

        param_prior = MVN([6, 11], [[1 / 3 ** 2, 0], [0, 1 / 3 ** 2]])
        noise_prior = {"noise0": Gamma.FromSD(3*noise_sd)}

        info = variational_bayes(me, param_prior, noise_prior)
        param_post, noise_post = info.param, info.noise

        if plot:
            plot_pdf(
                param_post,
                expected_value=param_true,
                compare_with=param_prior,
                plot="joint",
            )

        for i in range(2):
            posterior_mean = param_post.mean[i]
            posterior_std = param_post.std_diag[i]

            self.assertLess(posterior_std, 0.3)
            self.assertAlmostEqual(
                posterior_mean, param_true[i], delta=2 * posterior_std
            )

            post_noise_precision = noise_post["noise0"].mean
        post_noise_sd = 1.0 / post_noise_precision ** 0.5
        self.assertAlmostEqual(post_noise_sd, noise_sd, delta=noise_sd / 100)

        self.assertLess(info.nit, 20)
        print(info)

    def test_vb_with_numeric_jac(self):
        self.run_vb(n_data=1000, given_jac=False)

    def test_vb_with_given_jac(self):
        self.run_vb(n_data=1000, given_jac=True, plot=False)


if __name__ == "__main__":
    import logging

    logging.basicConfig(level=logging.DEBUG)
    unittest.main()
