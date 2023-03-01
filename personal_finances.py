import sys
sys.path.append('..')
import numpy as np
import FinancialCalculator as fc

class PersonalFinances(object):
    def __init__(self, 
                 accounts=[],
                 initial_income = 0, 
                 initial_expense = 0, 
                 income_tax=None, 
                 fica_taxes = None, 
                 age = 18, 
                 income_growth = 0, 
                 expense_growth = 0,
                 standard_apr = 0):
        """
        
        Parameters
        ----------
        accounts : TYPE
            DESCRIPTION.
        fed_tax : TYPE, optional
            DESCRIPTION. The default is None.
        state_tax : TYPE, optional
            DESCRIPTION. The default is None.
        age : TYPE, optional
            DESCRIPTION. The default is 18.

        Returns
        -------
        None.

        """
        
        self._working = True
        self._income = None
        self._expenses = None
        self._age = age
        self._retired = False
        self._income_growth_rate = None
        self._expense_growth_rate = None
        self._accounts = {}
        self._income_tax = None
        self._fica = None

        self.SetIncomeTax(income_tax)
        self.SetFICA(fica_taxes)
        self.SetExpenses(initial_expense)
        self.SetIncome(initial_income)
        self.SetIncomeGrowthRate(income_growth)
        self.SetExpenseGrowthRate(expense_growth)

        self._agi = self._income
        
        for key in accounts:
            self.AddAccount(key, accounts[key])
            
        ##always have a 'standard' account in which leftover expenses can accumulate
        account = fc.IndividualTaxable(apr=standard_apr, tax=fc.fed_ca_tax)
        self.AddAccount('standard', account)
        
    def GetNetWorth(self):
        net_worth = 0
        for key in self._accounts:
            net_worth += self._accounts[key].GetAccountValue()
        return net_worth
        
    def GetIncome(self):
        return self._income

    def GetAge(self):
        return self._age
    
    def GetWorking(self):
        return self._working
    
    def GetRetired(self):
        return self._retired
    
    def GetExpenses(self):
        return self._expenses
    
    def GetAccountKeys(self):
        return self._accounts.keys() 
    
    def GetAccount(self, key):
        return self._accounts[key]
    
    def GetIncomeTax(self):
        return self._income_tax
    
    def GetFICA(self):
        return self._fica
    
    def SetIncome(self, income):
        self._income = income
        
    def Retire(self, retire=True):
        self._retired = retire
    
    def SetExpenses(self, expenses):
        self._expenses = expenses
        
    def SetIncomeTax(self, income_tax):
        self._income_tax = income_tax
        
    def SetFICA(self, fica):
        self._fica = fica
        
    def SetIncomeGrowthRate(self, rate):
        self._income_growth_rate = rate
        
    def SetExpenseGrowthRate(self, rate):
        self._expense_growth_rate = rate
    
    def AddAccount(self, key, account):
        if self._accounts.get(key) is not None:
            raise RuntimeError('identifier {identifier} already exists in account list. Please '
                               'use a different identifying name or remove the existing account.')
        self._accounts[key] = account
        
    def RemoveAccount(self, key, withdraw=True):
        account = self._accounts.pop(key)
        if(withdraw):
            account.Withdraw(account.GetValue())
            
    def Age(self, time_step=1):
        self._age += time_step
        for i in range(max(time_step,1)):
            contribution_deductions = 0
            self.Contribute('standard', self._income)
            for key in self._accounts:
                if self._retired:
                    self._income = 0
                    if key != 'standard':
                        withdraw = self.Withdraw(key)
                        self.Contribute('standard',withdraw)
                        self._accounts[key].Age(min(1,time_step))
                    
                else:     
                    if key != 'standard':
                        personal_contribution = self._accounts[key].GetContribution(self._income)
                        #employer_contribution = self._accounts[key].GetEmployerContribution(self._income)
                        self.Withdraw('standard', personal_contribution)
                        self.Contribute(key, personal_contribution, self._income)
                        self._accounts[key].Age(min(1,time_step))
                        if isinstance(self._accounts[key], fc.TradTaxDeferred):
                            contribution_deductions += personal_contribution
        
            self._expenses *= (1+self._expense_growth_rate)
            self._income *= (1+self._income_growth_rate)
            self.Withdraw('standard', self._expenses)
            taxes = self._income_tax.GetTax(self._income-contribution_deductions) \
                  + self._fica.GetTax(self._income)
            self.Withdraw('standard',taxes)
            self._accounts['standard'].Age(min(1,time_step))
                
    def ContributeToAll(self, amount=None, income=None):
        for key in self._accounts:
            self.Contribute(key, amount, income=income)
    
    def WithrdawFromAll(self, amount=None):
        for key in self._accounts:
            self.Withdraw(key, amount)
    
    def WithdrawAll(self, time_step=1, tax=False):
        result = 0
        for key in self._accounts:
            while(self._accounts[key].GetAccountValue() > 0):
                amount = self._accounts[key].GetAccountValue()
                result += self.Withdraw(key, np.inf, tax=tax)
        return result
    
    def Contribute(self, account_key, amount = None, income=None):
        self._accounts[account_key].Contribute(amount, income)
        
    def Withdraw(self, account_key, amount = None, tax=False):
        return self._accounts[account_key].Withdraw(amount, tax=tax)

if __name__ == '__main__':
    roth = fc.Roth(0, base_contribution=6500+8000, yearly_withdrawal=0.0, contribution_rate=0.0,
                apr=.05, contribution_cap=6500+8000)

    trad = fc.TradTaxDeferred(0, base_contribution=14500, yearly_withdrawal=0.0, contribution_rate=0.0,
                apr=.05, employer_contribution_rate=.05, tax=fc.fed_ca_tax, contribution_cap=14500)

    indtax = fc.IndividualTaxable(0, 12000, 0, 0, 0.05, tax=fc.capital_gains_tax)

    accounts = {'roth':roth, 'trad':trad, 'indtax':indtax}

    person = PersonalFinances(accounts,
                              initial_income=125000,
                              initial_expense=54000,
                              income_tax=fc.fed_ca_tax,
                              fica_taxes=fc.fica_tax,
                              age=30,
                              income_growth=.025,
                              expense_growth=.02,
                              standard_apr=.05)
    
    person.Age(15)
    print(person.GetNetWorth())
    
    print(roth.GetAccountValue(), trad.GetAccountValue(), indtax.GetAccountValue(), person.GetAccount('standard').GetAccountValue())

    print(person.WithdrawAll(tax=True))
    print(person.GetIncome())