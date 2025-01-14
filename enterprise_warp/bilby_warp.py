import bilby

class PTABilbyLikelihood(bilby.Likelihood):
    """
    The class that wraps Enterprise likelihood in Bilby likelihood.

    Parameters
    ----------
    pta: enterprise.signals.signal_base.PTA
      Enterprise PTA object that contains pulsar data and noise models
    parameters: list
      A list of signal parameter names
    """
    def __init__(self, pta, parameters):
        self.pta = pta
        self.parameters = parameters
        self._marginalized_parameters = []

    def log_likelihood(self):
        tmparams = []
        tmparamname = None
        curparameters = {}
        
        # add timing parameters into a list
        for param in self.parameters:
            if "timing model_tmparams" in param:
                tmparams.append(self.parameters[param])
                if tmparamname is None:
                    tmparamname = "_".join(param.split("_")[:-1])
            else:
                curparameters[param] = self.parameters[param]
        if tmparamname is not None:
            curparameters[tmparamname] = tmparams

        return self.pta.get_lnlikelihood(curparameters)

    def get_one_sample(self):
        return {par.name: par.sample() for par in self.pta.params}

def get_bilby_prior_dict(pta):
    """
    Get Bilby parameter dict from Enterprise PTA object.
    Currently only works with uniform priors.

    Parameters
    ----------
    pta: enterprise.signals.signal_base.PTA
      Enterprise PTA object that contains pulsar data and noise models
    """
    priors = dict()
    for param in pta.params:

        if param.size==None:
            if param.type=='uniform':
                #priors[param.name] = bilby.core.prior.Uniform( \
                #    param._pmin, param._pmax, param.name)
                priors[param.name] = bilby.core.prior.Uniform( \
                    # param._pmin
                    param.prior._defaults['pmin'], param.prior._defaults['pmax'], \
                    param.name)
            elif param.type=='normal':
                #priors[param.name] = bilby.core.prior.Normal( \
                #    param._mu, param._sigma, param.name)
                priors[param.name] = bilby.core.prior.Normal( \
                    param.prior._defaults['mu'], param.prior._defaults['sigma'], \
                    param.name)
            elif param.type=='truncatednormal':
                priors[param.name] = bilby.core.prior.TruncatedGaussian( \
                    param.prior._defaults['mu'], param.prior._defaults['sigma'], \
                    param.prior._defaults['minv'], param.prior._defaults['maxv'], \
                    param.name)
            else:
                raise ValueError(
                    "Unknown prior type for translation into Bilby. "
                    "Known types: Normal, Uniform."
                )

        else:
            print(param.name, param.type)
            if param.name=='jup_orb_elements' and param.type=='uniform':
                for ii in range(param.size):
                    priors[param.name+'_'+str(ii)] = bilby.core.prior.Uniform(
                        -0.05, 0.05, param.name+'_'+str(ii)
                    )
            elif "timing model_tmparams" in param.name and param.type == "uniform":
                for ii in range(param.size):
                    priors[param.name + "_" + str(ii)] = bilby.core.prior.Uniform(
                        param.prior._defaults['pmin'],
                        param.prior._defaults['pmax'],
                        param.name + "_" + str(ii)
                    )
            else:
                raise ValueError(
                    "Unknown prior with non-unit size for "
                    "translation into Bilby. Known prior: "
                    "jup_orb_elements or tmparams of type "
                    "Uniform."
                )

    # Consistency check
    for key, val in priors.items():
        if key not in pta.param_names:
            print('[!] Warning: Bilby\'s ',key,' is not in PTA params:',\
                  pta.param_names)

    return priors
