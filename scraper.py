#!/usr/bin/env python
#
#   about   send command(s) to multiple servers using pxssh
#   author  pyratebeard <root@pyratebeard.net>
#   code    http://code.pyratebeard.net/scraper
#

import os
import sys
import argparse
import logging
from getpass import getpass
from datetime import datetime, timedelta
import socket
import pxssh

# set global variables
user_home = os.path.expanduser("~")
user = ""
passwd = ""
session_token = os.path.join(user_home, ".scraper.token")

# set available arguments for script
def getArgs():
	global args
	parser = argparse.ArgumentParser(description='send command(s) to multiple servers using pxssh')
	parser.add_argument('-i', '--input', required=True, action='store', help='List of hostnames')
	parser.add_argument('-o', '--output', required=False, action='store', help='Output file')
	parser.add_argument('-c', '--command', required=False, action='store', help='Command list file')
	args = parser.parse_args()
	return args

# configure log file format
def logConf():
	global scraper_log
	log_name = args.output
	scraper_log = os.path.join(user_home, log_name)

	logging.basicConfig(format="%(asctime)s %(levelname)s : %(message)s",datefmt="%H:%M:%S",filename=scraper_log,filemode="a",level=logging.INFO)

# write log to file or stdout depending on output arg
def writeLog(msg, state):
	if not args.output:
		msg = state + " " + msg
		print(msg)
	else:
		if state == "INFO":
			logging.info(msg)
		if state == "WARN":
			logging.warning(msg)

# if there is no token, or it has expired, we create one
def createToken():
	user = raw_input("Username: ")
	passwd = getpass("Password: ")
	with open(session_token, "a") as token:
		token.write("%s\n%s" %(user, passwd))

	return user, passwd

# if there is a token that is less than 10 mins old we load the creds
# over 10 mins, or no token, we create a new one
def checkToken():
	now = datetime.now().strftime("%s")
	expiry = (datetime.now() - timedelta(minutes = 10)).strftime("%s")
	if os.path.isfile(session_token):
		token_mtime = datetime.fromtimestamp(os.path.getmtime(session_token)).strftime("%s")
		if token_mtime <= expiry:
			os.remove(session_token)
			print("Cached credentials have expired")
			user, passwd = createToken()
		else:
			print("Using cached credentials")
			lines = [line.strip() for line in open(session_token)]
			user = lines[0]
			passwd = lines[1]
	else:
		print("No cached credentials")
		user, passwd = createToken()

	return user, passwd

# pass the command(s) to the prompt
def sendCommand(s, command):
	s.sendline(command)
	s.prompt()
	writeLog(s.before, "INFO")
	s.logout()
	s.close()

# if the hostname resolves we try to login
# if not successful output error - 
## this needs to be improved to give greater detail
def login(server, user, passwd):
	s = pxssh.pxssh()
	try:
		if s.login(server, user, passwd):
			msg = "%s - login successful" % server
			writeLog(msg, "INFO")
			if not args.command:
				sendCommand(s, command)
			else:
				commands = [line.strip() for line in open(args.command)]
				for i in range(len(commands)):
					sendCommand(s, commands[i])
		else:
			msg = "%s - login unsuccessful" % server
			writeLog(msg, "WARN")
	except pxssh.ExceptionPxssh as e:
		msg = "%s - login unsuccessful - %s" %(server, str(e))
		writeLog(msg, "WARN")
	except Exception as e:
		msg = "%s - login unsuccessful - %s" %(server, str(e))
		writeLog(msg, "WARN")

# lets do this
def main():

	getArgs()

	if args.output is not None:
		logConf()

	writeLog("===== STARTING =====", "INFO")

	user, passwd = checkToken()

	# if no command file, enter single command
	if not args.command:
		global command
		command = raw_input("Command: ")

	servers = [server.strip() for server in open(args.input)]

	# for stdout if an output file is used
	global total_num
	total_num = len(servers)
	num = 0

	for server in servers:
		try:
			num = num + 1
			# this can be improved to clear the whole line...
			sys.stdout.write("[%s/%s] %s\t\t\r" %(num, total_num, server))
			sys.stdout.flush()
			# ensure the hostname exists before attempting to log on
			socket.getaddrinfo(server,0,0,0,0)
			msg = "Hostname %s did resolve" % server
			writeLog(msg, "INFO")

			login(server, user, passwd)

		except socket.gaierror:
			msg = "Hostname %s did not resolve" % server
			writeLog(msg, "WARN")

	writeLog("===== FINISHED =====", "INFO")
	sys.stdout.flush()
	print("\nFinished\r")

if __name__ == "__main__":
	try:
		main()
	except (Exception, RuntimeError, NameError, TypeError) as e:
		print(str(e))
		os._exit(1)
	except KeyboardInterrupt:
		print("\nExited by user")
		os._exit(1)
