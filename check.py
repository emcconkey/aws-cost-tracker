#!/usr/bin/env python3
import sqlite3
import sys
import datetime
from dateutil.parser import parse

DBFILE = 'costdata.sqlite'


def query_db(query, data):
	db = sqlite3.connect(DBFILE)
	dbc = db.cursor()
	dbc.execute(query, data)
	records = dbc.fetchall()
	return records


def daily_average(start, count):
	end = (parse(start) + datetime.timedelta(days=int(count))).strftime("%Y-%m-%d")
	records = query_db("select * from daily_costs where date>=? and date<? order by date", (start, end))
	total = 0.00
	count = 0
	for r in records:
		total += r[2]
		count += 1
	if count < 1:
		count = 1
	average = total / count
	return average


def alert_average(threshold):
	start = (datetime.date.today() - datetime.timedelta(days=8)).strftime("%Y-%m-%d")
	count = 7
	avg = daily_average(start, count)
	today = get_day_cost(datetime.date.today().strftime("%Y-%m-%d"))
	print("Average: ", avg, " Today: ", today)
	return


def get_day_cost(day):
	records = query_db("select * from daily_costs where date=?", (day,))
	if len(records):
		return records[0][2]
	else:
		return 0.00


def show_average(start, count):
	avg = daily_average(start, count)
	end = (parse(start) + datetime.timedelta(days=int(count))).strftime("%Y-%m-%d")
	out = start + " - " + end + " AWS Daily Average\n"
	out += "====================================================\n"
	out += '{0:40s}: $ {1:8.2f}\n'.format('Average', avg)
	return out


def show_day(day):
	records = query_db("select * from tracking where date=? order by account, product", (day,))
	d = records[0][1]
	out = d + " AWS Costs\n"
	out += "====================================================\n"
	total = 0.00
	account_total = 0.00
	last_account = ""
	for r in records:
		if r[2] != last_account:
			last_account = r[2]
			out += '{0:40s}: $ {1:8.2f}\n'.format('Subtotal', account_total)
			out += '-------------------------------------------\nAccount: {0:s}\n'.format(last_account)
			account_total = 0.00
		total += r[4]
		account_total += r[4]
		out += '{0:40s}: $ {1:8.2f}\n'.format(r[3], r[4])

	out += "----------------------------------------------------\n"
	out += '{0:40s}: $ {1:8.2f}\n'.format('Total', total)
	return out


def show_month(start):
	end = parse(start)
	month = end.month + 1
	end = end.replace(month=month).strftime("%Y-%m-%d")

	records = query_db("select * from daily_costs where date>=? and date<? order by date", (start, end))

	out = start + " - " + end + " AWS Costs\n"

	out += "=================================\n"
	total = 0.00
	for r in records:
		total += r[2]
		out += '{0:20s}: $ {1:8.2f}\n'.format(r[1], r[2])

	out += "-----------------------------------------------------\n"
	out += '{0:20s}: $ {1:8.2f}\n'.format('Total', total)
	return out


def show_mtd_product(start):
	end = parse(start)
	month = end.month + 1
	end = end.replace(month=month).strftime("%Y-%m-%d")

	records = query_db("select *,sum(cost) as sc from tracking where date>=? and date<? group by account, product", (start, end))

	d = records[0][1]
	out = d + "Month to date AWS costs by account\n"
	out += "====================================================\n"
	total = 0.00
	account_total = 0.00
	last_account = ""
	first = True
	for r in records:
		if r[2] != last_account:
			last_account = r[2]
			if not first:
				out += '{0:40s}: $ {1:8.2f}\n'.format('Subtotal', account_total)
				out += '-------------------------------------------\nAccount: {0:s}\n'.format(last_account)
			first = False
			account_total = 0.00
		total += r[5]
		account_total += r[5]
		out += '{0:40s}: $ {1:8.2f}\n'.format(r[3], r[5])

	out += "----------------------------------------------------\n"
	out += '{0:40s}: $ {1:8.2f}\n'.format('Total', total)
	return out


def main(argv):
	if argv[0] == "day":
		if len(argv) > 1:
			print(show_day(parse(argv[1]).strftime('%Y-%m-%d')))
		else:
			print(show_day(datetime.date.today().strftime('%Y-%m-%d')))
		return
	if argv[0] == "month":
		if len(argv) > 1:
			print(show_month(parse(argv[1]).replace(day=1).strftime('%Y-%m-%d')))
		else:
			print(show_month(datetime.date.today().replace(day=1).strftime('%Y-%m-%d')))
		return
	if argv[0] == "mtd":
		if len(argv) > 1:
			print(show_mtd_product(parse(argv[1]).replace(day=1).strftime('%Y-%m-%d')))
		else:
			print(show_mtd_product(datetime.date.today().replace(day=1).strftime('%Y-%m-%d')))
		return
	if argv[0] == "average":
		if len(argv) < 3:
			print(show_average(datetime.date.today().strftime('%Y-%m-%d'), 7))
		else:
			print(show_average(argv[1], argv[2]))
		return
	if argv[0] == "alert":
		if argv[1] == "average":
			alert_average(argv[2])
			return

	print("Unknown command.")
	exit(1)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Unknown command.")
		exit(1)

	main(sys.argv[1:])
	exit(0)