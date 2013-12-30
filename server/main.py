from bottle import route, run, abort, view, post, request, response, static_file
import readsubhalo
from gaepsi.compiledbase.geometry import Cubenoid
import numpy

boxsize = 100000.0
M = numpy.matrix("2,1,1  ;1,4,-2 ; 1,0,1").T 
cub = Cubenoid(M, [0, 0, 0], [boxsize, boxsize, boxsize],
        center=0, neworigin=0)

def getsnap(snapid):
    return readsubhalo.SnapDir(snapid, '/mnt/raid0/www/MB-IIa/')

@route('/hello')
def hello():
    return "Hello World!"

@route('/snap/<snapid:int>')
def snap(snapid):
    snap = getsnap(snapid)
    return dict(redshift=snap.redshift)

@route('/snap/<snapid:int>/group/<gid:int>')
@view('group.html')
def group(snapid, gid):
    snap = getsnap(snapid)
    tab = snap.readgroup()
    fields = tab.dtype.fields 
    if gid >= len(tab) or gid < 0:
        return abort(404, "Group %d not found in snapid %d" % (gid,
snapid))
    return dict(groups=[(gid, tab[gid])])

@route('/snap/<snapid:int>/galaxy')
def galaxy(snapid):
    snap = readsubhalo.SnapDir(snapid, '/mnt/raid0/www/MB-IIa/')
    
@route('/search/<snapid:int>')
@view('search.html')
def search(snapid):
    return dict(snapid=snapid)

def makeselection(snap, f):
    gtab = None
    tab = snap.load('subhalo', 'tab', g=gtab)
    type = snap.load('subhalo', 'type', g=gtab)
    xmin = numpy.float64(f.get('xmin'))
    ymin = numpy.float64(f.get('ymin'))
    xmax = numpy.float64(f.get('xmax'))
    ymax = numpy.float64(f.get('ymax'))
    MassMin = numpy.float64(f.get('MassMin'))

    mask0 = tab['mass'] > MassMin/1e10

    type = type[mask0]
    x, y, z = tab['pos'][mask0].T.copy()
    cub.apply(x, y, z)
  
    mask = numpy.ones_like(x, dtype='?')
    print xmax, ymax, xmin, ymin
#    mask &= type == 1
    mask &= x >= xmin
    mask &= x <= xmax
    mask &= y >= ymin
    mask &= y <= ymax
    id = mask0.nonzero()[0][mask]
    return id

@post('/search/<snapid:int>')
@route('/dosearch/<snapid:int>')
@view('galaxy.json')
def do_search(snapid):
    response.content_type = 'application/json'
    f = request.params
    Nmax = numpy.int(f.get('Nmax'))
    Nmax = 10
    snap = getsnap(snapid)
    gtab = snap.readgroup()
    edge = cub.newboxsize.max()
    gtab = None
    type = snap.load('subhalo', 'type', g=gtab)
    tab = snap.load('subhalo', 'tab', g=gtab)
    SDSSi = snap.load('subhalo', 'RfFilter/SDSS.SDSS/i', g=gtab)
    SDSSr = snap.load('subhalo', 'RfFilter/SDSS.SDSS/r', g=gtab)
    SDSSg = snap.load('subhalo', 'RfFilter/SDSS.SDSS/g', g=gtab)
    SDSSu = snap.load('subhalo', 'RfFilter/SDSS.SDSS/u', g=gtab)
    SDSSz = snap.load('subhalo', 'RfFilter/SDSS.SDSS/z', g=gtab)
    
    id = makeselection(snap, f)
    mass = tab['mass'][id]
    arg = mass.argsort()[::-1]
    id = id[arg][:Nmax]

    x, y, z = tab['pos'][id].T
    print x.min(), x.max(), y.min(), y.max()
    cub.apply(x, y, z)
    mass = tab['mass'][id]
    vel = tab['vel'][id]
    pos = tab['pos'][id]
    rcirc = tab['rcirc'][id]

    x /= edge
    y /= edge
    w = rcirc / edge * 4
    h = rcirc / edge * 4

    print mass
    print vel
    print pos 
    print id

    rt = dict(
        x=y, y=x, w=w, h=h, 
        mass=mass,
        SDSS=[
            snap.load('subhalo', 'RfFilter/SDSS.SDSS/%s' % band)[id]
            for band in "irguz"])
    return rt
@route('/<filename:path>')
def server_static(filename):
    return static_file(filename, root='/mnt/raid0/www/mbiibrowser/')

run(host='0.0.0.0', port=8080, debug=True)
