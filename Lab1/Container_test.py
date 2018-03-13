#!/usr/bin/python3
import lxc
import sys


def echo_string(param):
	'''
	Write a string into a specified file.
	Args:
		param: a dict that indicates both the string and the file.
				The string is indicated by its "str_to_be_echoed" 
				item, while the file by "file_path".
	'''

	with open(param["file_path"], 'w', encoding='utf-8') as fd:
		fd.write(param["str_to_be_echoed"])
	

c = lxc.Container("Hello-Container")

if c.defined:
	print("Container already exists", file=sys.stderr)
	sys.exit(1)

if not c.create("download", lxc.LXC_CREATE_QUIET, {"dist":"debian",
													"release":"wheezy",
													"arch":"i386"}):
	print("Failed to create the container rootfs", file=sys.stderr)
	sys.exit(1)

if not c.start():
	print("Failed to start the container", file=sys.stderr)
	sys.exit(1)



try:
	c.attach_wait(echo_string, {"str_to_be_echoed":u"1400012770 Li Pengcheng", "file_path":u"Hello-Container"})
	c.attach_wait(lxc.attach_run_command, ["cat", "Hello-Container"])
	#c.attach_wait(lxc.attach_run_command, ["ls"])

finally:
	pass

if not c.shutdown(30):
	print("Failed to cleanly shutdown the container, forcing.")
	if not c.stop():
		print("Failed to kill to container", file=sys.stderr)
		sys.exit(1)

if not c.destroy():
	print("Failed to destroy the container.", file=sys.stderr)
	sys.exit(1)
