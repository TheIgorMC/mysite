from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/archery')
def archery():
    return render_template('archery.html')

@app.route('/3dprinting')
def printing():
    return render_template('3dprinting.html')

@app.route('/electronics')
def electronics():
    return render_template('electronics.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
