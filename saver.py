import sys
sys.path.append('..')
import numpy as np
import FinancialCalculator as fc

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
                 yearly_withdrawal=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 tax=None,
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
        self._yearly_withdrawal = yearly_withdrawal
        self._contribution_rate = contribution_rate
        self._tax = tax
        self._contribution_cap = contribution_cap

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
        return float('{:0.2f}'.format(self._net_contributions))
    
    def GetAccountValue(self):
        return float('{:0.2f}'.format(self._total_value))
    
    def GetTaxObject(self):
        return self._tax
    
    def GetEmployerContribution(self, income):
        if self._employer_contribution_rate is None:
            return 0
        else:
            return self._employer_contribution_rate * income
    
    def SetAPR(self, apr):
        self._apr = apr
        
    def SetContributionCap(self, contribution_cap):
        self._contribution_cap = contribution_cap
    
    def SetTaxObject(self, tax):
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
    
    def SetYearlyWithdrawal(self, withdrawal):
        self._yearly_withdrawal = withdrawal
        
    # def SetEmployerContributionRate(self, rate=None):
    #     self._employer_contribution_rate = rate
        
    def Contribute(self, contribution=None, income = None, time_step = 0, **kwargs):
        """
        Parameters
        ----------
        contribution : float, optional
            total_contribution spread over time_step. The default is None,
            and initialized to yearly contribution specified in object.
        time_step : int, optional
            time in years to spread contribution over. The default is 1.

        """
        
        if contribution is None:
            contribution = self.GetContribution(income) * max(time_step,1)
        contribution += self._additional_contributions(contribution=contribution, income=income, **kwargs) * max(time_step, 1)
        self._net_contributions += contribution
        
        if(time_step == 0):
            self._total_value += contribution
        else:
            contribution *= 1 / time_step
            for i in range(time_step):
                self._total_value += contribution
                self.Age(1)

    def Withdraw(self, amount=None, time_step = 0, **kwargs):
        
        if amount is None:
            amount = self._yearly_withdrawal
        
        tax_amount = 0
        if time_step == 0:
            self._total_value -= amount
            tax_amount += self._withdraw_tax(amount, **kwargs) 
        else:        
            for i in range(time_step):
                self._total_value -= amount/time_step
                self.Age(1)
                tax_amount += self._withdraw_tax(amount/time_step, **kwargs)            
        return float('{:0.2f}'.format(amount - tax_amount))
    
    def Age(self, time_step=1):
        self._account_age += time_step
        self._total_value *= (1+self._apr)**time_step

    def _withdraw_tax(self, amount, **kwargs):
        return 0.0

    def _additional_contributions(self, **kwargs):
        return 0.0
    
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
                 yearly_withdrawal=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 tax=None,
                 contribution_cap=np.inf,
                 employer_contribution_rate=0.0,
                 employer_contribution_match=0.0,
                 employer_contribution_cap=np.inf
                 ):
        self._overloaded = True
        Saver.__init__(self, init_value, base_contribution, yearly_withdrawal, contribution_rate, apr, tax, contribution_cap)
        self._employer_contribution_rate=employer_contribution_rate
        self._employer_contribution_match=employer_contribution_match
        self._employer_contribution_cap=employer_contribution_cap

    def _withdraw_tax(self, amount):
        if self._tax is not None:
            return self._tax.GetTax(amount)
        return 0

    def _additional_contributions(self, **kwargs):
        val = 0.0
        if 'contribution' in kwargs:
            val += self._employer_contribution_rate * kwargs['contribution']
        if 'income' in kwargs:
            val += self._employer_contribution_match * kwargs['income']
        return min(val, self._employer_contribution_cap)

class Roth(Saver):
    def __init__(self,
                 init_value=0.0,
                 base_contribution=0.0,
                 yearly_withdrawal=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 contribution_cap=np.inf,
                 employer_contribution_rate=0.0,
                 employer_contribution_match=0.0,
                 employer_contribution_cap=np.inf
                 ):
        self._overloaded = True
        Saver.__init__(self, init_value, base_contribution, yearly_withdrawal, contribution_rate, apr, None, contribution_cap)
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
    
class IndividualTaxable(Saver):
    def __init__(self,
                 init_value=0.0,
                 base_contribution=0.0,
                 yearly_withdrawal=0.0,
                 contribution_rate=0.0,
                 apr=0.0,
                 tax=None
                 ):
        self._overloaded = True
        Saver.__init__(self, init_value, base_contribution, yearly_withdrawal, contribution_rate, apr, tax)

    def _withdraw_tax(self, amount):
        #Note, this is an estimate. reality is more complictated if we're dealing with stocks...
        #Essentially, what we will assume is that we're only taxed on gains when withdrawing money (in reality, we may be selling and buying before ever truly liquidating).
        #We then assume, when withdrawing, we're selling stocks, etc., such that what we're selling gives a fractional gain the same as the fractional gain if we sold everything.
        if self._tax is not None:
            gains = self.GetAccountValue() - self._net_contributions
            estimated_taxable_amount = gains / self.GetAccountValue() * amount
            return max(self._tax.GetTax(estimated_taxable_amount), 0.0)
        return 0.0
    
#TODO : joined savings account? e.g. roth 401k plus traditional 401k with shared contribution limit

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
