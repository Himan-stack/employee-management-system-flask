from flask import flash

from flask import Flask, render_template, request, redirect, url_for, session
import re
import random
from database import get_connection
from flask import make_response
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import csv
import io

app = Flask(__name__)
app.secret_key = "employee_management_secret_key"

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'

SALARY_MAP = {
    1: 90000,
    2: 60000,
    3: 35000
}


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":
            session["admin"] = username
            return redirect(url_for("dashboard"))

        else:
            return render_template(
                "login.html",
                error="Invalid Username or Password"
            )

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Dashboard Cards
    cursor.execute("SELECT COUNT(*) total FROM employees")
    employees = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) total FROM departments")
    departments = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) total FROM projects")
    projects = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) total FROM salary")
    salary = cursor.fetchone()["total"]

    cursor.execute("SELECT MAX(net_salary) highest FROM salary")
    highest_salary = cursor.fetchone()["highest"]

    cursor.execute("SELECT MIN(net_salary) lowest FROM salary")
    lowest_salary = cursor.fetchone()["lowest"]

    cursor.execute("SELECT ROUND(AVG(net_salary),2) average FROM salary")
    average_salary = cursor.fetchone()["average"]

    # Employees per Department
    cursor.execute("""
        SELECT
            d.department_name,
            COUNT(e.employee_id) total
        FROM departments d
        LEFT JOIN employees e
        ON d.department_id = e.department_id
        GROUP BY d.department_name
        ORDER BY d.department_name
    """)
    

    chart_data = cursor.fetchall()

    labels = [row["department_name"] for row in chart_data]
    values = [row["total"] for row in chart_data]
    
    cursor.execute("""
    SELECT
    employee_code,
    name,
    email
    FROM employees
    ORDER BY employee_id DESC
    LIMIT 5
    """)

    recent_employees = cursor.fetchall()

    cursor.close()
    conn.close()
    return render_template(
        "dashboard.html",
        employees=employees,
        departments=departments,
        projects=projects,
        salary=salary,
        highest_salary=highest_salary,
        lowest_salary=lowest_salary,
        average_salary=average_salary,
        labels=labels,
        values=values,
        recent_employees=recent_employees
    )


@app.route("/add_employee", methods=["GET", "POST"])
def add_employee():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Load Departments
    cursor.execute("SELECT * FROM departments ORDER BY department_name")
    departments = cursor.fetchall()

    # Load Projects
    cursor.execute("SELECT * FROM projects ORDER BY project_name")
    projects = cursor.fetchall()

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        age = int(request.form["age"])
        gender = request.form["gender"]
        education = request.form["education"]
        city = request.form["city"]
        address = request.form["address"]
        department_id = int(request.form["department"])
        payment_tier = int(request.form["payment_tier"])

        selected_projects = request.form.getlist("projects")

        if not re.match(EMAIL_REGEX, email):
            return render_template(
                "add_employee.html",
                error="Invalid Email Address",
                departments=departments,
                projects=projects
            )

        employee_code = f"EMP{random.randint(100000,999999)}"

        try:

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
                    address,
                    department_id
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,YEAR(CURDATE()),%s,%s,%s)
                """,
                (
                    employee_code,
                    name,
                    email,
                    phone,
                    age,
                    gender,
                    education,
                    city,
                    address,
                    department_id
                )
            )

            employee_id = cursor.lastrowid

            basic_salary = SALARY_MAP[payment_tier]

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
                    experience,
                    ever_benched,
                    leave_or_not,
                    bonus,
                    hra,
                    deduction,
                    net_salary
                )
                VALUES
                (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    employee_id,
                    payment_tier,
                    basic_salary,
                    0,
                    "No",
                    0,
                    bonus,
                    hra,
                    deduction,
                    net_salary
                )
            )

            for project in selected_projects:

                cursor.execute(
                    """
                    INSERT INTO employee_project
                    (employee_id,project_id)
                    VALUES
                    (%s,%s)
                    """,
                    (
                        employee_id,
                        int(project)
                    )
                )

            conn.commit()
            flash("Employee added successfully!", "success")
            return redirect(url_for("employees"))

        except Exception as e:

            conn.rollback()

            return render_template(
                "add_employee.html",
                error=str(e),
                departments=departments,
                projects=projects
            )

    return render_template(
        "add_employee.html",
        departments=departments,
        projects=projects
    )

@app.route("/employees")
def employees():

    if "admin" not in session:
        return redirect(url_for("login"))

    page = request.args.get("page", 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    search = request.args.get("search", "").strip()

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        query = """
        SELECT
            e.employee_id,
            e.employee_code,
            e.name,
            e.email,
            e.phone,
            e.gender,
            e.education,
            d.department_name,
            s.salary_amount,
            s.net_salary

        FROM employees e

        JOIN departments d
            ON e.department_id=d.department_id

        JOIN salary s
            ON e.employee_id=s.employee_id

        WHERE
            e.name LIKE %s
            OR e.email LIKE %s
            OR e.employee_code LIKE %s

        ORDER BY e.employee_id DESC

        LIMIT %s OFFSET %s
        """

        values = (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%",
            per_page,
            offset
        )

        cursor.execute(query, values)

        employees = cursor.fetchall()

        cursor.execute("""
        SELECT COUNT(*) total
        FROM employees
        WHERE
            name LIKE %s
            OR email LIKE %s
            OR employee_code LIKE %s
        """,
        (
            f"%{search}%",
            f"%{search}%",
            f"%{search}%"
        ))

    else:

        query = """
        SELECT
            e.employee_id,
            e.employee_code,
            e.name,
            e.email,
            e.phone,
            e.gender,
            e.education,
            d.department_name,
            s.salary_amount,
            s.net_salary

        FROM employees e

        JOIN departments d
            ON e.department_id=d.department_id

        JOIN salary s
            ON e.employee_id=s.employee_id

        ORDER BY e.employee_id DESC

        LIMIT %s OFFSET %s
        """

        cursor.execute(query, (per_page, offset))

        employees = cursor.fetchall()

        cursor.execute("SELECT COUNT(*) total FROM employees")

    total = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    total_pages = (total + per_page - 1) // per_page

    return render_template(
        "employees.html",
        employees=employees,
        search=search,
        page=page,
        total_pages=total_pages
    )


@app.route("/edit_employee/<int:id>", methods=["GET", "POST"])
def edit_employee(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Load dropdown data
    cursor.execute("SELECT * FROM departments ORDER BY department_name")
    departments = cursor.fetchall()

    cursor.execute("SELECT * FROM projects ORDER BY project_name")
    projects = cursor.fetchall()

    if request.method == "POST":

        name = request.form["name"].strip()
        email = request.form["email"].strip()
        phone = request.form["phone"].strip()
        age = int(request.form["age"])
        gender = request.form["gender"]
        education = request.form["education"]
        city = request.form["city"]
        address = request.form["address"]
        department_id = int(request.form["department"])
        payment_tier = int(request.form["payment_tier"])

        if not re.match(EMAIL_REGEX, email):
            return "Invalid Email"

        basic_salary = SALARY_MAP[payment_tier]

        hra = basic_salary * 0.20
        bonus = basic_salary * 0.10
        deduction = basic_salary * 0.05
        net_salary = basic_salary + hra + bonus - deduction

        try:

            cursor.execute("""
                UPDATE employees
                SET
                    name=%s,
                    email=%s,
                    phone=%s,
                    age=%s,
                    gender=%s,
                    education=%s,
                    city=%s,
                    address=%s,
                    department_id=%s
                WHERE employee_id=%s
            """,
            (
                name,
                email,
                phone,
                age,
                gender,
                education,
                city,
                address,
                department_id,
                id
            ))

            cursor.execute("""
                UPDATE salary
                SET
                    payment_tier=%s,
                    salary_amount=%s,
                    bonus=%s,
                    hra=%s,
                    deduction=%s,
                    net_salary=%s
                WHERE employee_id=%s
            """,
            (
                payment_tier,
                basic_salary,
                bonus,
                hra,
                deduction,
                net_salary,
                id
            ))

            # Remove old project assignments
            cursor.execute(
                "DELETE FROM employee_project WHERE employee_id=%s",
                (id,)
            )

            # Insert new project assignments
            selected_projects = request.form.getlist("projects")

            for project in selected_projects:

                cursor.execute(
                    """
                    INSERT INTO employee_project
                    (employee_id, project_id)
                    VALUES (%s,%s)
                    """,
                    (
                        id,
                        int(project)
                    )
                )

            conn.commit()
            flash("Employee updated successfully!", "success")
            return redirect(url_for("employees"))

        except Exception as e:

            conn.rollback()

            return str(e)

    # Load employee details

    cursor.execute("""
        SELECT
            e.*,
            s.payment_tier
        FROM employees e
        JOIN salary s
            ON e.employee_id=s.employee_id
        WHERE e.employee_id=%s
    """, (id,))

    employee = cursor.fetchone()

    cursor.execute("""
        SELECT project_id
        FROM employee_project
        WHERE employee_id=%s
    """, (id,))

    employee_projects = [
        x["project_id"]
        for x in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return render_template(
        "edit_employee.html",
        employee=employee,
        departments=departments,
        projects=projects,
        employee_projects=employee_projects
    )


@app.route("/delete_employee/<int:id>")
def delete_employee(id):

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            "DELETE FROM employee_project WHERE employee_id=%s",
            (id,)
        )

        cursor.execute(
            "DELETE FROM salary WHERE employee_id=%s",
            (id,)
        )

        cursor.execute(
            "DELETE FROM employees WHERE employee_id=%s",
            (id,)
        )

        conn.commit()
        flash("Employee deleted successfully!", "success")
    except Exception as e:

        conn.rollback()

        return str(e)

    finally:

        cursor.close()
        conn.close()

    return redirect(url_for("employees"))

@app.route("/download_pdf")
def download_pdf():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.employee_code,
            e.name,
            e.email,
            d.department_name,
            s.salary_amount,
            s.net_salary
        FROM employees e
        JOIN departments d
            ON e.department_id=d.department_id
        JOIN salary s
            ON e.employee_id=s.employee_id
        ORDER BY e.employee_id
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    pdf = SimpleDocTemplate("employees.pdf")

    data = [
        [
            "Code",
            "Name",
            "Email",
            "Department",
            "Salary",
            "Net Salary"
        ]
    ]

    for row in rows:
        data.append(list(row))

    table = Table(data)

    table.setStyle(TableStyle([

        ("BACKGROUND",(0,0),(-1,0),colors.darkblue),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),

        ("GRID",(0,0),(-1,-1),1,colors.black),

        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),

        ("BACKGROUND",(0,1),(-1,-1),colors.beige),

        ("BOTTOMPADDING",(0,0),(-1,0),10),

    ]))

    pdf.build([table])

    with open("employees.pdf","rb") as f:
        pdf_data = f.read()

    response = make_response(pdf_data)

    response.headers["Content-Type"] = "application/pdf"

    response.headers["Content-Disposition"] = \
        "attachment; filename=Employees_Report.pdf"

    return response

@app.route("/download_csv")
def download_csv():

    if "admin" not in session:
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            e.employee_code,
            e.name,
            e.email,
            d.department_name,
            s.salary_amount,
            s.net_salary

        FROM employees e

        JOIN departments d
            ON e.department_id=d.department_id

        JOIN salary s
            ON e.employee_id=s.employee_id

        ORDER BY e.employee_id
    """)

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    output=io.StringIO()

    writer = csv.writer(output)

    writer.writerow([
        "Employee Code",
        "Name",
        "Email",
        "Department",
        "Salary",
        "Net Salary"
    ])
    writer.writerows(rows)

    response = make_response(output.getvalue())

    response.headers["Content-Disposition"] = \
        "attachment; filename=Employees_Report.csv"

    response.headers["Content-Type"] = "text/csv"

    flash("Report generated successfully!", "success")

    return response


@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)