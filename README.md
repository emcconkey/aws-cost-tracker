# aws-cost-tracker
Loads AWS cost data from the Cost Explorer API into a sqlite db for simple reporting/monitoring

## load.py
This pulls in all the costs for the previous day and inserts them into the database.
The data is loaded into two tables; daily_costs and tracking. The daily_costs table
simply keeps a daily tally of costs. The tracking table keeps a list of aggregate charges per
day and account, grouped by AWS product.


### daily_costs table code:

    CREATE TABLE daily_costs(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        cost REAL
                      )

### Cost anomaly detection

The daily_costs table keeps track of the daily cost and can alert when the daily average changes.
Running checks with check.py will allow you to find when the daily average has increased/decreased
a certain amount.


### Tracking table code

    CREATE TABLE tracking(
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT,
                        account TEXT,
                        product TEXT,
                        cost REAL
                      )

### Instructions

1. Set up your AWS CLI command according to: https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html
2. Run initdb.py to initialize the sqlite database
5. Modify load.py and check.py to set DBFILE to the location of your desired sqlite file
6. Create a daily cron job that runs load.py

Once these are done, you will have a sqlite db that you can run queries against
to track your daily usage.

### Commands
* initdb.py - initializes the database
* check.py
  * check.py day - shows today's cost
  * check.py day <YYYY-MM-DD> - shows cost for that day
  * check.py month - shows moth-to-date cost
  * check.py month <YYYY-MM-DD> - shows cost for the month that date appears in
  * check.py mtd - shows month-to-date cost broken by account
  * check.py mtd <YYYY-MM-DD> - shows month-to-date cost broken by account for the month that date appears in
  