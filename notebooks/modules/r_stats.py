# -*- coding: utf-8 -*-
"""
Wrappers for R statistical tests and other procedures
"""


from rpy2.robjects.packages import importr
from rpy2.robjects import numpy2ri
numpy2ri.activate()

stats = importr('stats')
rrcov = importr('rrcov')
effsize = importr('effsize')


def t_test(*args, **kwargs):
    '''
    Utilizes R's implementation of Student's t-test

    For arguments, see
    https://stat.ethz.ch/R-manual/R-patched/library/stats/html/t.test.html
    '''

    result = stats.t_test(*args, **kwargs)

    return {
        't': result.rx2('statistic')[0],
        'df': result.rx2('parameter')[0],
        'p': result.rx2('p.value')[0],
    }

def wilcox_test(*args, **kwargs):
    '''
    Utilizes R's implementation of the Wilcoxon signed-rank test

    For arguments, see
    https://stat.ethz.ch/R-manual/R-patched/library/stats/html/wilcox.test.html
    '''

    result = stats.wilcox_test(*args, **kwargs)

    return {
        'W': result.rx2('statistic')[0],
        'p': result.rx2('p.value')[0],
    }

def T2_test(*args, **kwargs):
    '''
    Utilizes the R package rrcov's implementation of Hotelling's T-squared test

    For arguments, see
    https://rdrr.io/cran/rrcov/man/T2.test.html
    '''

    result = rrcov.T2_test(*args, **kwargs)

    return {
        'T2': result.rx2('statistic')[0],
        'F': result.rx2('statistic')[1],
        'df_num': result.rx2('parameter')[0],
        'df_den': result.rx2('parameter')[1],
        'p': result.rx2('p.value')[0],
    }

def shapiro_test(*args, **kwargs):
    '''
    Utilizes R's implementation of the Shapiro-Wilk normality test

    For arguments, see
    https://stat.ethz.ch/R-manual/R-patched/library/stats/html/shapiro.test.html
    '''

    result = stats.shapiro_test(*args, **kwargs)

    return {
        'W': result.rx2('statistic')[0],
        'p': result.rx2('p.value')[0],
    }

def cohen_d(*args, **kwargs):
    '''
    Utilizes the R package effsize's implementation of Cohen's d and Hedges's g effect size

    For arguments, see
    https://rdrr.io/cran/effsize/man/cohen.d.html
    '''

    result = effsize.cohen_d(*args, **kwargs)

    return {
        'method': result.rx2('method')[0],
        'estimate': result.rx2('estimate')[0],
    }
