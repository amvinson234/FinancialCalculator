import numpy as np

class Tax(object):
    def __init__(self, brackets_rate=None, deduction=None):
        self._brackets_rate = None
        self._deduction = None
        
        self.SetStandardDeduction(deduction)
        self.SetBrackets(brackets_rate)
    
    def SetBrackets(self, brackets_rate):
        self._brackets_rate = brackets_rate
    
    def SetStandardDeduction(self, deduction):
        if deduction is None:
            self._deduction = 0
        else:
            self._deduction = deduction
        
    def GetTax(self, amount=0, deduction=None):
        if deduction is None:
            deduction = self._deduction
            
        amount -= deduction
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
    
class CombineTax(Tax):
    def __init__(self, tax_sequence):
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

fed_tax_bracket = {9950:.10, 40525:.12, 86375:.22, 164925:.24, 209425:.32, 523600:.35, np.inf:.37}
ca_tax_bracket = {8809:.01, 20883:.02, 32960:.04, 45753:.06, 57824:.08, 295373:.093, 354445:.103, 590742:.113, 1000000:.123, np.inf:.133}

fed_tax = Tax(fed_tax_bracket, 12550)
ca_tax = Tax(ca_tax_bracket, 4601)
fed_ca_tax = CombineTax([fed_tax, ca_tax])
fica_tax = Tax({np.inf:0.0765})
fed_ca_fica_tax = CombineTax([fed_tax, ca_tax, fica_tax])
