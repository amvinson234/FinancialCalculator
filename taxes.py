import numpy as np

class TaxBucket(object):
    def __init__(self, brackets_rate=None, deduction=0):
        self._brackets_rate = None
        self._deduction = deduction
        self._income_sources = []
        self._taxable_income = 0
        self._deduction_sources = []
        
        self.SetStandardDeduction(deduction)
        self.SetBrackets(brackets_rate)
    
    def SetBrackets(self, brackets_rate):
        self._brackets_rate = brackets_rate
    
    def SetStandardDeduction(self, deduction):
        if deduction is None:
            self._deduction = 0
        else:
            self._deduction = deduction
        
    def GetTax(self, ordinary_income=0, deduction=None):
        if deduction is None:
            deduction = self._deduction
        amount = ordinary_income
        amount -= deduction
        for income_acct in self._income_sources:
            amount += income_acct.taxable_withdrawals
        for deduct_acct in self._deduction_sources:
            amount -= deduct_acct.deductable_contributions

        amount = max(amount, 0)
        tax = 0
        prev_bracket = 0
        for bracket in self._brackets_rate:
            money_in_bracket = min(amount, bracket-prev_bracket)
            amount -= money_in_bracket 
            tax += money_in_bracket * self._brackets_rate[bracket]
            prev_bracket = bracket
        return tax
    
    def GetEffectiveTaxRate(self, amount = None):
        if amount == 0 or amount is None:
            return 0
        tax = self.GetTax(amount)
        return tax / amount
    
    def AddTaxableIncomeSources(self, accounts):
        if not isinstance(accounts, list):
            accounts = [accounts]

        self._income_sources.extend(accounts)

    def AddDeductionSources(self, accounts):
        if not isinstance(accounts, list):
            accounts = [accounts]

        self._deduction_sources.extend(accounts)

#TODO incorporate accoutns in combineTax
class CombineTax(TaxBucket):
    def __init__(self, tax_sequence):
        TaxBucket.__init__(self)
        self._tax_sequence = None
        self.SetTaxSequence(tax_sequence)
        
    def SetTaxSequence(self, tax_sequence):
        self._tax_sequence = tax_sequence
    
    def GetTax(self, amount=0):
        tax_amnt = 0
        for tax in self._tax_sequence:
            tax_amnt += tax.GetTax(amount)
        
        return tax_amnt
    
    def GetEffectiveTaxRate(self, amount=None):
        return self.GetTax(amount) / amount

year = 2023

if year == 2022:
    fed_tax_bracket = {10275:.10, 41775:.12, 89075:.22, 170050:.24, 215950:.32, 539900:.35, np.inf:.37}
    ca_tax_bracket = {10099:.01, 23942:.02, 37788:.04, 52455:.06, 66295:.08, 338639:.093, 406364:.103, 677275:.113, np.inf:.123}
    fed_tax_bracket_married = {2*key: fed_tax_bracket[key] for key in fed_tax_bracket}
    fed_tax_bracket_married.pop(539900*2)
    fed_tax_bracket_married[647850] = .35 #for some reason this bracket doesn't follow doubling pattern...
    ftbm_keys = list(fed_tax_bracket_married.keys())
    ftbm_keys.sort()
    fed_tax_bracket_married = {ftbm_key: fed_tax_bracket_married[ftbm_key] for ftbm_key in ftbm_keys}
    ca_tax_bracket_married = {2*key: ca_tax_bracket[key] for key in ca_tax_bracket}
if year == 2023:
    fed_tax_bracket = {11000:.10, 44725:.12, 95375:.22, 182100:.24, 231250:.32, 578125:.35, np.inf:.37}
    ca_tax_bracket_22 = {10099:.01, 23942:.02, 37788:.04, 52455:.06, 66295:.08, 338639:.093, 406364:.103, 677275:.113, np.inf:.123}
    ca_tax_bracket = {}
    ratio = 11/10.275
    for key in ca_tax_bracket_22.keys():
        ca_tax_bracket[key*ratio] = ca_tax_bracket_22[key]
    fed_tax_bracket_married = {2*key: fed_tax_bracket[key] for key in fed_tax_bracket}
    fed_tax_bracket_married.pop(578125*2)
    fed_tax_bracket_married[693750] = .35 #for some reason this bracket doesn't follow doubling pattern...
    ftbm_keys = list(fed_tax_bracket_married.keys())
    ftbm_keys.sort()
    fed_tax_bracket_married = {ftbm_key: fed_tax_bracket_married[ftbm_key] for ftbm_key in ftbm_keys}
    ca_tax_bracket_married = {2*key: ca_tax_bracket[key] for key in ca_tax_bracket}

fed_tax = TaxBucket(fed_tax_bracket, 12950)
ca_tax = TaxBucket(ca_tax_bracket, 5202)
fed_ca_tax = CombineTax([fed_tax, ca_tax])
fed_tax_married = TaxBucket(fed_tax_bracket_married, 12950*2)
ca_tax_married = TaxBucket(ca_tax_bracket_married, 5202*2)
fed_ca_tax_married = CombineTax([fed_tax_married, ca_tax_married])
fica_tax = TaxBucket({np.inf:0.0765})
fed_ca_fica_tax = CombineTax([fed_tax, ca_tax, fica_tax])
fed_ca_fica_tax_married = CombineTax([fed_tax_married, ca_tax_married, fica_tax])

capital_gains_bracket = {44625:0.0, 492300:.15, np.inf:.2}
capital_gains_bracket_married = {89250:0.0, 553850:.15, np.inf:.2}
capital_gains_tax = TaxBucket(capital_gains_bracket)
capital_gains_tax_married = TaxBucket(capital_gains_bracket_married)

fed_tax_bracket = {10275:.10, 41775:.12, 89075:.22, 170050:.24, 215950:.32, 539900:.35, np.inf:.37}
ca_tax_bracket = {10099:.01, 23942:.02, 37788:.04, 52455:.06, 66295:.08, 338639:.093, 406364:.103, 677275:.113, np.inf:.123}
fed_tax_bracket_married = {2*key: fed_tax_bracket[key] for key in fed_tax_bracket}
fed_tax_bracket_married.pop(539900*2)
fed_tax_bracket_married[647850] = .35 #for some reason this bracket doesn't follow doubling pattern...
ftbm_keys = list(fed_tax_bracket_married.keys())
ftbm_keys.sort()
fed_tax_bracket_married = {ftbm_key: fed_tax_bracket_married[ftbm_key] for ftbm_key in ftbm_keys}
ca_tax_bracket_married = {2*key: ca_tax_bracket[key] for key in ca_tax_bracket}

if year == 2023:
    fed_tax = TaxBucket(fed_tax_bracket, 12950)
    ca_tax = TaxBucket(ca_tax_bracket, 5202)
    fed_ca_tax = CombineTax([fed_tax, ca_tax])
    fed_tax_married = TaxBucket(fed_tax_bracket_married, 12950*2)
    ca_tax_married = TaxBucket(ca_tax_bracket_married, 5202*2)
    fed_ca_tax_married = CombineTax([fed_tax_married, ca_tax_married])
    fica_tax = TaxBucket({np.inf:0.0765})
    fed_ca_fica_tax = CombineTax([fed_tax, ca_tax, fica_tax])
    fed_ca_fica_tax_married = CombineTax([fed_tax_married, ca_tax_married, fica_tax])