import numpy as np
import unittest
from bayes.vb import *
from bayes.parameters import *
from bayes.multi_model_error import *

np.random.seed(6174)

A1,  B1, A2, B2 = 1., 2., 3., 4.
noise_sd = 0.1

N = 2000
xs = np.linspace(0, 1, N)

data_1 = A1 * xs + B1 + np.random.normal(0, noise_sd, N)
data_2 = A2 * xs + B2 + np.random.normal(0, noise_sd, N)

"""
Combining two linear models can be done _naively_ by manually defining the 
four parameters prm[0..3] and hardcode two separate model errors. In 
`multi_me`, they are both evaluated and concatenated.
"""

def model_error_1(prm):
    return prm[0] * xs + prm[1] - data_1

def model_error_2(prm):
    return prm[2] * xs + prm[3] - data_2

def multi_me(prm):
    return np.append(model_error_1(prm), model_error_2(prm))

"""
Both logically (why have two models instead of one with different parameters) 
and practially (imagine having > 100 models), this is bad. Instead, we want to
define the model once. Bonus: We want to name the parameters. e.g. "B" instead 
of index 1. Goto "test_joint" to see that in action.
"""

def model(prm):
    return prm["A"] * xs + prm["B"]

class ModelError:
    def __init__(self, fw, data):
        self.fw, self.data = fw, data

    def __call__(self, named_parameters):
        return self.fw(named_parameters) - self.data

    def evaluate(self, named_parameters):
        return OrderedDict({'sensor_1': self.fw(named_parameters) - self.data})

class Test_VB(unittest.TestCase):

    def check_posterior(self, info):
        param_post, noise_post = info.param, info.noise
        for i, param_true in enumerate([A1, B1, A2, B2]):
            posterior_mean = param_post.mean[i]
            posterior_std = param_post.std_diag[i]

            self.assertLess(posterior_std, 0.3)
            self.assertAlmostEqual(posterior_mean, param_true, delta=2 * posterior_std)
            
        post_noise_precision = noise_post.mean[0]
        post_noise_std = 1. / post_noise_precision**0.5
        self.assertAlmostEqual(post_noise_std, noise_sd, delta=noise_sd/10)
        
        self.assertLess(info.nit, 20)


    def test_multiple(self):

        prior_mean = np.r_[A1, B1, A2, B2] + 0.5 # slightly off
        prior_prec = np.r_[0.25, 0.25, 0.25, 0.25]
        prior = MVN(prior_mean, np.diag(prior_prec))

        info = variational_bayes(multi_me, prior)
        self.check_posterior(info)
      
    def test_joint_evaluate(self):
        # Define two separate parameter lists, one for each model.
        p1 = ModelParameters()
        p1.define("A")
        p1.define("B")

        p2 = ModelParameters()
        p2.define("A")
        p2.define("B")

        # Define two ModelErrors, but note that both use the same model.
        me1 = ModelError(model, data_1)
        me2 = ModelError(model, data_2)

        # For the inference, we combine them and use a 'key' to distinguish
        # e.g. "A" from the one model to "A" from the other one.
        me = MultiModelError()
        key1 = me.add(me1, p1)
        me.latent.add("B", key1)
        key2 = me.add(me2, p2)
        me.latent.add("B", key2)
        me.latent.add_by_name("A")

        parameter_vec = np.array([1,2,4])
        error_full_vector = me(parameter_vec)
        all_model_errors = me.evaluate(parameter_vec)
        error_list = []
        for key, single_me in all_model_errors.items():
            error_list.append(single_me['sensor_1'])

        np.testing.assert_almost_equal(np.concatenate(error_list), error_full_vector)

    
    def test_joint(self):
        # Define two separate parameter lists, one for each model.
        p1 = ModelParameters()
        p1.define("A")
        p1.define("B")

        p2 = ModelParameters()
        p2.define("A")
        p2.define("B")

        # Define two ModelErrors, but note that both use the same model.
        me1 = ModelError(model, data_1)
        me2 = ModelError(model, data_2)

        # For the inference, we combine them and use a 'key' to distinguish
        # e.g. "A" from the one model to "A" from the other one.
        me = MultiModelError()
        key1 = me.add(me1, p1)
        key2 = me.add(me2, p2)
        print(key1, key2)

        prior = me.uncorrelated_normal_prior()
        prior.add("A", A1+0.5, 2, key1)
        prior.add("B", B1+0.5, 2, key1)
        prior.add("A", A2+0.5, 2, key2)
        prior.add("B", B2+0.5, 2, key2)

        info = variational_bayes(me, prior.to_MVN())
        print(info)
        self.check_posterior(info)

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    unittest.main()
