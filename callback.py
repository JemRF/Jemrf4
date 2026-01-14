def inflate(value):
    return value * 1.7

class thing:
  def __init__(this,amount,action):
    this.amount = amount
    this.action = action
    this.return=1

  def perform(this):
    
    return this.action(this.amount)
      
      
john = thing(12,inflate)

print(john.perform())
