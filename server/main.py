from bottle import route, run


@route('/hello')
def hello():
    return "Hello World!"

@route('/q')
def query():
    return "!"

run(host='localhost', port=8080, debug=True)
