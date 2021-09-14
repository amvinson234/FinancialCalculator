import FinancialCalculator as fc

class Saver(object):
    def __init__(self, initial_value=0, personal_base_contribution=0, yearly_withdrawal=0, 
                 personal_contribution_rate = 0, contribution_cap = None,
                 apr = 0, tax = None, account_type = None, employer_contribution_rate = None):
        
        self._net_contributions = initial_value
        self._total_value = initial_value
        self._account_age = 0
        self._apr = None
        self._tax = None
        self._personal_base_contribution = None
        self._yearly_withdrawal = None
        self._personal_contribution_rate = None
        self._contribution_cap = None
        self._account_type = account_type
        self._employer_contribution_rate = None
    
        self.SetAPR(apr)
        self.SetPersonalContribution(personal_base_contribution, personal_contribution_rate)
        self.SetEmployerContributionRate(employer_contribution_rate)
        self.SetAccountType(account_type)
        self.SetYearlyWithdrawal(yearly_withdrawal)
        self.SetTaxObject(tax) #Tax object (or list of tax objects?)
    
    def GetValue(self):
        return self._total_value
    
    def GetAPR(self):
        return self._apr
    
    def GetAccountAge(self):
        return self._account_age
    
    def GetPersonalContribution(self, income=None):
        contribution = 0
        if income is not None and self._personal_contribution_rate is not None:
            contribution = income*self._personal_contribution_rate
        contribution += self._personal_base_contribution
        
        if self._contribution_cap is not None:
            contribution = min(contribution, self._contribution_cap)
            
        return contribution
    
    def GetNetContributions(self):
        return float('{:0.2f}'.format(self._net_contributions))
    
    def GetAccountValue(self):
        return float('{:0.2f}'.format(self._total_value))
    
    def GetTaxObject(self):
        return self._tax
    
    def GetAccountType(self):
        return self._account_type
    
    def GetEmployerContribution(self, income):
        if self._employer_contribution_rate is None:
            return 0
        else:
            return self._employer_contribution_rate * income
    
    def SetAPR(self, apr):
        self._apr = apr
    
    def SetTaxObject(self, tax):
        self._tax = tax
        
    def SetPersonalContribution(self, base_contribution, income_rate = 0):
        self._personal_base_contribution = base_contribution
        self._personal_contribution_rate = income_rate
    
    def SetYearlyWithdrawal(self, withdrawal):
        self._yearly_withdrawal = withdrawal
        
    def SetAccountType(self, account_type = None):
        self._account_type = account_type
        
    def SetEmployerContributionRate(self, rate=None):
        self._employer_contribution_rate = rate
        
    def Contribute(self, contribution=None, income = None, time_step = 0):
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
        None.

        """
        
        if contribution is None:
            contribution = self.GetPersonalContribution(income) * max(time_step,1)
            contribution += self.GetEmployerContribution(income) * max(time_step,1)
        
        self._net_contributions += contribution
        
        if(time_step == 0):
            self._total_value += contribution
        else:
            contribution *= 1 / time_step
            for i in range(time_step):
                self._total_value += contribution
                self.Age(1)

    def Withdraw(self, amount=None, time_step = 0):
        
        if amount is None:
            amount = self._yearly_withdrawal
        
        tax_amount = 0
        if time_step == 0:
            self._total_value -= amount
            if self._tax is not None:
                tax_amount += self._tax.GetTax(amount)
        else:        
            for i in range(time_step):
                self._total_value -= amount/time_step
                self.Age(1)
                if self._tax is not None:
                    tax_amount += self._tax.GetTax(amount/time_step)
            
        return float('{:0.2f}'.format(amount - tax_amount))
    
    def Age(self, time_step=1):
        self._account_age += time_step
        self._total_value *= (1+self._apr)**time_step
        
