from flask import Flask, request, render_template, flash, redirect, send_file
import requests
import json
import math
from flask_wtf import Form
from wtforms import validators,StringField, IntegerField,SubmitField, BooleanField, SelectField
from flask_cors import CORS
from blockdevice import PilihCapsMon, PilihCapsOsd, PilihCapsMds
from blockdevice import newImage, newPool, list_image, image_info, editImage, deleteImage


app = Flask(__name__)
cors = CORS(app, resources={r"10.10.6.251:5000/api/v0.1/*": {"Access-Control-Allow-Origin": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'
app.secret_key = 'development key'
headers = {'Access-Control-Max-Age' : '3600',
           'Content-Type' : 'text/plain',
           'Content-Length' : '0',
           'Access-Control-Allow-Origin': '*',
           "Access-Control-Allow-Credentials": "True",
           'Access-Control-Allow-Methods': 'GET, POST, OPTIONS,PUT',
           'Access-Control-Allow-Headers': 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range',
           'Access-Control-Expose-Headers': 'Content-Length'}

class BuatUser(Form):
    userID = StringField('userID')
    OSDr   = BooleanField('read')
    OSDw   = BooleanField('write')
    OSDx   = BooleanField('execute')
    MONr   = BooleanField('read')
    MONw   = BooleanField('write')
    MONx   = BooleanField('execute')
    MDSr   = BooleanField('read')
    MDSw   = BooleanField('write')
    MDSx   = BooleanField('execute')
    pool   = SelectField('Pool')
    submit = SubmitField()

class BuatPool(Form):
    namaPool = StringField('Nama Pool')
    PGnum = IntegerField('PG Number')
    PGPnum = IntegerField('PGP Number')
    submit = SubmitField()

class BuatImage(Form):
    namaPool = SelectField('Nama Pool')
    namaImage = StringField('Nama Image')
    kapasitas = IntegerField('Kapasitas dalam GB')
    submit = SubmitField()

@app.route('/')
def index():
    r = requests.get('http://10.10.6.251:5000/api/v0.1/health.json')
    r1 = requests.get('http://10.10.6.251:5000/api/v0.1/fsid.json')
    r2 = requests.get('http://10.10.6.251:5000/api/v0.1/pg/stat.json')
    pgstat = json.loads(r2.text)
    datapersen =math.ceil((pgstat['output']['raw_bytes_used'])/(pgstat['output']['raw_bytes_avail'])*100)
    return render_template('home.html',datum=datapersen,data =json.loads(r.text),data1=json.loads(r1.text),headers=headers)

@app.route('/AddUser')
def adduser():
    r = requests.get('http://10.10.6.251:5000/api/v0.1/auth/list.json')
    return render_template('adduser.html', data =json.loads(r.text),headers=headers)

@app.route('/AddUser/DelUser/<string:entity>', methods = ['GET','PUT'])
def deluser(entity):
    requests.put('http://10.10.6.251:5000/api/v0.1/auth/del', params={"entity":entity},headers=headers)
    return redirect('/AddUser')

@app.route('/AddUser/form', methods = ['GET','POST','PUT'])
def adduserform():
    form = BuatUser(request.form)
    r = requests.get('http://10.10.6.251:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    form.pool.choices = [(pool,pool) for pool in pools]   
    if request.method == 'POST':
        if form.validate() == False:
            flash('Isi seluruhnya')
            return render_template('form.html', form=form)
        else:
            requests.put('http://10.10.6.251:5000/api/v0.1/auth/get-or-create',
                params={"entity":"client."+form.userID.data, "caps":[ 
                PilihCapsMon(form.MONr.data,form.MONw.data,form.MONx.data),
                PilihCapsOsd(form.OSDr.data,form.OSDw.data,form.OSDx.data, form.pool.data),
                PilihCapsMds(form.MDSr.data,form.MDSw.data,form.MDSx.data)]},headers=headers)
            return redirect('/AddUser')
    elif request.method == 'GET':
        return render_template('form.html', form=form)

@app.route('/AddUser/EditUser/<string:entity>', methods = ['GET','POST','PUT'])
def edituser(entity):
    form = BuatUser(request.form)
    form.userID.data = entity
    r = requests.get('http://10.10.6.251:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    form.pool.choices = [(pool,pool) for pool in pools]

    if request.method == 'POST':
        if form.validate() == False:
            flash('Isi seluruhnya')
            return render_template('formedit.html', form=form, entity=entity)
        else:
            requests.put('http://10.10.6.251:5000/api/v0.1/auth/caps',
                params={"entity":form.userID.data, "caps":[
                PilihCapsMon(form.MONr.data,form.MONw.data,form.MONx.data),
                PilihCapsOsd(form.OSDr.data,form.OSDw.data,form.OSDx.data,form.pool.data),
                PilihCapsMds(form.MDSr.data,form.MDSw.data,form.MDSx.data)]},headers=headers)
            return redirect('/AddUser')
    elif request.method == 'GET':
        return render_template('formedit.html', form=form, entity=entity)

@app.route('/VolumeList',methods = ['GET','POST'])
def volumelist():
    r = requests.get('http://10.10.6.251:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    images = []
    list_dict = []
    dict = {}
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    for pool in pools:
        poolimages = (list_image(pool))
        if poolimages != []:
            dict['namapool'] = pool
        for i in poolimages:
	    dict['namaimage'] = i
	    haha  = image_info(pool,i)
	    dict['size'] = haha['size']/1024**3
            images.append(i)
	    list_dict.append(dict.copy())
    return render_template('addvolume.html', data=json.loads(r.text), dict=list_dict)

@app.route('/VolumeList/formpool',methods=['GET','POST','PUT'])
def formpool():
    form = BuatPool(request.form)
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('formpool.html', form=form)

        else:
            requests.put('http://10.10.6.251:5000/api/v0.1/osd/pool/create',headers=headers, params = {'pool':form.namaPool.data, 'pg_num':form.PGnum.data, 'pgp_num':form.PGPnum.data})
	    return redirect('/VolumeList')
    elif request.method == 'GET':
   	 return render_template('formpool.html', form=form)	

@app.route('/VolumeList/formimage',methods=['GET','POST','PUT'])
def formimage():
    form = BuatImage(request.form)
    r = requests.get('http://10.10.6.251:5000/api/v0.1/osd/pool/stats.json',headers=headers)
    poolimages = []
    pools = []
    for lists in json.loads(r.text)["output"]:
        pools.append(lists['pool_name'])
    form.namaPool.choices = [(pool,pool) for pool in pools]
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('formimage.html', form=form)
        else:
            newImage(form.namaPool.data, form.namaImage.data, form.kapasitas.data)
            return redirect('/VolumeList')
    if request.method == 'GET' :
        return render_template('formimage.html', form=form)

@app.route('/VolumeList/EditPool/<string:poolname>', methods = ['GET','PUT','POST'])
def editpool(poolname):
    form = BuatPool(request.form)
    form.namaPool.data = poolname
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('editpool.html',form=form, poolname=poolname)
        else:
            requests.put('http://10.10.6.251:5000/api/v0.1/osd/pool/set',params={"pool":form.namaPool.data, "var":"pg_num", "val":form.PGnum.data}, headers=headers)
            requests.put('http://10.10.6.251:5000/api/v0.1/osd/pool/set',params={"pool":form.namaPool.data, "var":"pgp_num", "val":form.PGPnum.data}, headers=headers)
            return redirect('/VolumeList')
    elif request.method == 'GET':
        return render_template('editpool.html', form=form, poolname=poolname)

@app.route('/VolumeList/DelPool/<string:poolname>', methods = ['GET','PUT'])
def delpool(poolname):
    requests.put('http://10.10.6.251:5000/api/v0.1/osd/pool/delete', params={"pool":poolname,"pool2":poolname, "sure":"--yes-i-really-really-mean-it"},headers=headers)
    return redirect('/VolumeList')

@app.route('/VolumeList/EditVolume/<string:namaimage>/<string:namapool>', methods=['GET','POST'])
def editblock(namaimage,namapool):
    form = BuatImage(request.form)
    form.namaImage.data = namaimage
    if request.method == 'POST':
        editImage(namapool, namaimage, form.kapasitas.data)
        return redirect('/VolumeList')
    elif request.method == 'GET':
        return render_template('formeditimage.html', form=form,namaimage=namaimage,namapool=namapool)

@app.route('/VolumeList/DelVolume/<string:namaimage>/<string:namapool>', methods=['GET'])
def delblock(namapool,namaimage):
    deleteImage(namapool,namaimage)
    return redirect('/VolumeList')

@app.route('/Konfigurasi', methods = ['GET','POST','PUT'])
def konfig():
    r1=requests.get('http://10.10.6.251:5000/api/v0.1/mon_status.json',headers=headers)
    r2=requests.get('http://10.10.6.251:5000/api/v0.1/mds/stat.json',headers=headers)
    r3=requests.get('http://10.10.6.251:5000/api/v0.1/osd/crush/dump.json', headers=headers)
    return render_template('konfig.html',data =json.loads(r1.text),datamds=json.loads(r2.text), dataosd=json.loads(r3.text))

@app.route('/Kirim', methods = ['GET','POST'])
def cephconf():
    return send_file('/etc/ceph/ceph.conf',attachment_filename='ceph.conf')

@app.route('/KirimContohKeyring/<string:client>/<string:keyring>', methods = ['GET', 'POST'])
def clientkeyring(client,keyring):
    file = open('/home/tasds/{}.keyring'.format(client),'w+')
    file.write('[{}.keyring]]\n'.format(client))
    file.write('        key = {}'.format(keyring))
    file.close()
    return send_file('/home/tasds/{}.keyring'.format(client))

if __name__=='__main__':
    app.run(host='0.0.0.0',port=8000,debug=True)
