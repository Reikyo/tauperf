import re
from rootpy.plotting import Graph
from . import log; log = log[__name__]
from . import samples
from .classify import Classifier, working_point
from .parallel import FuncWorker, Worker, run_pool
from .categories import CATEGORIES

from . import NTUPLE_PATH
VAR_PATTERN = re.compile('((?P<prefix>hlt|off|true)_)?(?P<var>[A-Za-z0-9_]+)(\*(?P<scale>\d+\.\d*))?$')


class Analysis(object):
    
    def __init__(self, 
                 ntuple_path=NTUPLE_PATH,
                 use_drellyan=False,
                 use_jz_slices=False,
                 trigger=False,
                 no_weight=False):

        if use_drellyan:
            log.info('Use Drell-Yan simulation')
            self.tau = samples.DY(
            ntuple_path=ntuple_path,
            weight_field='pu_weight', #mc_event_weight',
            name='tau', 
            label='Real #tau_{had}',
            trigger=trigger,
            color='#00A3FF')
        else:
            log.info('Use Z->tautau simulation')
            self.tau = samples.Tau(
                ntuple_path=ntuple_path,
                name='tau', 
                label='Real #tau_{had}',
                trigger=trigger,
                weight_field=None if no_weight else 'pu_weight', 
                color='#00A3FF')

        if use_jz_slices:
            log.info('Use JZ samples for bkg')
            self.jet = samples.JZ(
                ntuple_path=ntuple_path,
                name='jet', 
                label='Fake #tau_{had}',
                trigger=trigger,
                weight_field=('mc_event_weight', 'pu_weight', 'pt_weight'), 
                color='#00FF00')
        else:
            log.info('Use data for bkg')
            self.jet = samples.DataJet(
                ntuple_path=ntuple_path,
                student='data',
                name='jet', 
                label='Fake #tau_{had}',
                trigger=trigger,
                # weird, please fix asap!
                weight_field=None if no_weight else 'pt_weight',
                color='#00FF00')
            
        self.trigger = trigger
        log.info('Analysis object is instantiated')

    def iter_categories(self, *definitions, **kwargs):
        names = kwargs.pop('names', None)
        for definition in definitions:
            for category in CATEGORIES[definition]:
                if names is not None and category.name not in names:
                    continue
                log.info("")
                log.info("=" * 40)
                log.info("%s category" % category.name)
                log.info("=" * 40)
                log.info("Signal cuts: %s" % self.tau.cuts(category))
                log.info("Background cuts: %s" % self.jet.cuts(category))
                yield category

    def get_hist_samples_array(self, vars, prefix, dummy_range=False, **kwargs):
        """
        """
        field_hist_tau = self.tau.get_field_hist(vars, prefix, dummy_range=dummy_range)
        log.debug('Retrieve Tau histograms')
        field_hist_tau = self.tau.get_hist_array(field_hist_tau, **kwargs)
        field_hist_jet = self.jet.get_field_hist(vars, prefix, dummy_range=dummy_range)
        log.debug('Retrieve Jet histograms')
        field_hist_jet = self.jet.get_hist_array(field_hist_jet, **kwargs)
        hist_samples_array = {}
        for key in field_hist_tau:
            match = re.match(VAR_PATTERN, key)
            if match:
                hist_samples_array[match.group('var')] = {
                    'tau': field_hist_tau[key],
                    'jet': field_hist_jet[key]
                }
            else:
                log.warning('No pattern matching for {0}'.format(key))
        return hist_samples_array

    def get_hist_signal_array(self, vars, prefix1, prefix2, **kwargs):
        """
        """
        field_hist_tau_1 = self.tau.get_field_hist(vars, prefix1)
        field_hist_tau_2 = self.tau.get_field_hist(vars, prefix2)
        log.debug('Retrieve Tau histograms')
        field_hist_tau_1 = self.tau.get_hist_array(field_hist_tau_1, **kwargs)
        field_hist_tau_2 = self.tau.get_hist_array(field_hist_tau_2, **kwargs)
        
        hist_samples_array = {}
        for key in field_hist_tau_1:
            match = re.match(VAR_PATTERN, key)
            if match:
                field_hist_tau_1[key].title += ' ({0})'.format(prefix1)
                hist_samples_array[match.group('var')] = {prefix1: field_hist_tau_1[key]}
        for key in field_hist_tau_2:
            match = re.match(VAR_PATTERN, key)
            if match:
                field_hist_tau_2[key].title += ' ({0})'.format(prefix2)
                hist_samples_array[match.group('var')][prefix2] = field_hist_tau_2[key]
        return hist_samples_array


    def train(self, 
              prefix,
              category=None,
              verbose='',
              features='features_pileup_corrected',
              cuts_features='cuts_features_pileup_corrected',
              n_jobs=1,
              **kwargs):

        if category is not None:
            categories = [category]
        else:
            if self.trigger:
                categories = CATEGORIES['training_hlt']
            else:
                categories = CATEGORIES['training']

        classifiers = []
        for cat in categories:
            cls_odd = Classifier(
                cat, 
                'weights/summary_odd_{0}_{1}.root'.format(cat.name, features),
                '{0}_odd_{1}'.format(cat.name, features),
                prefix=prefix,
                train_split='odd',
                test_split='even',
                features=features,
                cuts_features=cuts_features,
                verbose=verbose)
            cls_even = Classifier(
                cat, 
                'weights/summary_even_{0}_{1}.root'.format(cat.name, features),
                '{0}_even_{1}'.format(cat.name, features),
                prefix=prefix,
                train_split='even',
                test_split='odd',
                features=features,
                cuts_features=cuts_features,
                verbose=verbose)
            classifiers += [cls_odd, cls_even]
            
        
        if n_jobs == 1:
            for cls in classifiers:
                cls.train(self.tau, self.jet, **kwargs)
        else:
            procs = [FuncWorker(
                    cls.train, self.tau, self.jet, **kwargs)
                     for cls in classifiers]
            run_pool(procs, n_jobs=n_jobs)

