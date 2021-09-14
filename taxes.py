
class Tax(object):
    def __init__(self, brackets_rate = None):
        self._brackets_rate = None
        
        self.SetBrackets(brackets_rate)
    
    def SetBrackets(self, brackets_rate):
        self._brackets_rate = brackets_rate
        
    def GetTax(self, amount=0):
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
