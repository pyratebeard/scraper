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
import traceback

# set global variables
userHome = os.path.expanduser("~")
user = ""
passwd = ""
sessionToken = os.path.join(userHome, ".scraper.token")

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
	global scraperLog
	logName = args.output
	scraperLog = os.path.join(userHome, logName)

	logging.basicConfig(format="%(asctime)s %(levelname)s : %(message)s",datefmt="%H:%M:%S",filename=scraperLog,filemode="a",level=logging.INFO)

# lets do this
def main():

	getArgs()

	# get creds
	user = raw_input('Username: ')
	passwd = getpass.getpass('Password: ')

	# if no command file, get command
	if not args.command:
		command = raw_input('Command: ')

	global system # for use in exception
	servers = [line.strip() for system in open(args.input)]

	# set up counter for terminal output
	total_num = len(servers)
	num = 0

	for system in servers:
		s = pxssh.pxssh()
		try:
			# check if the system is online
			socket.getaddrinfo(system,0,0,0,0)
			try:
				s.login(system, user, passwd)
				if not args.output: # if no output file print to terminal
					print '%s - ssh session login successful' % system
					if not args.command: # if no command file, use command from input
						s.sendline(command)
						s.prompt()
						print s.before
						s.logout
						s.close
					else:
						# read the commands in file
						commands = [line.strip() for line in open(args.command)]
						for c in range(len(commands)): # issue commands line by line
							s.sendline(commands[i])
							s.prompt()
							print s.before
							s.logout
							s.close
				else:
					# output the counter
					num = num +1
					sys.stdout.write('[%s/%s] %s \r' % \
										(num, total_num, system))
					sys.stdout.flush()
					f = open(args.output, 'a')
					log = '%s - ssh session login successful\n' % system
					f.write(log)
					f.close
					if not args.command: # if no command file, use command from input
						s.sendline(command)
						s.prompt()
						log = '%s\n' % s.before
						f.write(log)
						f.close
						s.logout
						s.close
					else:
						# read the commands in file
						commands = [line.strip() for line in open(args.command)]
						for c in range(len(commands)): # issue commands line by line
							s.sendline(commands[i])
							s.prompt()
							log = '%s\n' % s.before
							f.write(log)
							f.close
							s.logout
							s.close
			except Exception, e:
				if 'password refused' in e:
					if not args.output:
						print '%s - password refused' % system
						print str(s)
					else:
						num = num +1
						sys.stdout.write('[%s/%s] %s \r' % \
										(num, total_num, system))
						sys.stdout.flush()
						f = open(args.output, 'a')
						log = '%s - password refused\n' % system
						f.write(log)
						f.close
					continue
				else:
					if not args.output:
						print '%s - another issue' % system
						print str(s)
					else:
						num = num +1
						sys.stdout.write('[%s/%s] %s \r' % \
										(num, total_num, system))
						sys.stdout.flush()
						f = open(args.output, 'a')
						log = '%s - another issue\n' % system
						f.write(log)
						f.close
					continue
		except socket.gaierror:
			if not args.output:
				print '%s - hostname did not resolve' % system
				print str(s)
			else:
				num = num +1
				sys.stdout.write('[%s/%s] %s \r' % \
								(num, total_num, system))
				sys.stdout.flush()
				f = open(args.output, 'a')
				log = '%s - hostname did not resolve\n' % system
				f.write(log)
				f.close
			continue

if __name__ == "__main__":
	try:
		main()
	except Exception, e:
		print str(e)
		traceback.print_exc()
		print 'Hostname = %s' % system
		os._exit(1)
	except KeyboardInterrupt:
		print
		print 'Exited by user'
		os._exit(1)
