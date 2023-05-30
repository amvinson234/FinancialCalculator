import sys
sys.path.append('..')
import numpy as np
import FinancialCalculator as fc

class PersonalFinances(object):
    def __init__(self, 
                 accounts={},
                 initial_income = 0, 
                 initial_expense = 0,
                 initial_standard_value = 0,
                 standard_apr=0.0,
                 income_tax_bucket = [],
                 fica_tax_bucket = None,
                 account_tax_buckets = [],
                 age = 18, 
                 income_growth = 0, 
                 expense_growth = 0,
                 married=False):
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
        self._married = married
        self._tax_buckets = account_tax_buckets
        self._income_tax_bucket = None
        self._fica_tax_bucket = None

        self.SetExpenses(initial_expense)
        self.SetIncome(initial_income)
        self.SetIncomeGrowthRate(income_growth)
        self.SetExpenseGrowthRate(expense_growth)
        
        for key in accounts:
            self.AddAccount(key, accounts[key])
            
        ##always have a 'standard' account in which leftover expenses can accumulate
        if income_tax_bucket is not None:
            for bucket in income_tax_bucket:
                bucket.taxable_income = initial_income
            self._income_tax_bucket = income_tax_bucket
            self._tax_buckets.extend(income_tax_bucket)
        if fica_tax_bucket is not None:
            fica_tax_bucket.taxable_income = initial_income
            self._fica_tax_bucket = fica_tax_bucket
            self._tax_buckets.append(fica_tax_bucket)
            
        account = fc.IndividualTaxable(initial_standard_value, apr=standard_apr)
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
            self.Contribute('standard', self._income)
            for key in self._accounts:
                if self._retired:
                    self._income = 0
                    if key != 'standard':
                        withdraw = self._accounts[key].Withdraw(self._accounts[key].GetAccountValue()*0.04) #TODO : make 4% withdraw flexible
                        self.Contribute('standard',withdraw)
                else:     
                    if key != 'standard':
                        personal_contribution = self._accounts[key].GetContribution(self._income)
                        #employer_contribution = self._accounts[key].GetEmployerContribution(self._income)
                        self.Withdraw('standard', personal_contribution)
                        self.Contribute(key, personal_contribution, self._income)
                self._accounts[key].Age()

            self.Withdraw('standard', self._expenses)
            self.ApplyTax()
            
    def GetTax(self):
        taxes = 0
        if self._income_tax_bucket is not None:
            for bucket in self._income_tax_bucket:
                bucket.taxable_income = self._income
        if self._fica_tax_bucket is not None:
            self._fica_tax_bucket.taxable_income = self._income

        for tax_bucket in self._tax_buckets:
            taxes += tax_bucket.GetTax() 

        return taxes
    
    def ApplyTax(self):
        taxes = self.GetTax()
        self.Withdraw('standard',taxes)
        return taxes

    def ContributeToAll(self, amount=None, income=None):
        for key in self._accounts:
            self.Contribute(key, amount, income=income)
    
    def WithrdawFromAll(self, amount=None):
        for key in self._accounts:
            self.Withdraw(key, amount)
    
    def WithdrawAll(self):
        result = 0
        for key in self._accounts:
            while(self._accounts[key].GetAccountValue() > 0):
                amount = self._accounts[key].GetAccountValue()
                result += self.Withdraw(key, np.inf)
        tax = self.GetTax()
        self.ApplyTax()
        return result - tax
    
    def Contribute(self, account_key, amount = None, income=None):
        self._accounts[account_key].Contribute(amount, income)
        
    def Withdraw(self, account_key, amount = None, tax=False):
        return self._accounts[account_key].Withdraw(amount, tax=tax)

if __name__ == '__main__':
    roth = fc.Roth(init_value=22000.0,
                 base_contribution=6500.,
                 contribution_rate=0.0,
                 apr=0.05,
                 employer_contribution_rate=0.0,
                 employer_contribution_match=0.0,
                 employer_contribution_cap=np.inf)
    
    saver401k =  fc.Saver401k(init_value_trad = 15000,
                 init_value_roth = 15000,
                 init_afterTax = 0,
                 apr = 0.05,
                 individual_contribution_cap = fc.individual_401k_contribution_limit,
                 total_contribution_cap = fc.total_401k_contribution_limit,
                 employer_contribution_rate = 0.05,
                 employer_contribution_match = 0.0,
                 employer_contribution_cap = fc.total_401k_contribution_limit - fc.individual_401k_contribution_limit)

    accounts = {'roth':roth, '401k':saver401k}

    income_init = 133000
    fc.fed_tax.AddTaxableIncomeSources([saver401k])
    fc.ca_tax.AddTaxableIncomeSources([saver401k])
    fc.fed_tax.AddTaxableIncome(income_init)
    fc.ca_tax.AddTaxableIncome(income_init)
    fc.fed_tax.AddDeductionSources([saver401k])
    fc.ca_tax.AddDeductionSources([saver401k])

    fc.fica_tax.AddTaxableIncome(income_init)

    brackets = [fc.fed_tax, fc.ca_tax, fc.fica_tax]

    person = PersonalFinances(accounts,
                              initial_income=income_init,
                              initial_standard_value=18000,
                              initial_expense=54000,
                              income_tax_bucket=[fc.fed_tax, fc.ca_tax],
                              fica_tax_bucket=fc.fica_tax,
                              age=31,
                              income_growth=.02,
                              expense_growth=.0175,
                              standard_apr=.01)
    
    person.Age(15)
    print(person.GetNetWorth())
    
    print(roth.GetAccountValue(), saver401k.GetAccountValue(), person.GetAccount('standard').GetAccountValue())

    #print(person.WithdrawAll())
    print(person.GetIncome())