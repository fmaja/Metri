from flask import Flask, render_template, redirect, url_for

# Minimal runnable Flask app that serves the UI prototype added under web/
app = Flask(__name__, template_folder='web/templates', static_folder='web/static')

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/run_tio')
def run_tio():
    # kept for backwards compatibility with earlier instructions
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard_ui.html')

@app.route('/exercises')
def exercises():
    return render_template('exercises_ui.html')

@app.route('/metronome')
def metronome():
    return render_template('metronome_ui.html')

@app.route('/detector')
def detector():
    return render_template('detector_ui.html')

if __name__ == '__main__':
    # Run in debug for local review. In production switch debug off.
    app.run(debug=True, host='0.0.0.0', port=5000)