import sys
import warnings
sys.path.append('..')
import numpy as np
import FinancialCalculator as fc

individual_401k_contribution_limit = 22500
total_401k_contribution_limit = 66000 #individual + employer contribution
ira_contribution_limit = 6500

class Saver(object):
    """Base Savings Account Object. Must be overloaded.

    Parameters
    ----------
    init_value : float, optional
        initial dollar value in account, by default 0
    base_contribution : float, optional
        base contribution value that user will contribute each year, by default 0
    yearly_withdrawal : float, optional
        how much value that user will extract from the account each year, by default 0
    contribution_rate : float, optional
        contribution rate of user, as a fraction of yearly income, by default 0
    apr : float, optional
        rate of growth as fraction of total account value per year, by default 0
    tax : Tax, optional
        tax object which dictates tax rates at different withdrawal amounts, by default None
    contribution_cap : float, optional
        yearly contribution cap, by default numpy.inf
    """
    def __init__(self, 
                 init_value=0.0,
                 base_contribution=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 contribution_cap=np.inf
                 ):
        
        try:
            self._overloaded
        except:
            raise RuntimeError('Must use inherited class of base Saver class')
        
        self._net_contributions = init_value
        self._total_value = init_value
        self._account_age = 0
        self._apr = apr
        self._base_contribution = base_contribution
        self._contribution_rate = contribution_rate
        self._contribution_cap = contribution_cap
        self._current_contribution = 0 #current contributions for the year
        self.taxable_withdrawals = 0
        self.deductable_contributions = 0

    def GetValue(self):
        return self._total_value
    
    def GetAPR(self):
        return self._apr
    
    def GetAccountAge(self):
        return self._account_age
    
    def GetContribution(self, income=None):
        """Returns current yearly contribution value based on set base contribution as well as income (if provided)

        Parameters
        ----------
        income : float, optional
            income for current contribution year.
            if provided, calculates contribution due to internally set contribution rate as fraction of income.
            by default None.

        Returns
        -------
        float
            contribution value amount
        """
        contribution = 0
        if income is not None and self._contribution_rate is not None:
            contribution = income*self._contribution_rate
        contribution += self._base_contribution
        
        contribution = min(contribution, self._contribution_cap)
            
        return contribution
    
    def GetNetContributions(self):
        """
        Returns
        -------
        float
            Net contributions in this account's lifespan
        """
        return float('{:0.2f}'.format(self._net_contributions))
    
    def GetAccountValue(self):
        """
        Returns
        -------
        float
            Current  account value
        """
        return float('{:0.2f}'.format(self._total_value))
    
    def GetTaxObject(self):
        """
        Returns
        -------
        Tax
            tax object associated with account
        """
        return self._tax
    
    def SetAPR(self, apr):
        """set return rate as annual percentage return (APR)

        Parameters
        ----------
        apr : float
            fractional return rate. e.g. 5% annual return corresponds to input of `apr=.05`
        """
        self._apr = apr
        
    def SetContributionCap(self, contribution_cap):
        """
        Parameters
        ----------
        contribution_cap : float
            personal contribution cap to apply to this account
        """
        self._contribution_cap = contribution_cap
    
    def SetTaxObject(self, tax):
        """
        Parameters
        ----------
        tax : Tax
            tax object to associate with account withdrawals
        """
        self._tax = tax
        
    def SetContribution(self, base_contribution=None, contribution_rate=None):
        """Set base contribution and contribution rate

        Parameters
        ----------
        base_contribution : float, optional
            base contribution value annually, by default None.
            If None, then base contribution will remain unchanged.
        contribution_rate : float, optional
            contribution as a fraction of income, by default None.
            If None, then contribution rate will remain unchanged.
        """
        
        if base_contribution is not None:
            self._base_contribution = base_contribution
        if contribution_rate is not None:
            self._contribution_rate = contribution_rate
    
    def Contribute(self, contribution=None, income = None, employer=False, **kwargs):
        """
        Parameters
        ----------
        contribution : float, optional
            total_contribution spread over time_step. The default is None,
            and initialized to yearly contribution specified in object.
        time_step : int, optional
            time in years to spread contribution over. The default is 1.

        Returns
        -------
        float
            attempted contribution which was above contribution cap.
            should be a value 0 (if contribution was below the cap) or greater.

        """
        over = 0.0
        if contribution is None:
            contribution = self.GetContribution(income)
        else:
            if contribution > (self._contribution_cap-self._current_contribution):
                over = (contribution - self._contribution_cap + self._current_contribution)
                contribution = self._contribution_cap

        contribution += self._additional_contributions(contribution=contribution, income=income, employer=employer, **kwargs)
        self._net_contributions += contribution
        self._current_contribution += contribution
        self._total_value += contribution
        
        self._udpate_deductable_contributions(contribution, income, employer, **kwargs)

        return over

    def Withdraw(self, amount, **kwargs):
        """Withdraw value amount over specified time

        Parameters
        ----------
        amount : float, optional
            amount to remove from account, by default None.
            If none, will withdraw amount specified from `self.SetYearlyWithdrawal(amount)`
        time_step : int, optional
            time over which amount will be withrawn, by default 0
        tax : bool, optional
            whether to apply tax to withrawal. by default False
        kwargs : arguments to pass to overloaded function _withdraw_tax

        Returns
        -------
        float
            value withdrawn (after taxes if `tax == True`)
        """
        
        amount = min(amount, self._total_value)
        self._udpate_taxable_withdrawals(amount, **kwargs)

        #TODO return anything?
        self._total_value -= amount
            
    def Age(self):
        #TODO : implement auto withdrawals and contributions?
        """Advance age of account by 1 year.
        Currently just advances age and calculates new value from APR growth.
        Does NOT currently implement automatic contributions or withdrawals

        Parameters
        ----------
        time_step : int, optional
            years to advance age of account by, by default 1
        """
        self._account_age += 1
        self._total_value *= (1+self._apr)
        self._current_contribution = 0
        self.deductable_contributions = 0
        self.taxable_withdrawals = 0

        self._age()

    def _additional_contributions(self, **kwargs):
        return 0.0
    
    def _udpate_taxable_withdrawals(self, amount, **kwargs):
        pass

    def _udpate_deductable_contributions(self, contribution, income, employer, **kwargs):
        pass
    
    def _age(self):
        pass

class Saver401k(Saver):
    def __init__(self, 
                 init_value_trad = 0,
                 init_value_roth = 0,
                 init_afterTax = 0,
                 apr = 0.0,
                 individual_contribution_cap = individual_401k_contribution_limit,
                 total_contribution_cap = total_401k_contribution_limit,
                 employer_contribution_rate = 0.0,
                 employer_contribution_match = 0.0,
                 employer_contribution_cap = total_401k_contribution_limit - individual_401k_contribution_limit
                 ):
        self._overloaded = True  

        #TODO :
        # update base saver values  while trad and roth are being updated
        Saver.__init__(self,
                       init_value=init_value_trad+init_afterTax+init_afterTax,
                       apr=apr
                      )
        self._trad = TradTaxDeferred(init_value=init_value_trad,
                                     apr=apr,
                                     employer_contribution_rate=employer_contribution_rate,
                                     employer_contribution_match=employer_contribution_match,
                                     employer_contribution_cap=employer_contribution_cap)
        self._roth = Roth(init_value=init_value_roth, 
                          apr=apr)
        self._afterTax = IndividualTaxable(init_value=init_afterTax, 
                               apr=apr)
        self.total_contribution_cap = total_contribution_cap
        self.individual_contribution_cap = individual_contribution_cap
        self.employer_contribution_cap = employer_contribution_cap

        self._current_contribution_individual = 0
        self._current_contribution_employer = 0
        self._current_contribution = 0

    def ContributeTraditional(self, contribution=None, income=None, employer=False):
        contr_limit_warning = 'Attempted to contribute more than contributions limits allow. Automatically lowering contribution to be equal to max allowable.'
        # if self._current_contribution + contribution > self.total_contribution_cap:
        #     warnings.warn(contr_limit_warning)
        #     contribution = self._current_contribution - self._current_contribution
        # if employer:
        #     if contribution is not None and self._current_contribution_employer + contribution > self.employer_contribution_cap:
        #         warnings.warn(contr_limit_warning)
        #         contribution = self.employer_contribution_cap - self._current_contribution_employer
        # else:
        #     if self._current_contribution_individual + contribution > self.individual_contribution_cap:
        #         warnings.warn(contr_limit_warning)
        #         contribution = self.individual_contribution_cap - self._current_contribution_individual

        self._trad.Contribute(contribution, income=income, employer=employer)
        self._current_contribution_individual = self._trad._current_contribution_individual + self._roth._current_contribution + self._afterTax._current_contribution
        self._current_contribution_employer = self._trad._current_contribution_employer
        self._current_contribution = self._trad._current_contribution + self._roth._current_contribution + self._afterTax._current_contribution
        self._net_contributions = self._trad._net_contributions + self._roth._net_contributions + self._afterTax._net_contributions
        self.deductable_contributions = self._trad.deductable_contributions + self._roth.deductable_contributions + self._afterTax.deductable_contributions

    def ContributeRoth(self, contribution, income=None, employer=False):
        # contr_limit_warning = 'Attempted to contribute more than contributions limits allow. Automatically lowering contribution to be equal to max allowable.'
        # if self._current_contribution + contribution > self.total_contribution_cap:
        #     warnings.warn(contr_limit_warning)
        #     contribution = self._current_contribution - self._current_contribution
        # self._current_contribution_individual += contribution
        # self._current_contribution += contribution
        self._roth.Contribute(contribution, income=income, employer=employer)
        self._current_contribution_individual = self._trad._current_contribution_individual + self._roth._current_contribution + self._afterTax._current_contribution
        self._current_contribution_employer = self._trad._current_contribution_employer
        self._current_contribution = self._trad._current_contribution + self._roth._current_contribution + self._afterTax._current_contribution
        self._net_contributions = self._trad._net_contributions + self._roth._net_contributions + self._afterTax._net_contributions
        self.deductable_contributions = self._trad.deductable_contributions + self._roth.deductable_contributions + self._afterTax.deductable_contributions

    def WithdrawTraditional(self, amount=None, **kwargs):
        self._trad.Withdraw(amount, **kwargs)
        self._total_value = self._trad._total_value + self._roth._total_value + self._afterTax._total_value
        self.taxable_withdrawals = self._roth.taxable_withdrawals + self._afterTax.taxable_withdrawals + self._trad.taxable_withdrawals
    
    def WithdrawRoth(self, amount, **kwargs):
        self._roth.Withdraw(amount, **kwargs)
        self.taxable_withdrawals = self._roth.taxable_withdrawals + self._afterTax.taxable_withdrawals + self._trad.taxable_withdrawals

    def Contribute(self, contribution=None, income=None, employer=False, **kwargs):
        #TODO : this should be a _contribute() class, and super class shouldn't do much, but call _contribute()
        #       same for withdraw
        rta = ['roth', 'traditional', 'aftertax']
        cnt = 0
        for el in rta:
            if el in kwargs.keys() and kwargs[acct_type] == True:
                acct_type = el
                cnt+=1
        if cnt > 1:
            raise RuntimeError('Only specify only one account type, traditional, roth, or aftertax')
        if cnt < 1:
            raise RuntimeError('Must specify a boolean parameter roth, traditional, or aftertax')
        
        if acct_type == 'roth':
            self.ContributeRoth(contribution, income, employer)
        if acct_type == 'traditional':
            self.ContributeTraditional(contribution, income, employer)
        if acct_type == 'aftertax':
            raise RuntimeError('aftertax not yet supported.')
        
    def Withdraw(self, amount=None, **kwargs):
        rta = ['roth', 'traditional', 'aftertax']
        cnt = 0
        for el in rta:
            if el in kwargs.keys() and kwargs[acct_type] == True:
                acct_type = el
                cnt+=1
        if cnt > 1:
            raise RuntimeError('Only specify only one account type, traditional, roth, or aftertax')
        if cnt < 1:
            raise RuntimeError('Must specify a boolean parameter roth, traditional, or aftertax')
        
        if acct_type == 'roth':
            self.WithdrawRoth(amount)
        if acct_type == 'traditional':
            self.WithdrawTraditional(amount)
        if acct_type == 'aftertax':
            raise RuntimeError('aftertax not yet supported.')
        
    def _age(self):
        self._roth.Age()
        self._trad.Age()
        self._afterTax.Age()
    
class TradTaxDeferred(Saver):
    """Traditional tax deferred savings account (e.g. Traditional 401k)
    Parameters
    ----------
    init_value : float, optional
        initial dollar value in account, by default 0
    base_contribution : float, optional
        base contribution value that user will contribute each year, by default 0
    yearly_withdrawal : float, optional
        how much value that user will extract from the account each year, by default 0
    contribution_rate : float, optional
        contribution rate of user, as a fraction of yearly income, by default 0
    apr : float, optional
        rate of growth as fraction of total account value per year, by default 0
    tax : Tax, optional
        tax object which dictates tax rates at different withdrawal amounts, by default None
    contribution_cap : float, optional
        yearly contribution cap, by default None
    employer_contribution_rate : float, optional
        emoloyer contribution rate as fraction of user's income, by default None
    employer_contribution_match : float, optional
        employer contribution rate as a fraction matching user's contribution
    employer_contribution_cap : flaot, optional
        maximum employer contribution value
    """

    def __init__(self,
                 init_value=0.0,
                 base_contribution=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 employer_contribution_rate=0.0,
                 employer_contribution_match=0.0,
                 employer_contribution_cap=np.inf
                 ):
        self._overloaded = True
        Saver.__init__(self, init_value, base_contribution, contribution_rate, apr)
        self._employer_contribution_rate=employer_contribution_rate
        self._employer_contribution_match=employer_contribution_match
        self._employer_contribution_cap=employer_contribution_cap
        self.individual_contribution_cap = individual_401k_contribution_limit
        self.total_contribution_cap = individual_401k_contribution_limit
        self._current_contribution_individual = 0
        self._current_contribution_employer = 0

    def _additional_contributions(self, contribution, income, employer, **kwargs):
        val = 0.0
        if employer:
            if income is not None:
                val += self._employer_contribution_rate * income
            val += self._employer_contribution_match * contribution
            val = max(0,min(val, self._employer_contribution_cap-self._current_contribution_employer))
            self._current_contribution_employer += val
        else:
            ind_contr = min(contribution, self.individual_contribution_cap-self._current_contribution_individual)
            employer_contr = self._employer_contribution_match * contribution
            employer_contr = max(0,min(val, self._employer_contribution_cap-self._current_contribution_employer))
            self._current_contribution_employer += employer_contr
            self._current_contribution_individual += ind_contr
            val += employer_contr - (contribution-ind_contr)
        return val
    
    def _udpate_taxable_withdrawals(self, amount, **kwargs):
        self.taxable_withdrawals += amount

    def _udpate_deductable_contributions(self, contribution, income, employer, **kwargs):
        self.deductable_contributions = self._current_contribution_individual

    def _age(self):
        self._current_contribution_individual = 0
        self._current_contribution_employer = 0

class Roth(Saver):
    """Roth savings account 
    Parameters
    ----------
    init_value : float, optional
        initial dollar value in account, by default 0
    base_contribution : float, optional
        base contribution value that user will contribute each year, by default 0
    yearly_withdrawal : float, optional
        how much value that user will extract from the account each year, by default 0
    contribution_rate : float, optional
        contribution rate of user, as a fraction of yearly income, by default 0
    apr : float, optional
        rate of growth as fraction of total account value per year, by default 0
    contribution_cap : float, optional
        yearly contribution cap, by default None
    employer_contribution_rate : float, optional
        emoloyer contribution rate as fraction of user's income, by default None
    employer_contribution_match : float, optional
        employer contribution rate as a fraction matching user's contribution
    employer_contribution_cap : flaot, optional
        maximum employer contribution value
    """
    def __init__(self,
                 init_value=0.0,
                 base_contribution=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 contribution_cap=np.inf,
                 employer_contribution_rate=0.0,
                 employer_contribution_match=0.0,
                 employer_contribution_cap=np.inf
                 ):
        self._overloaded = True
        Saver.__init__(self, init_value, base_contribution, contribution_rate, apr, contribution_cap)
        self._employer_contribution_rate=employer_contribution_rate
        self._employer_contribution_match=employer_contribution_match
        self._employer_contribution_cap=employer_contribution_cap

    def _additional_contributions(self, **kwargs):
        val = 0.0
        if 'contribution' in kwargs and kwargs['contribution'] is not None:
            val += self._employer_contribution_match * kwargs['contribution']
        if 'income' in kwargs and kwargs['income'] is not None:
            val += self._employer_contribution_rate * kwargs['income']
        return min(val, self._employer_contribution_cap)

    def _age(self):
        self._current_contribution_individual = 0
        self._current_contribution_employer = 0
    
class IndividualTaxable(Saver):
    """Individual Taxable Account Object. Must be overloaded.

    Parameters
    ----------
    init_value : float, optional
        initial dollar value in account, by default 0
    base_contribution : float, optional
        base contribution value that user will contribute each year, by default 0
    yearly_withdrawal : float, optional
        how much value that user will extract from the account each year, by default 0
    contribution_rate : float, optional
        contribution rate of user, as a fraction of yearly income, by default 0
    apr : float, optional
        rate of growth as fraction of total account value per year, by default 0
    tax : Tax, optional
        tax object which dictates tax rates at different withdrawal amounts, by default None
    """
    def __init__(self,
                 init_value=0.0,
                 base_contribution=0.0,
                 yearly_withdrawal=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 employer_contribution_rate=0.0,
                 employer_contribution_match=0.0,
                 employer_contribution_cap=np.inf
                 ):
        self._overloaded = True
        Saver.__init__(self, init_value, base_contribution, yearly_withdrawal, contribution_rate, apr)
        self._employer_contribution_rate=employer_contribution_rate
        self._employer_contribution_match=employer_contribution_match
        self._employer_contribution_cap=employer_contribution_cap
    
    def _additional_contributions(self, **kwargs):
        val = 0.0
        if 'contribution' in kwargs and kwargs['contribution'] is not None:
            val += self._employer_contribution_match * kwargs['contribution']
        if 'income' in kwargs and kwargs['income'] is not None:
            val += self._employer_contribution_rate * kwargs['income']
        return min(val, self._employer_contribution_cap)
    
    def _age(self):
        self._current_contribution_individual = 0
        self._current_contribution_employer = 0

if __name__ == '__main__':
    roth = Roth(0, base_contribution=6500+8000, yearly_withdrawal=0.0, contribution_rate=0.0,
                apr=.05)
    roth.Contribute(income=133000,time_step=15)

    trad = TradTaxDeferred(0, base_contribution=14500, yearly_withdrawal=0.0, contribution_rate=0.0,
                apr=.05, employer_contribution_rate=.05, tax=fc.fed_ca_tax)
    trad.Contribute(income=133000,time_step=15)

    indtax = IndividualTaxable(0, 24000, 0, 0, 0.05, tax=fc.fed_ca_tax) #tax should really be long-term capital gains?
    indtax.Contribute(time_step=15)
    
    print(roth.GetNetContributions(), roth.GetAccountValue())
    print(trad.GetNetContributions(), trad.GetAccountValue())
    print(indtax.GetNetContributions(), indtax.GetAccountValue())

    print(roth.GetAccountValue()*.04, roth.Withdraw(roth.GetAccountValue()*.04))
    print(trad.GetAccountValue()*.04, trad.Withdraw(trad.GetAccountValue()*.04))
    print(indtax.GetAccountValue()*.04, indtax.Withdraw(indtax.GetAccountValue()*.04))
