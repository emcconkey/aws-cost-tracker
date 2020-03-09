#!/usr/bin/env python3
import fileinput
from io import StringIO
import datetime
from backports.datetime_fromisoformat import MonkeyPatch
import csv
import sqlite3
import boto3

MonkeyPatch.patch_fromisoformat()

AWS_REGION = "us-east-1"
AWS_COST_EXPLORER_SERVICE_KEY = "ce"
COST_EXPLORER_GROUP_BY = [
	{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"},
	{"Type": "DIMENSION", "Key": "SERVICE"}]

DBFILE = 'costdata.sqlite'


def query_db(query):
	db = sqlite3.connect(DBFILE)
	dbc = db.cursor()
	dbc.execute(query)
	records = dbc.fetchall()
	return records


def write_db(query, data):
	db = sqlite3.connect(DBFILE)
	db.execute(query, data)
	db.commit()
	db.close()


def build_tracking_data():
	print("Do this thing")


def pull_daily_data(day):
	cost_explorer = boto3.client(AWS_COST_EXPLORER_SERVICE_KEY, AWS_REGION)
	start = datetime.date.fromisoformat(day) - datetime.timedelta(days=1)
	time_period = {
		"Start": start.strftime('%Y-%m-%d'),
		"End": day}
	token = None
	costlist = []

	# clear out this day's items before adding the new ones
	write_db("DELETE FROM tracking where date='" + start.strftime('%Y-%m-%d') + "'", ())
	write_db("DELETE FROM daily_costs where date='" + start.strftime('%Y-%m-%d') + "'", ())

	while True:
		kwargs = {}
		if token:
			kwargs = {"NextPageToken": token}
		data = cost_explorer.get_cost_and_usage(
			TimePeriod=time_period,
			Granularity="DAILY",
			Metrics=["UnblendedCost"],
			GroupBy=COST_EXPLORER_GROUP_BY, **kwargs)
		costlist += data["ResultsByTime"]
		token = data.get("NextPageToken", None)
		if not token:
			break

	for cost_and_usage_by_time in costlist:
		total_cost = 0
		for cost_group_data in cost_and_usage_by_time["Groups"]:
			cost_group = CostGroup(
				cost_group_data, cost_and_usage_by_time, False)
			total_cost += float(cost_group.amount)
			write_db('INSERT INTO tracking VALUES (?,?,?,?,?)', (None, start.strftime('%Y-%m-%d'), cost_group.account_id, cost_group.service, cost_group.amount))
		write_db('INSERT INTO daily_costs VALUES (?, ?, ?)', (None, start.strftime('%Y-%m-%d'), total_cost))


class CostGroup():
	""" Class that abstracts a cost group. Will allow us to have shorter
	and more simple functions by going to the essence of the concept."""

	def __init__(self, cost_group_data, cost_and_usage_by_time, is_monthly):
		self.account_id = cost_group_data["Keys"][0]
		self.service = cost_group_data["Keys"][1]
		self.time_start = cost_and_usage_by_time["TimePeriod"]["Start"]
		if is_monthly:
			date_parts = self.time_start.split("-")
			self.time_start = "%s/%s" % (date_parts[1], date_parts[0])
		self.amount = cost_group_data["Metrics"]["UnblendedCost"]["Amount"]
		self.unit = cost_group_data["Metrics"]["UnblendedCost"]["Unit"]
		self.estimated = cost_and_usage_by_time["Estimated"]

	def __repr__(self):
		return "%s, %s, %s, %s, %s, %s\n" % (
			self.time_start,
			self.account_id,
			self.service,
			self.amount,
			self.unit,
			self.estimated)


pull_daily_data(datetime.date.today().strftime('%Y-%m-%d'))
