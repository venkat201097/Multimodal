from flask import Flask, render_template, request, redirect, url_for
import os
import sys
import pickle
import pandas as pd
import random

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static'

# app.config['UPLOAD_FOLDER'] = 'static'
 
def traingenerator():
	for sample in train_data[bucket]:
		yield sample

def testgenerator():
	global retrieve
	i = 0
	retrieve = 'i'
	for sample in random.sample(testaud[bucket],len(testaud[bucket])):
		i+=1
		yield sample,i
	i = 0
	retrieve = 'a'
	for sample in random.sample(testimg[bucket],len(testimg[bucket])):
		i+=1
		yield sample,i

def storetest(form_dict):
	global testsample
	global retrieve
	if retrieve=='i':
		response = list(form_dict)[0][:4]
		sample = testsample[0].split('_')[1].split('/')[-1]
	else:
		# response = form_dict['label']
		response = list(form_dict)[0]
		# print(response,file=sys.stderr)
		sample = testsample[0].split('_')[0].split('/')[-1]
	sampleid = testsample[0]
	if retrieve=='i':
		label = lab2img[sample]
	else:
		label = img2lab[sample]
	for i in testsample[1:]:
		if retrieve=='i':
			if i.split('_')[0].split('/')[-1]==lab2img[sample]:
				labelid = i
			if i.split('_')[0].split('/')[-1]==response:
				responseid = i
		else:
			if i.split('_')[1].split('/')[-1]==img2lab[sample]:
				labelid = i
			if i.split('_')[1].split('/')[-1]==response:
				responseid = i
	global sub_id
	with open('static/Data/S{}/test.csv'.format(sub_id),'a+') as fp:
		fp.write('{},{},{},{},{},{},{},{}\n'.format(bucket,retrieve,sample,sampleid,label,labelid,response,responseid))

@app.route('/')
def home():
	global bucket,retrieve
	bucket = 0
	retrieve = 'i'
	return render_template("index.html")

@app.route('/info',methods=['GET','POST'])
def info():
	with open('static/Data/subjects.csv','a+') as fp:
		fp.write('{},{},{},{}\n'.format(request.form['id'],request.form['name'],request.form['gender'],request.form['email']))
	global sub_id
	sub_id = request.form['id']

	if not os.path.isdir('static/Data/S'+request.form['id']):
		os.system('mkdir '+'static/Data/S'+request.form['id'])

	with open('static/Data/S{}/test.csv'.format(sub_id),'w+') as fp:
		fp.write('Session,Test_Phase,Sample,Sample_Id,Label,Label_Id,Response,Response_Id\n')

	with open('static/Data/S{}/train.csv'.format(sub_id),'w+') as fp:
		fp.write('Session,Sample,Sample_Id,Label,Label_Id,PlayCount,Time\n')

	global train_bucket
	train_bucket = traingenerator()
	return render_template('safety.html', session=bucket,sess_type="train")

@app.route('/traininfo',methods=['GET','POST'])
def traininfo():
	global sub_id
	playcount = request.form['playcount']
	timespent = request.form['timespent']

	with open('static/Data/S{}/train.csv'.format(sub_id),'a+') as fp:
		fp.write('{},{}\n'.format(playcount,timespent))

	return redirect(url_for("train"))



@app.route('/train',methods=['GET','POST'])
def train():
	global sub_id
	global bucket
	global train_bucket
	try:
		trainsample = train_bucket.__next__()
		with open('static/Data/S{}/train.csv'.format(sub_id),'a+') as fp:
			sampleid = trainsample[0]
			sample = trainsample[0].split('_')[0].split('/')[-1]
			labelid = trainsample[1]
			label = trainsample[1].split('_')[1].split('/')[-1]
			fp.write('{},{},{},{},{},'.format(bucket,sample,sampleid,label,labelid))
	except:
		global test_bucket
		test_bucket = testgenerator()
		return render_template("safety.html", session=bucket,sess_type="test")
	return render_template("train.html", image = trainsample[0],label=trainsample[1])

@app.route('/score',methods=['GET','POST'])
def score():
	if bucket==NUM_BUCKETS:
		return render_template('end.html')
	return render_template('safety.html', session=bucket,sess_type="train")

@app.route('/test',methods=['GET','POST'])
def test():
	global retrieve
	global test_bucket
	if "test" not in request.form:
		storetest(request.form)
	global testsample
	try:
		testsample,curr_index = test_bucket.__next__()
	except:
		global bucket
		bucket+=1
		if bucket<NUM_BUCKETS:
			global train_bucket
			train_bucket = traingenerator()
		global sub_id
		responses = pd.read_csv('static/Data/S{}/test.csv'.format(sub_id))
		curr_resp = responses[responses['Session']==(bucket-1)]
		# print(bucket-1)
		# print(curr_resp)
		scores = {'i':0,'a':0}
		for i,x in curr_resp.iterrows():
			if x['Label']==x['Response']:
				# print('yes')
				scores[x['Test_Phase']]+=1
		return render_template('score.html',session=bucket,sess_type="train",score_i=scores['i'],score_a=scores['a'])
			# return render_template('safety.html', session=bucket,sess_type="train")

	return render_template("test.html", samples= testsample[1:],label=testsample[0],retrieve=retrieve,index=curr_index)

if __name__ == "__main__":
	CLASSES_PER_BUCKET = 10
	NUM_BUCKETS = 6
	bucket = 0
	retrieve = 'i'

	testsample=None
	test_bucket = None
	train_bucket = None

	img2lab = pickle.load(open('static/pickles/img2lab.pkl','rb'))
	lab2img = {j:i for i,j in img2lab.items()}

	train_data = pickle.load(open('static/pickles/train.pkl','rb'))
	testimg = pickle.load(open('static/pickles/imgtest.pkl','rb'))
	testaud = pickle.load(open('static/pickles/audtest.pkl','rb'))

	app.run(debug=True)