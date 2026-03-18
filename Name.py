import random
import csv

f_names = [
"Karen","Jake","Michael","Tianna","Daniel","Olivia","Nathan","Isabella","Joshua","Chloe",
"Matthew","Sophia","David","Emily","Andrew","Hannah","Ryan","Megan","Brandon","Zoe",
"Justin","Ava","Caleb","Leah","Jordan","Kayla","Dylan","Jasmine","Tyler","Brianna",
"Aaron","Natalie","Lucas","Sarah","Ethan","Grace","Noah","Victoria","Liam","Alyssa",
"Elijah","Madison","Logan","Samantha","Mason","Alexis","Cameron","Paige","Connor","Vanessa"
]

l_names = [
"Brown","Smith","Johnson","Williams","Jones","Miller","Davis","Wilson","Taylor","Anderson",
"Thomas","Jackson","White","Harris","Martin","Thompson","Garcia","Martinez","Robinson","Clark",
"Rodriguez","Lewis","Lee","Walker","Hall","Allen","Young","Hernandez","King","Wright",
"Lopez","Hill","Scott","Green","Adams","Baker","Nelson","Carter","Mitchell","Perez",
"Roberts","Turner","Phillips","Campbell","Parker","Evans","Edwards","Collins","Stewart","Morris"
]

n_counts = {}
e_counts = {}
used_ids = set()

def generate_unique_id(prefix):
    while True:
        number = prefix + str(random.randint(0, 999999)).zfill(6)
        if number not in used_ids:
            used_ids.add(number)
            return number

def generate_name():
    while True:
        first = random.choice(f_names)
        last = random.choice(l_names)
        key = (first, last)

        if key not in n_counts:
            n_counts[key] = 1
            return first, last
        elif n_counts[key] == 1:
            n_counts[key] += 1
            return first, last
        # if already used twice try again

def generate_email(first, last):
    base = f"{first.lower()}.{last.lower()}"
    
    if base not in e_counts:
        e_counts[base] = 1
        return f"{base}@mymona.uwi.edu"
    else:
        e_counts[base] += 1
        return f"{base}02@mymona.uwi.edu"

users = []

# generate students
for _ in range(100):
    first, last = generate_name()
    email = generate_email(first, last)
    uid = generate_unique_id("620")
    users.append(["Student", uid, first, last, email])

# generate staff
for _ in range(20):
    first, last = generate_name()
    email = generate_email(first, last)
    uid = generate_unique_id("451")
    users.append(["Staff", uid, first, last, email])

with open("Users.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Role","ID","First Name","Last Name","Email"])
    writer.writerows(users)

print("Database generated: Users.csv")