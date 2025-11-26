import random as rand
import time

class User:
    def __init__(self, money, xp, lastBegTime, lastWorkTime, hasJob, itemsOwned):
        self.money = money
        self.xp = xp
        self.lastBegTime = lastBegTime
        self.lastWorkTime = lastWorkTime
        self.hasJob = hasJob
        self.itemsOwned = itemsOwned


testUser = User(10, 0, 0, 0, False, ' ')
testUser.money += 20
print(vars(testUser))
money = 10
xp = 0
lastBegTime = 0
lastWorkTime = 0
hasJob = False
itemsOwned = " "
availJobs = {
    'The very legal pizzeria.',
    'Not selling stolen goods.'
}
shop = {
    'Cardboard trophy - xp: 10+, costs $10',
    'Iron trophy - xp: 250+, costs $300',
    'Diamond trohpy - xp: 1000+, costs $1500'
}

curJob = 'none'

def begAct():
    global money, xp, lastBegTime
    now = time.time()

    if now - lastBegTime < 20:
       remainingTime = int(20 - (now - lastBegTime))
       print(f'Please wait {remainingTime} seconds before trying to beg again.')
       return

    lastBegTime = now
    mGained = rand.randint(5, 80)
    xpGained = rand.randint(5, 15)
    xp += xpGained
    money += mGained
    print(f'You begged and received ${money} and gained {xp} xp.')

def workAct():
    global money, xp, lastWorkTime
    now = time.time()
    

    if now - lastWorkTime < 3600:
       remainingTime = int(3600 - (now - lastWorkTime))
       hourVal = int(remainingTime/60)
       print(f'Please wait {hourVal} minutes before trying to work again.')
       return

    lastWorkTime = now
    mGained = rand.randint(150, 300)
    xpGained = rand.randint(25, 35)
    xp += xpGained
    money += mGained
    print(f'You worked and earned ${money} and gained {xp} xp.')

def checkInventory():
    global money, xp, hasJob, curJob

    print(f'You have ${money}')
    print(f'Your xp is currently at {xp}')
    if hasJob == True:
        print(f'You have a job, you are currently working at "{curJob}".')
    else:
        print(f'You have ${money}')
        print(f'Your xp is currently at {xp}')

def getJob():
    global xp, hasJob, availJobs

    if xp >= 5000 and hasJob == False:
        print(f'Where would you like to work? {availJobs}')
        print('please enter job 1 or job 2.')
    elif xp < 5000 and hasJob == False:
        print(f'You do not have enough xp to get a job, you currently have {xp} xp.')
    else:
        print('You do not meet the requirements to get a new job.')

def claimJob1():
    global xp, hasJob, curJob

    if xp >= 5000 and hasJob == False:
        curJob = 'The very legal pizzeria'
        hasJob = True
        print('You are now working at "The very legal pizzeria!"')
    elif xp < 5000 and hasJob == False:
        print(f'You do not have enough xp to get a job, you currently have {xp} xp.')
    else:
        print('You do not meet the requirements to get a new job.')

def claimJob2():
    global xp, hasJob, curJob

    if xp >= 5000 and hasJob == False:
        curJob = 'Not selling stolen goods'
        hasJob = True
        print('You are now working at "Not selling stolen goods!"')
    elif xp < 5000 and hasJob == False:
        print(f'You do not have enough xp to get a job, you currently have {xp} xp.')
    else:
        print('You do not meet the requirements to get a new job.')

def xpBoost():
    global xp

    xp += 5000

while True:
    action = input('What would you like to do? ')

    if action == 'beg':
        begAct()
    elif action == 'inventory':
        checkInventory()
    elif action == 'job list':
        getJob()
    elif action == 'job 1':
        claimJob1()
    elif action == 'job 2':
        claimJob2()
    elif action == 'xpBoost':
        xpBoost()
    elif action == 'work':
        if hasJob == True:
            workAct()
        else:
            print('You do not have a job, please enter "job list"')
    else:
        print('We have encoutered an error, please try using "inventory", "beg", "job list", "job 1", "job 2", "job list".')