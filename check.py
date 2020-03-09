#!/usr/bin/env python3
import sqlite3
import sys
import datetime
from dateutil.parser import parse
import boto3

DBFILE = 'costdata.sqlite'


def query_db(query, data):			#Retrieves data from db based on input query and data(date)
	db = sqlite3.connect(DBFILE)	#Sets up db as connection to the sql database
	dbc = db.cursor()				#Sets up dbc as the cursor to the database to step through
	dbc.execute(query, data)		#Executes query and obtains data specified from db
	records = dbc.fetchall()		#Gets all data in the db for the input date data
	return records					#Returns retrieved data


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


#No errors, can use as reference
def account_daily_average(start, count):
	end = (parse(start) + datetime.timedelta(days=int(count))).strftime("%Y-%m-%d")
	records = query_db("select * from tracking where date>=? and date<? order by account", (start, end))
	index = -1
	last_account = ""
	accounts = []
	for r in records:						#Iterate through all records
		if r[2] != last_account:				#Check if account changed
			index += 1								#Increment index due to changed account number
			last_account = r[2]						#Update last_account to new value
			accounts.append([None] * 3)				#Create new empty entry in accounts
			accounts[index][0] = last_account		#Set new entry's account number
			accounts[index][1] = 0.0				#Change NoneType to float
		accounts[index][1] += r[4]				#Add cost to account
	for x in accounts:						#Step through every account
		x[1] = (x[1] / count)					#Change total cost to average cost
	return accounts


def get_account_day_cost(day, accounts):
	records = query_db("select * from tracking where date=? order by account", (day,))
	last_account = ""
	index = -1
	first = True
	for r in records:
		if r[2] != last_account:					#Check if account changed
			first = True								#Mark that this is the first entry for this account
			index += 1									#Increment the index
			last_account = r[2]							#Update to new account number

		if accounts[index][0] == last_account:		#Check if current index account is the same as current records entry
			if first == True:							#Is this the first time with this account?
				first = False							#Trip first flag
				accounts[index][2] = 0.0				#Set NoneType to float
			accounts[index][2] += r[4]				#Add record's cost to account's cost
		else:
			if int(accounts[index][0]) < int(last_account):		#Check if last_account passed this account number
				index += 1											#Index to next accounts entry
	return accounts


def alert_average(threshold):
	#Need to cast to float as its read in as a string
	threshold = float(threshold)
	#Sets start date to 8 days ago
	start = (datetime.date.today() - datetime.timedelta(days=8)).strftime("%Y-%m-%d")
	yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
	count = 7
	#Call daily_average with the starting date 8 days ago and the count of 7 days it will go through
	avg = daily_average(start, count)
	#Get the cost of today
	yesterday_cost = get_day_cost(yesterday)

	avg = round(avg, 2)
	yesterday_cost = round(yesterday_cost, 2)

	#Calculate the percent change between the past week avg and yesterday_cost
	if abs(avg) > 0.00:
		percent_change = ((yesterday_cost / avg) - 1) * 100
	else:
		percent_change = 0.00
	#||If acceptable threshold will be printed move the avg/yesterday print line up here||
	#Check if the change is within the threshold
	if percent_change < threshold:
		# print('{0:20s}: {1:8.0f}%\n'.format('Acceptable Threshold', percent_change))
		pass
	else:
		#Print the past weeks average and yesterdays costs
		print('=======Daily Average Alert=======\n')
		print('{0:20s}: $ {1:8.2f}\n{2:20s}: $ {3:8.2f}'.format('Average', avg, 'Yesterday', yesterday_cost))
		print('{0:20s}: {1:8.0f}%\n'.format('Percent Change', percent_change))
		print('=================================\n')
	
	account_alert_average(threshold)
	return


def account_alert_average(threshold):
	threshold = float(threshold)
	start = (datetime.date.today() - datetime.timedelta(days=8)).strftime("%Y-%m-%d") 
	yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
	count = 7
	#Set up empty list to hold the account info
	accounts = []
	#[]:Index of accounts
	#[][]:0:Account ID, 1:Total->Avg Cost over past week, 2:Yesterday's cost
	accounts = account_daily_average(start,count)
	accounts = get_account_day_cost(yesterday, accounts)

	print('==========Account Alerts==========\n')
	for x in accounts:
		if x[2] != None:					#Doesn't have a cost for yesterday, pass on print
			average_cost = round(x[1], 2)
			yesterday_cost = round(x[2], 2)
			#Check if the change in costs is a significant value to report
			if abs(average_cost) > 0.00 and abs(average_cost - yesterday_cost) > 10.0:
				percent_change = (((yesterday_cost/average_cost) - 1) * 100)
			else:
				percent_change = 0
			#||Change the alert tree prints if this branch will be used||
			if abs(percent_change) < threshold:
				# print('Account: {0:12s}'.format(x[0]))
				# print('{0:20s}: {1:f}\n{2:20s}: {3:f}'.format('Average',average_cost, 'Yesterday',yesterday_cost))
				# print('{0:20s}: {1:8.0f}%\n'.format('Acceptable Threshold', percent_change))
				pass
			else:
				print('Account: {0:20s}'.format(x[0]))
				print('{0:20s}: ${1:8.2f}\n{2:20s}: ${3:8.2f}'.format('Average',average_cost, 'Yesterday',yesterday_cost))
				print('{0:20s}:  {1:8.0f}%\n'.format('Percent Change', percent_change))
	print('==================================')
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


def show_day(day):					#Prints costs of a given day by account
	#Stores given dates data in records
	#Retrieves records based on date, ordered by account number and product, ||Find out what (day,) does||
	records = query_db("select * from tracking where date=? order by account, product", (day,))
	d = records[0][1]				#Sets d to the date from daily_costs table
	out = d + " AWS Costs\n"		#Sets out to the date followed by AWS Costs
	out += "====================================================\n"	#Adds a line spacer to out
	total = 0.00
	account_total = 0.00
	last_account = ""
	first = True
	#r is used to hold tracking table
	for r in records:				#
		if r[2] != last_account:	
			last_account = r[2]		#Use last_account to ensure the account number isn't printed multiple times
			#||Read through and try to figure out how this line works||
			#account_name = boto3.client('organizations').describe_account(AccountId=last_account).get('Account').get('Name')
			account_name = last_account	#||Used to patch my ability to actually run this program I think||
			#Checks if this is the first account listed, if it isn't add subtotal to previous account statement
			if not first:				
				out += '{0:40s}: $ {1:8.2f}\n'.format('Subtotal', account_total)
			#Adds initial spacer line and the account number
			out += '-------------------------------------------\nAccount: {0:s}\n'.format(account_name)
			first = False			#Trip first account flag
			account_total = 0.00	#Reset account total for the new account
		#Increase total and account_total by cost in current entry
		total += r[4]
		account_total += r[4]
		#Only add entry to out if total is >0
		if r[4] > 0:
			#Add a line with the product and it's associated cost
			out += '{0:40s}: $ {1:8.2f}\n'.format(r[3], r[4])

	#Prints the final accounts subtotal line followed by the day's total cost
	out += '{0:40s}: $ {1:8.2f}\n'.format('Subtotal', account_total)
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


def show_mtd_detail(start):
	end = parse(start)
	month = end.month + 1
	end = end.replace(month=month).strftime("%Y-%m-%d")

	records = query_db("select *,sum(cost) as sc from tracking where date>=? and date<? group by account, product", (start, end))

	d = records[0][1]
	out = "Month to date AWS costs by account\n"
	out += "====================================================\n"
	total = 0.00
	account_total = 0.00
	last_account = ""
	account_name = ""
	first = True
	for r in records:
		if r[2] != last_account:
			if not first:
				out += '{0:40s}: $ {1:8.2f}\n'.format(account_name, account_total)
			first = False
			account_total = 0.00
			last_account = r[2]
			#account_name = boto3.client('organizations').describe_account(AccountId=last_account).get('Account').get(	'Name')
			account_name = last_account
			out += '-------------------------------------------\nAccount: {0:s}\n'.format(account_name)
		total += r[5]
		account_total += r[5]
		out += '{0:40s}: $ {1:8.2f}\n'.format(r[3], r[5])

	out += "----------------------------------------------------\n"
	out += '{0:40s}: $ {1:8.2f}\n'.format('Total', total)
	return out


def show_mtd_product(start):
	end = parse(start)
	month = end.month + 1
	end = end.replace(month=month).strftime("%Y-%m-%d")

	records = query_db("select *,sum(cost) as sc from tracking where date>=? and date<? group by account, product", (start, end))

	d = records[0][1]
	out = "Month to date AWS costs by account\n"
	out += "====================================================\n"
	total = 0.00
	account_total = 0.00
	last_account = ""
	account_name = ""
	first = True
	for r in records:
		if r[2] != last_account:
			if not first:
				out += '{0:40s}: $ {1:8.2f}\n'.format(account_name, account_total)
			first = False
			account_total = 0.00
			last_account = r[2]
			#account_name = boto3.client('organizations').describe_account(AccountId=last_account).get('Account').get('Name')
			account_name = last_account
			#out += '-------------------------------------------\nAccount: {0:s}\n'.format(account_name)
		total += r[5]
		account_total += r[5]
		#out += '{0:40s}: $ {1:8.2f}\n'.format(r[3], r[5])

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
	if argv[0] == "mdetail":
		if len(argv) > 1:
			print(show_mtd_detail(parse(argv[1]).replace(day=1).strftime('%Y-%m-%d')))
		else:
			print(show_mtd_detail(datetime.date.today().replace(day=1).strftime('%Y-%m-%d')))
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
	if argv[0] == "alert":
		if argv[1] == "acnt_average":
			account_alert_average(argv[2])
			return

	print("Unknown command.")
	exit(1)


if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Unknown command.")
		exit(1)

	main(sys.argv[1:])
	exit(0)