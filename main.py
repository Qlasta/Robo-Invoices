import requests
import datetime as dt
from flask import Flask, redirect, url_for, request, render_template, flash
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired
from wtforms import SubmitField, DateField
from flask_bootstrap import Bootstrap
from config import SECRET_KEY, SECRET


URL = "https://api.robolabs.lt"
invoice_list_endpoint = "/api/get_invoice_list"
headers = {
    "x-api-key": SECRET
}
# defaults for date selectors
today = dt.datetime.now()
last_month_start = (today - dt.timedelta(days=today.day)).replace(day=1)
last_month_end = today - dt.timedelta(days=today.day)


def generate_query(date_from, date_to):
    """Required starting date and ending date in format YYYY-mm-dd, returns body for the API query."""
    query = {
        "invoice_date_from": f"{date_from} 00:00:00",
        "invoice_date_to": f"{date_to} 00:00:00",
        "execute_immediately": "True"
    }
    return query


app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
Bootstrap(app)


class DateSelector(FlaskForm):
    date_from = DateField(label="Date From", validators=[DataRequired()], format="%Y-%m-%d", default=last_month_start)
    date_to = DateField(label="Date To", validators=[DataRequired()], format="%Y-%m-%d", default=last_month_end)
    submit = SubmitField(label='Submit')


@app.route("/", methods=["GET", "POST"])
def index():
    form = DateSelector()
    if request.method == "POST":
        selected_from = form.date_from.data
        selected_to = form.date_to.data
        if selected_from > selected_to:
            flash('"Date From" is later than "Date To". Please select valid period.')
        else:
            query = generate_query(selected_from, selected_to)
            query_response = requests.post(url=f"{URL}{invoice_list_endpoint}", json=query, headers=headers)
            if query_response.status_code != 200:
                flash("Something went wrong. Try again later.")
            else:
                data = query_response.json()
                if "error" in data:
                    flash(f"{data['error']['message']}")
                else:
                    chosen_invoices = data["result"]["data"]
                    # add year-month field for grouping
                    invoices_group = []
                    for inv in chosen_invoices:
                        date = dt.datetime.strptime(inv["date_invoice"], "%Y-%m-%d")
                        inv["month_invoice"] = date.strftime("%Y-%m")
                        invoices_group.append(inv)
                    invoices_group.sort(key=lambda x: x["date_invoice"])
                    total_inv_count = len(invoices_group)
                    if total_inv_count == 0:
                        flash(f"{data['result']['error']}")
                    return render_template("index.html", form=form, invoices=invoices_group,
                                           inv_count=total_inv_count)
    return render_template("index.html", form=form)


if __name__ == "__main__":
    app.run(debug=True)

