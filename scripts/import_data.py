import os
import random
import pandas as pd
import mysql.connector
from faker import Faker

fake = Faker("en_IN")

connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YourPassword",
    database="employee_management_v2"
)

cursor = connection.cursor()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
csv_path = os.path.join(BASE_DIR, "data", "Employee.csv")

df = pd.read_csv(csv_path)

# Salary mapping
salary_map = {
    1: 90000,
    2: 60000,
    3: 35000
}

# Department IDs
department_ids = [1, 2, 3, 4, 5]

# Project IDs
project_ids = [1, 2, 3, 4, 5]

for index, row in df.iterrows():

    employee_code = f"EMP{index+1:05d}"

    name = fake.name()

    email = f"{employee_code.lower()}@company.com"

    phone = fake.msisdn()[:10]

    department_id = random.choice(department_ids)

    cursor.execute(
        """
        INSERT INTO employees
        (
            employee_code,
            name,
            email,
            phone,
            age,
            gender,
            education,
            joining_year,
            city,
            department_id
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            employee_code,
            name,
            email,
            phone,
            int(row["Age"]),
            row["Gender"],
            row["Education"],
            int(row["JoiningYear"]),
            row["City"],
            department_id
        )
    )

    employee_id = cursor.lastrowid

    payment_tier = int(row["PaymentTier"])

    basic_salary = salary_map[payment_tier]

    hra = basic_salary * 0.20

    bonus = basic_salary * 0.10

    deduction = basic_salary * 0.05

    net_salary = basic_salary + hra + bonus - deduction

    cursor.execute(
        """
        INSERT INTO salary
        (
            employee_id,
            payment_tier,
            salary_amount,
            bonus,
            hra,
            deduction,
            net_salary,
            experience,
            ever_benched,
            leave_or_not
        )
        VALUES
        (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            employee_id,
            payment_tier,
            basic_salary,
            bonus,
            hra,
            deduction,
            net_salary,
            int(row["ExperienceInCurrentDomain"]),
            row["EverBenched"],
            int(row["LeaveOrNot"])
        )
    )

    total_projects = random.randint(1, 3)

    assigned_projects = random.sample(project_ids, total_projects)

    for project_id in assigned_projects:

        cursor.execute(
            """
            INSERT INTO employee_project
            (employee_id, project_id)
            VALUES
            (%s,%s)
            """,
            (
                employee_id,
                project_id
            )
        )

connection.commit()

cursor.close()

connection.close()

print("===================================")
print("Employee Data Imported Successfully")
print("===================================")