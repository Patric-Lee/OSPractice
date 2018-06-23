from flask import Flask
from flask import request
from flask import render_template
import lxc




app = Flask(__name__)
container_map = {}
#@app.route('/')
@app.route('/job/create', methods=['POST', 'GET'])
def create_task():
	error =  None
	
	if request.method == 'POST':
		task = request.form
		image = preprocessing(task)
		create_result = lxc_create_task(task, image)
		if create_result.get('code') == 0:
			return create_result.get("message")
		else:
			return create_result.get("message") 



	return render_template('create.html')

@app.route('/job/check'), methods=['POST','GET'])
def check_task():
	error = None
	if request.method == 'POST':
		task = request.form
		check_result = lxc_check_task(task)
	return check_result["message"]	
	#return render_template('check.html', check_result=check_result)

@app.route('/job/kill', methods=['POST','GET'])
def kill_task():
	error = None
	if request.method == 'POST':
		task = request.form
		kill_result = lxc_kill_task(task)
	#return render_template('kill.html', kill_result=kill_result)
	return check_result["message"]


def preprocessing(task):
	image = {}
	image["dist"] = task["dist"]
	image["release"] = task["release"]
	image["arch"] = task["arch"]
	print(image)
	return image

def lxc_create_task(task, image):
	result = {"code":-1, "message":""}
	result["name"] = task['name']
	result["id"] = -1	
	container = lxc.Container(task['name'])
	if container.defined:
		result["message"] = 'Task ' + task['name'] + ' exists!'
		return result

	if not container.create("download", 0, image): 
		result["message"] = 'Failed to create the container rootfs'
		return result
	
	if not container.start():
		result["message"] = 'Failed to start the container'
		return result

	result["code"] = 0
	result["id"] = container.init_pid
	result["message"] = "Task created!"
	container_dict["name"] = container
	print(result["id"])
	return result

def 

def lxc_kill_task(task):
	result = {"code":-1, "message":"Kill failed."}
	if task["name"] in container_dict:
		container = container_dict.get(task["name"])
		if not container.shutdown(30):
			if not container.stop():
				result["message"] = "Task cannot be killed."
			
		else:
			result["code"] = 0
			result["message"] = "Task killed."
			container.destroy()
			result[task["name"]] = None
	else:
		result["message"] = "No such task."
	return result 

def lxc_check_task(task):
	result = {"code":-1, "message":"Check failed."}
        if task["name"] in container_dict:
                container = container_dict.get(task["name"])
                result["state"] = container.state
		
        else:
                result["message"] = "No such task."
        return result



















