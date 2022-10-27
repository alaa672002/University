
# main account function
class Account():
    def __init__(self,balance,name):
       self.name = name
       self.balance = balance
     # deposit money function 
    def deposit(self, amount):
        self.balance+=amount
        self.print_balance()
        return self.balance
    
     #withdrawing money function    
    def withdraw(self, amount):
        pass
    
    # A function to get the account's balances       
    def get_balance(self):
        return self.balance
    # A function to print the balance       
    def print_balance(self):
        print("\n The account balance is %.2f" %self.balance)

# Saving account class      
class Saving(Account):
     def __init__(self,balance,name,interest_rate):
         super().__init__(balance,name)
         self.interest_rate = interest_rate
      #get account type   
     def get_type(self):
         return "Saving"
     
     def withdraw(self, amount):
        if self.balance - amount >= 0:
           self.balance -= amount 
           self.print_balance()
           return True
        else:
            print("You don't have enough balance ")
            self.print_balance()
            return False
         #calculate forecast after a year using the interest rate and balance   
     def forecast(self):
         return self.balance * (1 + self.interest_rate/100)
         
# Current Account class       
class Current(Account):
     def __init__(self,balance,name,overdraft):
         super().__init__(balance, name)         
         self.overdraft = overdraft
     #get account type     
     def get_type(self):
         return "Current"
     def withdraw(self, amount):
        if self.balance + self.overdraft - amount >= 0:
           self.balance -= amount 
           self.print_balance()
           return True
        else:
            print("You don't have enough balance ")
            self.print_balance()
            return False
#User class        
class User:
    def __init__(self, name, password):
        self.name = name
        self.password = password

#Admin class
class AdminUser(User):
    def __init__(self, name, password):
        super().__init__(name, password)
        
    def get_type(self):
        return "admin"
        
 #Customer class       
class Customer(User):
    def __init__(self, name, password, address):
        super().__init__(name, password)
        self.address = address
        self.accounts = []
        # Print all accounts and their balances
    def print_accounts(self):
        for i, account in enumerate(self.accounts):
            account_type = account.get_type()
            print(f"\t{i+1} - {account_type} account: £{account.get_balance()}")
    # to view customer's accounts summary    
    def view_summary(self):
        n_acc= self.get_num_accounts()
        total_balance = self.get_total_balance()
        print(f"total balance : £{total_balance}")
        print(f"total number of accounts: {n_acc}")
        print(f"Your address is : {self.address}")
        #to work out the total numbe of accounts per customer 
    def get_num_accounts(self):
        return len(self.accounts)
    # calculate the total balance of all accounts for each customer
    def get_total_balance(self):
        total_balance = 0
        for account in self.accounts:
            total_balance = account.balance + total_balance
            
        return total_balance
      # to get the total balance  plus the interest rate
    def get_total_forecast_balance(self):
        total_balance = 0
        for account in self.accounts:
            if isinstance(account, Saving):
                total_balance = account.forecast() + total_balance
            else:
                total_balance = account.balance + total_balance
            
        return total_balance
    
        
    def get_type(self):
        return "customer"
        
# Access users data from the Users file        
def parse_users():
    users = {}
    with open("Users.txt", "r") as f:
        lines = f.readlines()
        for line in lines[1:]:
            if line.strip() != "":
                user_type, name, password, address = line.strip().split(",")
                if user_type == "admin":
                    user = AdminUser(name, password)
                elif user_type == "customer":
                    user = Customer(name, password, address)
                else:
                    raise ValueError(f"Unknown user type '{user_type}'")
                
                users[name] = user
            
    return users

#Access users accounts data from the Accounts file
def parse_accounts():
    accounts = []
    with open("Accounts.txt", "r") as f:
        lines = f.readlines()
        for line in lines[1:]:
             if line.strip() != "":
                account_type, balance, overdraft, interest_rate, name = line.strip().split(",")
                if account_type == "Current":
                    account = Current(float(balance), name, float(overdraft))
                elif account_type == "Saving":
                    account = Saving(float(balance), name, float(interest_rate))
                else:
                    raise ValueError(f"Unknown account type '{account_type}'")
                
                accounts.append(account)
            
    return accounts
#save users into csv file
def save_users(users):
    with open("Users.txt", "w") as f:
        lines = [] # lines to save
        lines.append("Type,Name,Password,Address\n") # header
        
        for user in users:
            if isinstance(user,AdminUser):
               address=""
            else:
                 address= user.address
            user_str = f"{user.get_type()},{user.name},{user.password},{address}\n"
            lines.append(user_str)
            
            
            
        f.writelines(lines)
        
#save accounts to csv file
def save_accounts(accounts):
    with open("Accounts.txt", "w") as f:
        lines = [] # lines to save
        lines.append("Type,Balance,Overdraft,interest rate,Name\n") #header
        
        for account in accounts:
            
            interest_rate = ""
            if isinstance(account, Saving):
                interest_rate = account.interest_rate
                overdraft = ""
            elif isinstance(account, Current):
                overdraft = account.overdraft
                interest_rate = ""
                
            account_str = f"{account.get_type()},{account.balance},{overdraft},{interest_rate},{account.name}\n"
            lines.append(account_str)
            
            
        f.writelines(lines)
            
        
# Main Banking System class       
class BankingSystem():
      def __init__(self):
          self.users = None
          self.selected_user = None
          self.selected_account = None
          self.load_data() # load saved data from files
         
      def load_data(self):
          self.users = parse_users()
          accounts = parse_accounts()
          for account in accounts:
              # append account to the corresponding user's accounts
              self.users[account.name].accounts.append(account)
      
      
      def save_data(self):
          save_users(list(self.users.values()))
          accounts = []
          # extract user accounts
          for user in self.users.values():
              if isinstance(user,Customer):
                  accounts.extend(user.accounts)
              
          save_accounts(accounts)
         # Deposit and withdraw menu
      def selected_account_menu(self):
          try:
              print("Please select an option:")
              menu=["1 - Deposit","2 - Withdraw","3 - Go back"]
              self.show_menu(menu)
              option = int(input())
              if option == 1:
                  amount = None
                  while amount is None:
                      amount_str = input("Enter deposit: ")
                      try:
                          amount = float(amount_str)
                      except ValueError:
                          print(f"amount should be a float, not {amount_str}")
                  
                  self.selected_account.deposit(amount)
                  self.save_data()
              elif option == 2:
                    success = False
                    while not success:
                        amount_str = input("Enter withdraw amount : ")
                        try:
                            amount= float(amount_str)
                        except ValueError:
                            print(f"amount should be a float, not {amount_str}")
                            continue
                                           
                        success = self.selected_account.withdraw(amount)
                            
                    self.save_data()
              elif option == 3:
                   return True
              else :
                  print("Invalid option..Try again ")
                  self.selected_account_menu()
          except ValueError:
             print("Option must be an integer...Please try again")
             self.selected_account_menu()
           
          return False
          #Select an account menu
      def view_account_menu(self):
          try:
              while True:
                  print("--Account list--")
                  print("Please select an option:")
                  self.selected_user.print_accounts()
                  option = int(input("Enter a number to select your option: "))
                  
                  acc = self.selected_user.accounts[option - 1]
                  self.selected_account = acc
                  account_str = f"{acc.get_type()} account: £{acc.get_balance()}"
                  print(f"You selected {option} - {account_str}.")
                  self.selected_account_menu()
          except IndexError:
                print("The option you selected does not match an account...Try again ")
                self.view_account_menu()
          except ValueError:
             print("Option must be an integer...Please try again")
             self.view_account_menu()
                
      def print_details(self):
         self.selected_user
          #Customer menu 
      def account_menu(self):
          try:
                print ("\n Please select an option:")
                menu=["1-View Account", "2-View Summary", "3-Quit"]
                self.show_menu(menu)
                option = int(input("Enter a number to select your option: "))
                if option ==1:
                  self.view_account_menu()
                elif option==2:
                  self.selected_user.view_summary()
                elif option==3:
                   print("You exited the system...Bye!")
                   return
                else:
                  print("Inavlid opiton")
                  self.account_menu()
          except ValueError:
             print("Option must be an integer...Please try again")
             self.account_menu()
          
          #admin menu 
      def admin_menu(self):
          try:
             print (" Please select an option: ")
             menu= ["1- Customer Summary","2- Financial Forecast","3- Transfer money","4- Account management"]
             self.show_menu(menu)
             option = int(input ("Enter a number to select your option: "))
             if option == 1:
                 self.display_customer_summary()
             elif option == 2:
                 self.forecast_for_users()
             else :
                 print("opiton is not selectable")
                 self.admin_menu()
             
          except ValueError:
             print("Option must be an integer....Please Try again")
             self.admin_menu()
        
          #to find the user account and append it 
      def get_customers(self):
          customers = []
          for user in self.users.values():
              if isinstance(user, Customer):
                  customers.append(user)
                  
          return customers
          # to print the forecast for customers 
      def forecast_for_users(self):
          for customer in self.get_customers():
              print(f"Name: {customer.name}, number of accounts: {customer.get_num_accounts()}, "
                    f"total money: {customer.get_total_balance()}, forecast: {customer.get_total_forecast_balance():.2f}")
                  
              print()
          
         # to display customers account's summary 
      def display_customer_summary(self):
          for user in self.get_customers():
                print(f"Name: {user.name}, address: {user.address}")
                for account in user.accounts:
                    if isinstance(account, Current):
                        print(f"Type: {account.get_type()}, balance: {account.get_balance()}, overdraft: {account.overdraft}")
                    if isinstance(account, Saving):
                        print(f"Type: {account.get_type()}, balance: {account.get_balance()}, interest_rate: {account.interest_rate}")
                print()
          # to show the items of the menus
      def show_menu(self,menu):
         for item in menu:
            print(item)    
      
      def run_app(self):
          
                print ("Welcome to the banking system, please log in first.")
            
                logged_in = False
                while not logged_in:
                    user_name = input ("\n Please input your username: ")
                    password = input ("\n Please input your password:  ")
                
                    if user_name not in self.users: # check if we have a user with given user_name
                         print(f"Invalid username {user_name}.... Please Try Again")
                         continue
                     
                    self.selected_user = self.users[user_name]
                
                    if password != self.selected_user.password:
                       print(f"Invalid Password {password}.... Please Try Again")
                       continue
                   
                    logged_in = True
                    print(f"You have now logged in , {user_name}")
                   
                if isinstance(self.selected_user, AdminUser):
                    self.admin_menu()
                     
                elif isinstance(self.selected_user, Customer):
                    self.account_menu()
                
         
                
         